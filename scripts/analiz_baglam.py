"""Bulgu 7 ve 16b'yi gerçek bağlam verisiyle yeniden sınar. Hiçbir şey yazmaz.

Kullanım:
    python scripts/analiz_baglam.py                  # analiz örneklemi (2025-09-22 →)
    python scripts/analiz_baglam.py --donem sinama   # örneklem dışı: 2024-09 → 2025-09-21
    python scripts/analiz_baglam.py --donem tumu

Bulgular 2025-09-22 → 2026-09-18 örnekleminde (613 bildirim) kuruldu. Arşiv
2026-09-24'te 2024-09'a uzatıldı; önceki 12 ay o bulguları KURARKEN hiç
görülmedi, yani onlar için gerçek bir örneklem dışı sınama.

İki soru:
  1. Bildirim yorgunluğu (Bulgu 7) ileriye bakan sayımın ürünü müydü?
     Eski: şirketin arşivdeki TÜM Yeni İş İlişkisi sayısı (lookahead).
     Yeni: bildirimden önceki 12 ay (siklik_durumu.yeni_is_12a) ve
     şirketin tüm özel durum açıklamaları (kap_oda_12a).
  2. "Skor–ilgi ilişkisi temiz tahtada var, spekülatif tahtada yok"
     (Adım 16b) gerçek ölçüyle de tutuyor mu?
     Eski: limit yakını gün vekili. Yeni: devre kesici günü (v90) ve
     bildirim anında yürürlükte VBTS.

AV, OLS ve kümelenmiş standart hata `skor_gecerlilik.py`'den geliyor —
ölçü değişmesin, yalnız bağlam değişsin.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from skor_gecerlilik import (  # noqa: E402
    anormal_hacim,
    bas,
    hacim_serileri,
    limit_sayaci,
    ols,
    yukle,
)

# baglam_hesapla.py --kuru çıktısı: bayrak canlı tabloya yazılmadan sınanabilsin.
BAGLAM_CSV = KOK / "data" / "baglam_kap_v1.csv"
# Analiz örnekleminin ilk bildirimi; öncesi örneklem dışı sınama dönemi.
ANALIZ_BASI = pd.Timestamp("2025-09-22", tz="Europe/Istanbul")


def satir(ad: str, sonuc: pd.DataFrame, terim: str, n: int, hisse: int) -> None:
    r = sonuc.loc[terim]
    print(f"  {ad:<34} n={n:>4} hisse={hisse:>3}  "
          f"katsayı={r['katsayi']:+.4f}  t={r['t']:+.2f}  p={r['p']:.3f}")


def grup_sinavi(sv: pd.DataFrame, gruplar) -> None:
    for ad, maske in gruplar:
        g = sv[maske]
        if len(g) < 30:
            print(f"  {ad:<34} n={len(g):>4}  (az gözlem, atlandı)")
            continue
        sonuc = ols(g["av"], g[["etki_skoru"]], g["ticker"], ["S"])
        satir(ad, sonuc, "S", len(g), g["ticker"].nunique())
        print(f"  {'':<34} ort. hacim artışı %{(np.exp(g['av'].mean()) - 1) * 100:+.1f}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--donem", choices=("analiz", "sinama", "tumu"), default="analiz")
    secenek = ap.parse_args()
    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1
    with psycopg.connect(dsn, connect_timeout=30) as baglanti:
        olay, fiyat, endeks = yukle(baglanti)
    if not BAGLAM_CSV.exists():
        print("!! önce: python scripts/baglam_hesapla.py --kuru", file=sys.stderr)
        return 1
    baglam = pd.read_csv(BAGLAM_CSV, dtype={"kap_id": str})

    takvim = list(endeks["tarih"])
    olay["av"] = anormal_hacim(olay, hacim_serileri(fiyat), takvim)
    olay["limit90"] = limit_sayaci(olay, fiyat, takvim)
    olay = olay.merge(baglam, on="kap_id", how="left")
    for k in ("etki_skoru", "ciro_orani", "net_tutar_tl", "car_3g"):
        olay[k] = pd.to_numeric(olay[k], errors="coerce")
    olay["siklik_eski"] = olay.groupby("ticker")["ticker"].transform("size")
    olay["ln_siklik_eski"] = np.log(olay["siklik_eski"])
    olay["ln_siklik_pit"] = np.log(olay["yeni_is_12a"])
    olay["ln_oda"] = np.log(olay["kap_oda_12a"].clip(lower=1))

    zaman = pd.to_datetime(olay["yayin_zamani"], utc=True)
    if secenek.donem == "analiz":
        olay = olay[zaman >= ANALIZ_BASI]
    elif secenek.donem == "sinama":
        olay = olay[zaman < ANALIZ_BASI]
    print(f"dönem: {secenek.donem} · {len(olay)} bildirim")

    tum = olay[olay["av"].notna()].copy()
    sv = tum[tum["etki_skoru"].notna()].copy()

    # ------------------------------------------------------------- 1
    bas("1 · BİLDİRİM YORGUNLUĞU — lookahead'siz yeniden sınama")
    print("  Bağımlı: AV. Std. hata hisse bazında kümelenmiş (CR1).\n")
    for ad, kol in (("ln(sıklık) ESKİ · tüm arşiv", "ln_siklik_eski"),
                    ("ln(sıklık) PIT · önceki 12 ay", "ln_siklik_pit"),
                    ("ln(tüm ÖDA) PIT · önceki 12 ay", "ln_oda")):
        for kume_ad, d in (("skorlu", sv), ("tümü", tum)):
            d = d.dropna(subset=[kol])
            sonuc = ols(d["av"], d[[kol]], d["ticker"], [kol])
            satir(f"{ad} [{kume_ad}]", sonuc, kol, len(d), d["ticker"].nunique())
    d = tum.dropna(subset=["ln_siklik_pit", "ln_oda"])
    print("\n  İkisi birlikte (tümü):")
    sonuc = ols(d["av"], d[["ln_siklik_pit", "ln_oda"]], d["ticker"],
                ["ln_siklik_pit", "ln_oda"])
    for terim in ("ln_siklik_pit", "ln_oda"):
        satir(f"  {terim}", sonuc, terim, len(d), d["ticker"].nunique())
    tam = d[d["arsiv_gun"] >= 365]
    sonuc = ols(tam["av"], tam[["ln_siklik_pit"]], tam["ticker"], ["ln_siklik_pit"])
    satir("PIT, yalnız 12 ayı tam olanlar", sonuc, "ln_siklik_pit",
          len(tam), tam["ticker"].nunique())

    # ------------------------------------------------------------- 2
    bas("2 · TAHTA AYRIŞMASI (16b) — vekil ve gerçek ölçü yan yana")
    print("  S ~ AV, gruba göre.\n")
    print("  [vekil] limit yakını gün (90 seans):")
    grup_sinavi(sv, (("temiz (≤1)", sv["limit90"] <= 1),
                     ("orta (2–4)", sv["limit90"].between(2, 4)),
                     ("spekülatif (≥5)", sv["limit90"] >= 5)))
    print("\n  [gerçek] yürürlükte VBTS:")
    grup_sinavi(sv, (("VBTS yok", sv["vbts_kademe"] == 0),
                     ("VBTS var", sv["vbts_kademe"] > 0)))
    u1, u2 = sv["dk90"].quantile([1 / 3, 2 / 3])
    print(f"\n  [gerçek] devre kesici günü (90 seans), üçlükler {u1:.0f} / {u2:.0f}:")
    grup_sinavi(sv, ((f"alt (≤{u1:.0f})", sv["dk90"] <= u1),
                     ("orta", (sv["dk90"] > u1) & (sv["dk90"] <= u2)),
                     (f"üst (>{u2:.0f})", sv["dk90"] > u2)))
    print("\n  [gerçek] onaylı eşiklerle bayrak (kap_v1):")
    grup_sinavi(sv, tuple((b, sv["bayrak"] == b)
                          for b in ("temiz", "hareketli", "tedbirli")))

    bas("3 · ÖLÇÜLER BİRBİRİNİ NE KADAR TUTUYOR")
    d = tum.dropna(subset=["limit90", "dk90"])
    print(f"  limit90 ~ dk90   Spearman ρ = "
          f"{d['limit90'].rank().corr(d['dk90'].rank()):+.3f}  (n={len(d)})")
    print(f"  dk90 dağılımı: medyan {d['dk90'].median():.0f}, "
          f"%25 {d['dk90'].quantile(.25):.0f}, %75 {d['dk90'].quantile(.75):.0f}, "
          f"max {d['dk90'].max():.0f}")
    print(f"  yürürlükte VBTS: {(tum['vbts_kademe'] > 0).sum()} / {len(tum)}")
    print("\nHiçbir şey yazılmadı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
