"""TCMB günlük döviz kuru çekicisi (spec §9, Adım 5).

Spec §8'in kuralı: TL çevrimi **bildirim tarihli** resmî kurla yapılır,
bugünkü kurla değil. 2025'te imzalanmış bir sözleşmeyi 2026 kuruyla
çevirmek rakamı şişirir. TCMB arşivi ücretsiz, resmî ve geriye dönük.

Alış mı satış mı: **döviz alış** (`ForexBuying`) seçildi. Şirketler
hasılatlarını TL'ye çevirirken bu kuru kullanıyor; ciro oranının payı ile
paydası aynı mantıkla hesaplanmış oluyor. Aradaki fark ~%0.2, ama hangisi
olduğunun sabit ve yazılı olması önemli.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import ClassVar

import httpx

from kap_radar.http_temel import ErisimHatasi, HizSinirliIstemci

KOK = "https://www.tcmb.gov.tr"

# Arşiv yolu tek URL'de iki ayrı tarih biçimi taşıyor: klasör YYYYMM,
# dosya DDMMYYYY.
ARSIV_YOLU = "/kurlar/{yil}{ay:02d}/{gun:02d}{ay:02d}{yil}.xml"


class KurErisimHatasi(ErisimHatasi):
    """TCMB'ye tüm denemelere rağmen ulaşılamadı."""


@dataclass(frozen=True)
class GunlukKur:
    """Bir bültenin kurları.

    `tarih` yanıttan okunur, istenen günden değil: hafta sonu istendiğinde
    hangi günün bülteni geldiği kaybolmamalı.
    """

    tarih: date
    kurlar: dict[str, Decimal]


def kur_ayristir(xml: str) -> GunlukKur:
    """TCMB bülteninden para birimi → TL karşılığı eşlemesi üretir.

    Kurlar `Unit` başına yayınlanıyor (JPY 100 birim üzerinden); tek
    birime indirgenmezse yen cinsli bir sözleşme 100 kat büyük görünür.
    Alış kuru boş olan para birimi atlanır — boşu sıfıra çevirmek çarpımı
    sessizce sıfırlar.
    """
    kok = ET.fromstring(xml)
    gun, ay, yil = (int(p) for p in kok.get("Tarih", "").split("."))

    kurlar: dict[str, Decimal] = {}
    for dugum in kok.findall("Currency"):
        kod = dugum.get("Kod")
        ham = (dugum.findtext("ForexBuying") or "").strip()
        if not kod or not ham:
            continue
        birim = int((dugum.findtext("Unit") or "1").strip() or 1)
        kurlar[kod] = Decimal(ham) / birim

    return GunlukKur(tarih=date(yil, ay, gun), kurlar=kurlar)


class KurIstemcisi(HizSinirliIstemci):
    """TCMB kur arşivinden gün gün okur."""

    HATA_SINIFI: ClassVar[type[ErisimHatasi]] = KurErisimHatasi

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("kok", KOK)
        super().__init__(**kwargs)

    def ham(self, tarih: date) -> str | None:
        """O günün bülten XML'ini olduğu gibi döndürür; yayın yoksa None.

        Hafta sonu ve resmî tatilde TCMB dosya yayınlamıyor ve 404
        veriyor. Bu bir hata değil, veri yokluğu: yeniden denemek
        anlamsız. Sunucu hataları (5xx) ise geçici sayılıp yeniden
        denenir — ikisi karıştırılmamalı.
        """
        yol = ARSIV_YOLU.format(yil=tarih.year, ay=tarih.month, gun=tarih.day)

        def cagri() -> httpx.Response:
            yanit = self._oturum.get(yol)
            if yanit.status_code != httpx.codes.NOT_FOUND:
                yanit.raise_for_status()
            return yanit

        yanit = self._dene(cagri)
        if yanit.status_code == httpx.codes.NOT_FOUND:
            return None
        return yanit.text

    def gun(self, tarih: date) -> GunlukKur | None:
        """O günün kurlarını döndürür; yayın yoksa None."""
        xml = self.ham(tarih)
        return kur_ayristir(xml) if xml is not None else None
