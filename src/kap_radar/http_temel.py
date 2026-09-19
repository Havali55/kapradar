"""Hız sınırlı, üstel geri çekilmeyle yeniden deneyen HTTP istemci tabanı.

KAP ve TCMB çekicileri aynı disiplini paylaşıyor: sabit asgari boşluk,
sınırlı sayıda deneme, her denemede ikiye katlanan bekleme, JSON/XML
çözümünün de bu ağın içinde olması. Mantık iki yerde yaşarsa biri
düzeltilip diğeri unutulur.

Kaynağa özgü davranış iki kancayla veriliyor: `_istek_oncesi` (KAP'ın
oturum ısıtması) ve `_hata_sonrasi` (bloğun ardından oturumu soğutma).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import ClassVar, TypeVar

import httpx

T = TypeVar("T")

VARSAYILAN_USER_AGENT = "kap-radar/0.1 (+iletisim: ornek@ornek.com)"


class ErisimHatasi(RuntimeError):
    """Kaynağa tüm denemelere rağmen ulaşılamadı."""


class HizSinirliIstemci:
    """Tek bir kaynağa nazikçe erişen istemci."""

    HATA_SINIFI: ClassVar[type[ErisimHatasi]] = ErisimHatasi

    def __init__(
        self,
        *,
        kok: str,
        transport: httpx.BaseTransport | None = None,
        uyku: Callable[[float], None] = time.sleep,
        saat: Callable[[], float] = time.monotonic,
        user_agent: str = VARSAYILAN_USER_AGENT,
        istek_araligi_sn: float = 0.5,
        maks_deneme: int = 5,
        geri_cekilme_tabani_sn: float = 2.0,
        zaman_asimi: float = 30.0,
    ) -> None:
        self._uyku = uyku
        self._saat = saat
        self._istek_araligi_sn = istek_araligi_sn
        self._maks_deneme = maks_deneme
        self._geri_cekilme_tabani_sn = geri_cekilme_tabani_sn
        self._son_istek_zamani: float | None = None
        self._user_agent = user_agent
        self._oturum = httpx.Client(
            base_url=kok,
            transport=transport,
            headers={"User-Agent": user_agent},
            timeout=zaman_asimi,
        )

    def _hiz_sinirla(self) -> None:
        """Ardışık istekler arasında sabit bir asgari boşluk bırakır.

        Çağıran tarafın beklemeyi hatırlamasına bırakılmaz: KAP'ta ardışık
        tarama tam da bu yüzden WAF'a takılmıştı.
        """
        if self._son_istek_zamani is not None:
            gecen = self._saat() - self._son_istek_zamani
            kalan = self._istek_araligi_sn - gecen
            if kalan > 0:
                self._uyku(kalan)
        self._son_istek_zamani = self._saat()

    def _istek_oncesi(self) -> None:
        """Her denemede, istekten önce koşar. Varsayılanı boş."""

    def _hata_sonrasi(self) -> None:
        """Başarısız denemeden sonra koşar. Varsayılanı boş."""

    def _dene(self, cagri: Callable[[], T]) -> T:
        """Bir isteği üstel geri çekilmeyle yeniden dener.

        Gövde çözümü de (JSON/XML) bu ağın içinde olmalı: kaynak araya
        giren bir sayfayı 200 ile döndürdüğünde hata HTTP katmanında
        değil gövdede görünür.
        """
        son_hata: Exception | None = None

        for deneme in range(self._maks_deneme):
            if deneme:
                self._uyku(self._geri_cekilme_tabani_sn * 2 ** (deneme - 1))
            try:
                self._istek_oncesi()
                self._hiz_sinirla()
                return cagri()
            except (
                httpx.TransportError,
                httpx.HTTPStatusError,
                json.JSONDecodeError,
            ) as hata:
                son_hata = hata
                self._hata_sonrasi()

        raise self.HATA_SINIFI(
            f"{self._oturum.base_url} adresine {self._maks_deneme} "
            "denemede ulaşılamadı"
        ) from son_hata

    def kapat(self) -> None:
        self._oturum.close()
