"""Çıkarımdan yayın kararına giden tam zincir (spec §6 + §8).

Kapı iki aşamalı ve ikinci aşama §8 hesaplarına ihtiyaç duyuyor. Bu
dosya o sırayı tek yerde kuruyor:

    Aşama A (metin)  →  §8 hesapları  →  Aşama B (tutarlılık)  →  skor

Ayrı durmasının sebebi 2026-09-20'de görüldü: koşucu yalnız Aşama A'yı
çalıştırıyordu ve B hiç devreye girmiyordu. CWENE 1502725'te model
şirketin kendi TL çevrimini ikinci kalem sayınca skor 0,08 yerine 0,61
çıktı — yakalayacak olan kontrol (B3) koşmuyordu.

Saf fonksiyon: ağ yok, veritabanı yok. Kur çözümü çağırandan bir
kapanış olarak geliyor, böylece hem canlı koşu hem geriye dönük
yeniden değerlendirme aynı kodu kullanıyor.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from kap_radar.cikarim import (
    Karar,
    KapiSonucu,
    TutarCikarimi,
    anlam_kapisi,
    metin_kapisi,
    tutarlilik_kapisi,
)
from kap_radar.skor import (
    SKORA_GIREN_TIPLER,
    Agirliklar,
    VARSAYILAN_AGIRLIKLAR,
    buyukluk_skoru,
    net_tutar_tl,
)

__all__ = ["Degerlendirme", "degerlendir"]


@dataclass(frozen=True)
class Degerlendirme:
    """Bir bildirimin yayına hazır hâli — ya da neden hazır olmadığı."""

    karar: Karar
    red_nedeni: str | None
    net_tutar_tl: Decimal | None
    ciro_orani: Decimal | None
    etki_skoru: Decimal | None

    @property
    def yayina_hazir(self) -> bool:
        return self.karar is Karar.YAYINLA


def _bos(kapi: KapiSonucu) -> Degerlendirme:
    """Hesaba hiç girmeden dönen karar."""
    return Degerlendirme(
        karar=kapi.karar,
        red_nedeni=kapi.red_nedeni,
        net_tutar_tl=None,
        ciro_orani=None,
        etki_skoru=None,
    )


def degerlendir(
    cikarim: TutarCikarimi,
    *,
    ham_metin_tr: str,
    ttm_hasilat: Decimal | None,
    kur_coz: Callable[[str], Decimal | None],
    karsi_taraf_acik: bool,
    guncelleme_mi: bool,
    karsi_taraf_niteligi: str | None = None,
    insan_denetimli: bool = False,
    agirliklar: Agirliklar = VARSAYILAN_AGIRLIKLAR,
) -> Degerlendirme:
    """Çıkarımı iki aşamalı kapıdan geçirip skorunu hesaplar.

    `insan_denetimli`: çıkarım elle yazıldı ya da elle onaylandı
    (`data/elle_duzeltmeler.json`). Anlam kapısı (B4–B6) atlanır — o
    soruyu insan zaten cevapladı; aritmetik kapıları yine koşar.
    """
    metin = metin_kapisi(cikarim, ham_metin_tr)
    if not metin.gecti:
        # Aşama A reddi bir üst katman modele gider; hesap koşturmanın
        # anlamı yok, zaten güvenilmeyen bir çıkarım üzerinde yapılırdı.
        return _bos(metin)

    net = net_tutar_tl(cikarim.tutarlar, kur_coz)
    oran = (
        net / ttm_hasilat
        if net is not None and ttm_hasilat and ttm_hasilat > 0
        else None
    )

    skora_giren = [t for t in cikarim.tutarlar if t.tip in SKORA_GIREN_TIPLER]
    tutarlilik = tutarlilik_kapisi(
        ciro_orani=oran,
        # Çevrilecek kalem yoksa eksik kur da yok; B2 tutarsız bildirimi
        # sebepsiz elle kuyruğa atmamalı.
        kur_bulundu=net is not None or not skora_giren,
        tl_kalemler=[
            (t.tip, t.deger * kur_coz(t.para_birimi))
            for t in skora_giren
            if kur_coz(t.para_birimi) is not None
        ],
    )
    if tutarlilik.gecti and not insan_denetimli:
        tutarlilik = anlam_kapisi(
            skora_giren, ham_metin_tr, karsi_taraf_niteligi=karsi_taraf_niteligi
        )
    if not tutarlilik.gecti:
        # Hesaplar özete giriyor: elle inceleyen kişi neyin şüpheli
        # göründüğünü rakamla görmeli.
        return Degerlendirme(
            karar=tutarlilik.karar,
            red_nedeni=tutarlilik.red_nedeni,
            net_tutar_tl=net,
            ciro_orani=oran,
            etki_skoru=None,
        )

    return Degerlendirme(
        karar=Karar.YAYINLA,
        red_nedeni=None,
        net_tutar_tl=net,
        ciro_orani=oran,
        etki_skoru=buyukluk_skoru(
            net_tutar_tl=net,
            ttm_hasilat=ttm_hasilat,
            karsi_taraf_acik=karsi_taraf_acik,
            guncelleme_mi=guncelleme_mi,
            agirliklar=agirliklar,
        ),
    )
