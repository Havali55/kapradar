"""Resmî TÜFE: aylık değişimlerden zincirlenen oran.

Kaynak: TÜİK tüketici fiyatları, TCMB'nin yayımladığı tablo
(tcmb.gov.tr → İstatistikler → Enflasyon Verileri → Tüketici Fiyatları),
2026-09-27'de aktarıldı. `tufe_aylik.csv` aylık ve yıllık yüzde
değişimleri taşıyor; tutarlılığını tests/test_tufe.py sınıyor (aylık
değişimlerin 12 aylık zinciri yayımlanan yıllık oranı vermeli).

Neden dış veri: skorun paydasında yıllık terimi cari birime taşıyan
katsayı normalde şirketin kendi TMS 29 yeniden ifadesinden okunuyor.
Bu, karşılaştırılan dönemin ilk yayını TMS 29 öncesiyse (2023 ara
dönemleri) enflasyonu değil muhasebe geçişini ölçüyor, ilk yayın
arşivde yoksa hiç okunamıyor. Bkz. `finansal.ttm_coz`.

Point-in-time: M ayının TÜFE'si M+1 ayının 3'ünde yayımlanır. O
tarihten önceki bir an için oran verilmez.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

TABLO = Path(__file__).with_name("tufe_aylik.csv")
YAYIN_GUNU = 3


@lru_cache(maxsize=1)
def aylik_tablo() -> dict[str, tuple[Decimal, Decimal]]:
    """"YYYY-AA" → (aylık % değişim, yıllık % değişim)."""
    with TABLO.open(encoding="utf-8", newline="") as f:
        return {
            s["ay"]: (Decimal(s["aylik_yuzde"]), Decimal(s["yillik_yuzde"]))
            for s in csv.DictReader(f)
        }


def _ay(g: date) -> str:
    return f"{g.year}-{g.month:02d}"


def _yayin_tarihi(ay: str) -> date:
    yil, a = int(ay[:4]), int(ay[5:])
    return date(yil + (a == 12), a % 12 + 1, YAYIN_GUNU)


def oran(bas: date, son: date, an: datetime | None = None) -> Decimal | None:
    """TÜFE(son'un ayı) / TÜFE(bas'ın ayı).

    Ay sonu fiyat düzeyleri arasındaki oran: bas ayından sonraki
    ayların aylık değişimleri çarpılır. Tabloda eksik ay varsa ya da
    `an` son ayın TÜFE'si yayımlanmadan önceyse None.
    """
    tablo = aylik_tablo()
    b, s = _ay(bas), _ay(son)
    if s < b or b not in tablo or s not in tablo:
        return None
    if an is not None and an.date() < _yayin_tarihi(s):
        return None
    aylar = sorted(a for a in tablo if b < a <= s)
    carpim = Decimal(1)
    for a in aylar:
        carpim *= 1 + tablo[a][0] / 100
    return carpim
