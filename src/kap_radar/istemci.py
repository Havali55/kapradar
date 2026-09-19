"""KAP HTTP istemcisi.

Adım 0'da ampirik olarak öğrenilen kurallar (spec §9) burada uygulanır:
oturum ısıtması, Referer başlığı ve dürüst User-Agent olmadan KAP'ın
WAF'ı bağlantıyı düşürüyor.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import date
from typing import TypeVar

import httpx

T = TypeVar("T")

KOK = "https://www.kap.org.tr"
ISITMA_YOLU = "/tr/bildirim-sorgu"
LISTE_YOLU = "/tr/api/disclosure/members/byCriteria"
DETAY_YOLU = "/tr/api/notification/attachment-detail"

VARSAYILAN_USER_AGENT = "kap-radar/0.1 (+iletisim: ornek@ornek.com)"


class KapErisimHatasi(RuntimeError):
    """KAP'a tüm denemelere rağmen ulaşılamadı."""


class KapIstemcisi:
    """KAP'ın kimliksiz JSON API'sine erişen istemci."""

    def __init__(
        self,
        *,
        transport: httpx.BaseTransport | None = None,
        uyku: Callable[[float], None] = time.sleep,
        saat: Callable[[], float] = time.monotonic,
        user_agent: str = VARSAYILAN_USER_AGENT,
        istek_araligi_sn: float = 0.5,
        maks_deneme: int = 5,
        geri_cekilme_tabani_sn: float = 2.0,
    ) -> None:
        self._uyku = uyku
        self._saat = saat
        self._istek_araligi_sn = istek_araligi_sn
        self._maks_deneme = maks_deneme
        self._geri_cekilme_tabani_sn = geri_cekilme_tabani_sn
        self._son_istek_zamani: float | None = None
        self._user_agent = user_agent
        self._isitildi = False
        self._oturum = httpx.Client(
            base_url=KOK,
            transport=transport,
            headers={"User-Agent": user_agent},
            timeout=30.0,
        )

    def _hiz_sinirla(self) -> None:
        """Ardışık istekler arasında sabit bir asgari boşluk bırakır.

        Adım 0'da ardışık tarama WAF'a takıldığı için bu koda gömülü:
        çağıran tarafın beklemeyi hatırlamasına bırakılmaz.
        """
        if self._son_istek_zamani is not None:
            gecen = self._saat() - self._son_istek_zamani
            kalan = self._istek_araligi_sn - gecen
            if kalan > 0:
                self._uyku(kalan)
        self._son_istek_zamani = self._saat()

    def _dene(self, cagri: Callable[[], T]) -> T:
        """Bir isteği üstel geri çekilmeyle yeniden dener.

        WAF bağlantıyı düşürdüğünde iş kaybolmamalı, sadece gecikmeli.
        Sabit aralıkla yeniden denemek bloklanmış bir WAF'ı açmaz; bekleme
        her denemede ikiye katlanır.

        JSON çözümü de bu ağın içinde: WAF araya girdiğinde 200 ile HTML
        sayfası dönüyor, yani hata HTTP katmanında değil gövdede görünüyor.
        """
        son_hata: Exception | None = None

        for deneme in range(self._maks_deneme):
            if deneme:
                self._uyku(self._geri_cekilme_tabani_sn * 2 ** (deneme - 1))
            self._hiz_sinirla()
            try:
                return cagri()
            except (
                httpx.TransportError,
                httpx.HTTPStatusError,
                json.JSONDecodeError,
            ) as hata:
                son_hata = hata

        raise KapErisimHatasi(
            f"KAP'a {self._maks_deneme} denemede ulaşılamadı"
        ) from son_hata

    def _isit(self) -> None:
        """API'den önce bir kez normal sayfa çekip çerez alır."""
        if self._isitildi:
            return
        self._dene(lambda: self._oturum.get(ISITMA_YOLU))
        self._isitildi = True

    def liste(self, baslangic: date, bitis: date) -> list[dict]:
        """Tarih aralığındaki bildirimleri döndürür.

        KAP 2.000 elemanda kesiyor; çağıran pencereyi yeterince dar tutmalı.
        """
        self._isit()
        return self._dene(
            lambda: self._oturum.post(
                LISTE_YOLU,
                json={
                    "fromDate": baslangic.isoformat(),
                    "toDate": bitis.isoformat(),
                    "mkkMemberOidList": [],
                    "subjectList": [],
                },
                headers={
                    "Referer": f"{KOK}{ISITMA_YOLU}",
                    "Accept": "application/json",
                },
            ).json()
        )

    def detay(self, kap_index: int) -> dict:
        """Tek bir bildirimin künyesini, gövdesini ve eklerini döndürür.

        Yanıt tek elemanlı bir dizi; boş dönerse bu sessizce yutulmaz,
        çünkü ayrıştırıcıya boş sözlük vermek yanlış kayıt üretir.
        """
        self._isit()
        govde = self._dene(
            lambda: self._oturum.get(
                f"{DETAY_YOLU}/{kap_index}",
                headers={
                    "Referer": f"{KOK}/tr/Bildirim/{kap_index}",
                    "Accept": "application/json",
                },
            ).json()
        )
        if not govde:
            raise KapErisimHatasi(f"{kap_index} için detay yanıtı boş döndü")
        return govde[0]

    def kapat(self) -> None:
        self._oturum.close()
