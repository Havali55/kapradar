"""KAP HTTP istemcisi.

Adım 0'da ampirik olarak öğrenilen kurallar (spec §9) burada uygulanır:
oturum ısıtması, Referer başlığı ve dürüst User-Agent olmadan KAP'ın
WAF'ı bağlantıyı düşürüyor.

Hız sınırı ve yeniden deneme `http_temel.HizSinirliIstemci`'den geliyor;
bu dosya yalnızca KAP'a özgü olanı tutuyor.
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from kap_radar.http_temel import (
    VARSAYILAN_USER_AGENT,
    ErisimHatasi,
    HizSinirliIstemci,
)

KOK = "https://www.kap.org.tr"
ISITMA_YOLU = "/tr/bildirim-sorgu"
LISTE_YOLU = "/tr/api/disclosure/members/byCriteria"
# Fon bildirimleri (Portföy Dağılım Raporu vb.) şirket listesinde YOK;
# ayrı uç noktadan geliyor (2026-09-22 keşfi).
FON_LISTE_YOLU = "/tr/api/disclosure/funds/byCriteria"
DETAY_YOLU = "/tr/api/notification/attachment-detail"
EK_YOLU = "/tr/api/file/download"
PDF_IMZASI = b"%PDF"


def java_sarmalini_ac(govde: bytes) -> bytes:
    """Ek indirme yanıtı Java serileştirilmiş byte[] (AC ED 00 05 ...).

    `Content-Type: application/pdf` dese de ilk baytlar PDF değil; asıl
    dosya sarmalın içinde, önünde 4 baytlık uzunluk alanıyla duruyor.
    Uzunluk tutmuyorsa yarım dosya yazmaktansa hata.
    """
    if govde.startswith(PDF_IMZASI):
        return govde
    bas = govde.find(PDF_IMZASI)
    if bas < 4:
        raise KapErisimHatasi("ek yanıtında PDF bulunamadı")
    uzunluk = int.from_bytes(govde[bas - 4 : bas], "big", signed=True)
    if uzunluk != len(govde) - bas:
        raise KapErisimHatasi(
            f"ek uzunluğu tutmuyor: alan {uzunluk}, gelen {len(govde) - bas}"
        )
    return govde[bas:]

__all__ = [
    "KOK",
    "VARSAYILAN_USER_AGENT",
    "KapErisimHatasi",
    "KapIstemcisi",
]


class KapErisimHatasi(ErisimHatasi):
    """KAP'a tüm denemelere rağmen ulaşılamadı."""


class KapIstemcisi(HizSinirliIstemci):
    """KAP'ın kimliksiz JSON API'sine erişen istemci."""

    HATA_SINIFI: ClassVar[type[ErisimHatasi]] = KapErisimHatasi

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("kok", KOK)
        super().__init__(**kwargs)
        self._isitildi = False

    def _istek_oncesi(self) -> None:
        """API'den önce normal sayfa çekip taze çerez alır.

        Çerezler önce temizleniyor: WAF'a takılmış bir oturumu aynı
        çerezlerle tazelemek bloğu taşır.
        """
        if self._isitildi:
            return
        self._oturum.cookies.clear()
        self._hiz_sinirla()
        self._oturum.get(ISITMA_YOLU)
        self._isitildi = True

    def _hata_sonrasi(self) -> None:
        """Blok oturum seviyesinde: aynı çerezle beklemek açmıyor.

        Adım 0 bulgusu bu; oturum soğuk işaretleniyor ki sonraki deneme
        önce yeniden ısınsın.
        """
        self._isitildi = False

    def liste(self, baslangic: date, bitis: date) -> list[dict]:
        """Tarih aralığındaki bildirimleri döndürür.

        KAP 2.000 elemanda kesiyor; çağıran pencereyi yeterince dar tutmalı.
        """
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

    def fon_liste(self, baslangic: date, bitis: date) -> list[dict]:
        """Fon bildirimleri; `liste` ile aynı sözleşme ve aynı 2.000 sınırı."""
        return self._dene(
            lambda: self._oturum.post(
                FON_LISTE_YOLU,
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

    def ek_indir(self, obj_id: str, kap_index: int) -> bytes:
        """Bildirim ekini (PDF) indirir, Java sarmalından çıkarır."""
        govde = self._dene(
            lambda: self._oturum.get(
                f"{EK_YOLU}/{obj_id}",
                headers={"Referer": f"{KOK}/tr/Bildirim/{kap_index}"},
            ).content
        )
        return java_sarmalini_ac(govde)

    def detay(self, kap_index: int) -> dict:
        """Tek bir bildirimin künyesini, gövdesini ve eklerini döndürür.

        Yanıt tek elemanlı bir dizi; boş dönerse bu sessizce yutulmaz,
        çünkü ayrıştırıcıya boş sözlük vermek yanlış kayıt üretir.
        """
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
