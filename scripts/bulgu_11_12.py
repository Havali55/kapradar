"""Bulgu 11 ve 12'yi güncel ölçülerle yeniden sınar. Hiçbir şey yazmaz.

Kullanım:  python scripts/bulgu_11_12.py [--donem analiz|sinama|tumu]

İlk sürüm (`skor_gecerlilik.py` §10–11) iki şeyi eskimiş ölçüyle yapıyordu:
  - CAR, β = 1 ve XU100 farkıydı. Artık tepki tablosu eşit ağırlıklı
    BIST'e karşı piyasa modeliyle hesaplanıyor (tepki.model = 'ew').
  - Tahta, "90 günde |getiri| ≥ %9 gün sayısı" vekiliydi. Artık Borsa
    İstanbul'un KAP kayıtlarından: devre kesici günü (tahta_durumu.v90)
    ve bildirim anında yürürlükte VBTS (vbts_kademe > 0).

Evren sitenin gördüğü evren: `akis` (yalnız yayına hazır bildirimler).
Sorular değişmedi:
  11. Büyük haber küçük haberden daha çok fiyatlanıyor mu?
  12. Oynak tahta daha çok mu hareket ediyor, yönlü mü hareket ediyor?
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
    DONEMLER,
    bas,
    donem_suz,
    ols,
    tek_orneklem,
    yildiz,
)

KRIZ_BASI = pd.Timestamp("2026-09-08")

SORGU = """
select a.kap_id, a.ticker, a.yayin_zamani, a.etki_skoru::float as s, a.car_3g::float as car3,
       t.v90, (coalesce(t.vbts_kademe, 0) > 0) as vbts, tp.t0
from akis a
left join tahta_durumu t on t.kap_id = a.kap_id
left join tepki tp on tp.kap_id = a.kap_id
"""


def grup_satiri(ad: str, g: pd.DataFrame) -> None:
    car = g["car3"].dropna().to_numpy(float)
    if len(car) < 10:
        print(f"  {ad:<16} n={len(car)} (yetersiz)")
        return
    t_, p_ = tek_orneklem(car)
    # Aynı hissenin bildirimleri bağımsız değil: sabit terimli OLS'de
    # hisse-kümelenmiş t, tek örneklem t'sinin dürüst karşılığı.
    d = g.dropna(subset=["car3"])
    tk = ols(d["car3"], np.zeros((len(d), 0)), d["ticker"], []).loc["sabit"]
    print(f"  {ad:<16} n={len(car):>3}  hisse={d['ticker'].nunique():>3}  "
          f"ort={car.mean()*100:+.2f}%  medyan={np.median(car)*100:+.2f}%  "
          f"pozitif=%{(car > 0).mean()*100:.0f}  "
          f"t={t_:+.2f}{yildiz(t_):<3} t_kume={tk['t']:+.2f}{yildiz(tk['t'])}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--donem", choices=DONEMLER, default="analiz")
    secenek = ap.parse_args()
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        df = pd.read_sql(SORGU, b)
    df = donem_suz(df, secenek.donem)
    print(f"dönem: {secenek.donem} · {len(df)} bildirim")
    df["abs_car3"] = df["car3"].abs()

    bas("11 · BÜYÜK HABER DAHA ÇOK FİYATLANIYOR MU?  (CAR3, EW piyasa modeli)")
    s = df.dropna(subset=["s"])
    grup_satiri("S >= 3", s[s["s"] >= 3])
    grup_satiri("S >= 3,5 (mega)", s[s["s"] >= 3.5])
    grup_satiri("S < 1", s[s["s"] < 1])
    d = s.dropna(subset=["car3"])
    r = ols(d["car3"], d[["s"]], d["ticker"], ["s"]).loc["s"]
    print(f"  CAR3 ~ S (kümelenmiş)  katsayı={r['katsayi']*100:+.3f} puan/S  "
          f"t={r['t']:+.2f}{yildiz(r['t'])}  p={r['p']:.3f}  n={int(r['n'])}")

    bas("12 · OYNAK TAHTA: OYNAKLIK VAR MI, YÖN VAR MI?  (gerçek devre kesici + VBTS)")
    v = df.dropna(subset=["car3", "v90"])
    print(f"  Evren: n={len(v)}  v90 ort={v['v90'].mean():.1f} medyan={v['v90'].median():.0f}"
          f"  VBTS yürürlükte={int(v['vbts'].sum())}")
    for ad, y in (("|CAR3|", v["abs_car3"]), ("CAR3 işaretli", v["car3"])):
        r = ols(y, v[["v90"]], v["ticker"], ["v90"]).loc["v90"]
        print(f"  {ad:<14} ~ v90   katsayı={r['katsayi']*100:+.3f} puan/gün  "
              f"t={r['t']:+.2f}{yildiz(r['t'])}  p={r['p']:.4f}")
    for ad, y in (("|CAR3|", v["abs_car3"]), ("CAR3 işaretli", v["car3"])):
        r = ols(y, v[["vbts"]].astype(float), v["ticker"], ["vbts"]).loc["vbts"]
        print(f"  {ad:<14} ~ VBTS  katsayı={r['katsayi']*100:+.3f} puan  "
              f"t={r['t']:+.2f}{yildiz(r['t'])}  p={r['p']:.4f}")
    # Sağlamlık: Eylül 2026 fon krizi (8 Eylül'den itibaren küçük hisselerde
    # sert düşüş, 16 Eylül'de XU100 −%5,5). Tedbirli tahtalar bu günlere
    # yığılıyorsa "aşağı yön" tahtadan değil krizden gelir.
    k = v[pd.to_datetime(v["t0"]) < KRIZ_BASI]
    print(f"  --- kriz hariç (t0 < {KRIZ_BASI.date()}), n={len(k)}")
    for ad, y in (("|CAR3|", k["abs_car3"]), ("CAR3 işaretli", k["car3"])):
        r = ols(y, k[["v90"]], k["ticker"], ["v90"]).loc["v90"]
        print(f"  {ad:<14} ~ v90   katsayı={r['katsayi']*100:+.3f} puan/gün  "
              f"t={r['t']:+.2f}{yildiz(r['t'])}  p={r['p']:.4f}")
    # Skor kontrolü: tedbirli tahtalar farklı büyüklükte bildirim
    # yapıyorsa v90'ın işareti skordan sızıyor olabilir.
    ks = v.dropna(subset=["s"])
    r = ols(ks["car3"], ks[["v90", "s"]], ks["ticker"], ["v90", "s"])
    print(f"  CAR3 ~ v90 + S (n={int(r.loc['v90','n'])})  v90={r.loc['v90','katsayi']*100:+.3f} "
          f"t={r.loc['v90','t']:+.2f}{yildiz(r.loc['v90','t'])}  "
          f"S={r.loc['s','katsayi']*100:+.3f} t={r.loc['s','t']:+.2f}")
    ic = v[pd.to_datetime(v["t0"]) >= KRIZ_BASI]
    print(f"  kriz penceresindeki bildirim: {len(ic)}  "
          f"(tedbirli {int(((ic['v90'] > 8) | ic['vbts']).sum())})")
    for ad, g in (("temiz (v90<=4)", v[(v["v90"] <= 4) & ~v["vbts"]]),
                  ("tedbirli", v[(v["v90"] > 8) | v["vbts"]])):
        print(f"  {ad:<16} n={len(g):>3}  ort |CAR3|={g['abs_car3'].mean()*100:.2f}%  "
              f"ort CAR3={g['car3'].mean()*100:+.2f}%")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
