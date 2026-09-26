"""Güncelleme ve düzeltme bildirimlerini önceki bildirime bağlar.

2026-09-26 veri denetimi iki çift sayım buldu:

  - Kamu ihalelerinde önce "ihale üzerimizde kaldı", sonra aynı tutarla
    "sözleşme imzalandı" bildirimi geliyor; ikisi de skorlanıyordu.
    PLTUR'un 3,4 mr TL'lik İBB işi (%54) sitede iki ayrı "mega iş"ti.
  - Düzeltme bildirimi geldiğinde asıl bildirim de yayında kalıyordu:
    aynı iş iki kart (ONCSM, VBTYZ, KAYSE %19,5, BVSAN).

`bildirim.ilgili_kap_id` (KAP'ın relatedDisclosureOid'i) hiçbir satırda
dolu değil. Ama KAP'ın yapılandırılmış "önceki açıklama tarihleri" alanı
güncellemelerin %94'ünde, düzeltmelerin 16'sının 15'inde dolu: şirketin
kendi verdiği bağ. Kural ona dayanıyor; alan boşsa ortak tutara bakılır.

Yalnız güncelleme ya da düzeltme bayrağı taşıyan bildirim bağlanır.
Bayraksız aynı tutar tesadüf olabilir: KAYSE 12 ve 13.02.2025'te iki ayrı
7,07 mr TL anlaşma duyurdu ("toplam satışlarımız 14,14 mr'a ulaştı").

Bağ türleri:
  duzeltme  : önceki bildirimin yerini alır; önceki yayından çekilir.
  ayni_is   : güncelleme, önceki bildirimin skorlu tutarını tekrarlıyor —
              iş zaten sayıldı; bu bildirim "önceden duyurulan iş".
  guncelleme: bağlı ama tutar yeni (ilave sipariş, fiyat farkı) ya da
              önceki bildirim skorsuz; sayılmaya devam eder.

Saf modül; veritabanına `scripts/bag_kur.py` yazar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Sequence

__all__ = ["Bag", "BagGirdisi", "baglari_kur"]

# Tarih alanı boşsa ortak tutar bu pencerede aranır.
DUZELTME_PENCERESI = timedelta(days=30)
GUNCELLEME_PENCERESI = timedelta(days=365)


@dataclass(frozen=True)
class BagGirdisi:
    kap_id: str
    ticker: str
    an: datetime  # İstanbul yerel saati: tarih eşleşmesi o takvimde
    guncelleme_mi: bool
    duzeltme_mi: bool
    onceki_tarihler: tuple[date, ...]
    # Skora giren kalemler (değer, para birimi) — yayındaki çıkarımdan.
    kalemler: frozenset[tuple[Decimal, str]]
    # Ham metindeki büyük sayılar: skorsuz bildirimde de ortaklık görülsün.
    metin_sayilari: frozenset[Decimal]


@dataclass(frozen=True)
class Bag:
    kap_id: str
    onceki_kap_id: str
    tur: str
    yontem: str


def _ortaklik(a: BagGirdisi, b: BagGirdisi) -> int:
    return len(a.kalemler & b.kalemler) + len(a.metin_sayilari & b.metin_sayilari)


def baglari_kur(girdiler: Sequence[BagGirdisi]) -> list[Bag]:
    hisse: dict[str, list[BagGirdisi]] = {}
    for g in sorted(girdiler, key=lambda g: g.an):
        hisse.setdefault(g.ticker, []).append(g)

    baglar: list[Bag] = []
    for g in girdiler:
        if not (g.guncelleme_mi or g.duzeltme_mi):
            continue
        onceki = [a for a in hisse[g.ticker] if a.an < g.an]
        # İki aday kaynağı: şirketin verdiği tarihteki bildirimler ve
        # pencere içinde tutarı ortak olanlar. Tarih çoğu zaman sürecin
        # İLK duyurusunu gösteriyor, aradaki bildirimi değil (ONRYT
        # 01.12.2025 → 2024-09-20; aynı 9,6 mn USD 11.11.2025'te
        # duyurulmuştu). Ortaklık şartı MIATK'yi korur: ilgisiz işle ortak
        # tutar yok.
        tarihler = set(g.onceki_tarihler)
        pencere = DUZELTME_PENCERESI if g.duzeltme_mi else GUNCELLEME_PENCERESI
        adaylar = {
            a.kap_id: a
            for a in onceki
            if a.an.date() in tarihler
            or (g.an - a.an <= pencere and _ortaklik(a, g) > 0)
        }
        if not adaylar:
            continue

        secilen = max(adaylar.values(), key=lambda a: (_ortaklik(a, g), a.an))
        yontem = "kap_tarih" if secilen.an.date() in tarihler else "tutar"
        if g.duzeltme_mi:
            tur = "duzeltme"
        elif g.kalemler & secilen.kalemler:
            tur = "ayni_is"
        else:
            tur = "guncelleme"
        baglar.append(Bag(g.kap_id, secilen.kap_id, tur, yontem))
    return baglar
