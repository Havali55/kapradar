"""Küçük hisse faktörü CAR'ı değiştiriyor mu? (model C vs iki faktörlü) — yazmaz.

Kullanım:  python scripts/faktor_kur.py && python scripts/analiz_faktor.py

    C (şu anki): AR = r − (α + β·r_m)
    D (öneri)  : AR = r − (α + β·r_m + γ·s),   s = r_ew − r_m

s = BIST eşit ağırlıklı getiri eksi XU100 — "küçük hisselerin endeksten
farkı". Tahmin penceresi, tampon, olay günü dışlama ve Vasicek küçültmesi
C ile aynı (tepki.py sabitleri); γ de kendi evren ortalamasına küçültülüyor.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.tepki import (  # noqa: E402
    BETA_ASGARI_GOZLEM,
    BETA_PENCERE,
    BETA_SICRAMA_ESIGI,
    BETA_TAMPON,
    getiri_serisi,
)

KAPANIS_CSV = KOK / "data" / "ham" / "evren" / "kapanis.csv"
OLAY_GUNU = 3


def kucult(tahmin: np.ndarray, se: np.ndarray) -> np.ndarray:
    capa = tahmin.mean()
    kv = max(tahmin.var() - (se**2).mean(), 1e-6)
    w = kv / (kv + se**2)
    return w * tahmin + (1 - w) * capa


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import faktor_kur  # aynı dizin

    kap = pd.read_csv(KAPANIS_CSV, index_col=0, parse_dates=True)
    ew = faktor_kur.ew_seri(kap)["ew_getiri"]
    ew.index = [t.date() for t in ew.index]

    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        depo = Depo(b)
        with b.cursor() as c:
            c.execute("select min(tarih), max(tarih) from endeks_gunluk")
            ilk, son = c.fetchone()
            c.execute(
                "select b.kap_id, b.ticker, t.t0, t.car_3g, t.beta_kaynak, "
                "  c.etki_skoru, td.bayrak "
                "from bildirim b join tepki t using (kap_id) "
                "left join lateral (select etki_skoru from cikarim c2 "
                "  where c2.kap_id = b.kap_id order by id desc limit 1) c on true "
                "left join tahta_durumu td using (kap_id) where t.t0 is not null"
            )
            olaylar = c.fetchall()
        endeks = depo.endeks_serisi(ilk, son)
        gunler = sorted(endeks)
        piyasa = getiri_serisi(endeks, gunler)
        hisse = {t: getiri_serisi(depo.fiyat_serisi(t, ilk, son), gunler)
                 for t in {o[1] for o in olaylar}}

    s = {g: ew[g] - piyasa[g] for g in piyasa if g in ew and pd.notna(ew[g])}
    sira = {g: i for i, g in enumerate(gunler)}
    olay_gun: dict[str, set] = {}
    for _, t, t0, *_ in olaylar:
        olay_gun.setdefault(t, set()).update(gunler[sira[t0]: sira[t0] + OLAY_GUNU])

    kayit = []
    for kap_id, t, t0, car_c, kaynak, skor, bayrak in olaylar:
        if kaynak != "tahmin" or car_c is None:
            continue
        i = sira[t0]
        bit = i - BETA_TAMPON
        pencere = gunler[max(1, bit - BETA_PENCERE): bit]
        gun = [g for g in pencere if g in hisse[t] and g in piyasa and g in s
               and g not in olay_gun[t] and abs(hisse[t][g]) < BETA_SICRAMA_ESIGI]
        if len(gun) < BETA_ASGARI_GOZLEM:
            continue
        X = np.column_stack([np.ones(len(gun)), [piyasa[g] for g in gun], [s[g] for g in gun]])
        y = np.array([hisse[t][g] for g in gun])
        k, *_ = np.linalg.lstsq(X, y, rcond=None)
        kalan = y - X @ k
        cov = (kalan @ kalan / (len(y) - 3)) * np.linalg.inv(X.T @ X)
        # E: tek faktör, kıyas eşit ağırlıklı BIST (r_ew = r_m + s).
        Xe = np.column_stack([np.ones(len(gun)), [piyasa[g] + s[g] for g in gun]])
        ke, *_ = np.linalg.lstsq(Xe, y, rcond=None)
        kalan_e = y - Xe @ ke
        se_e = np.sqrt((kalan_e @ kalan_e / (len(y) - 2)) / ((Xe[:, 1] - Xe[:, 1].mean()) ** 2).sum())
        r2_c = 1 - ((y - np.column_stack([np.ones(len(gun)), X[:, 1]]) @ np.linalg.lstsq(
            np.column_stack([np.ones(len(gun)), X[:, 1]]), y, rcond=None)[0]) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        r2_e = 1 - (kalan_e @ kalan_e) / ((y - y.mean()) ** 2).sum()
        pen = gunler[i: i + 3]
        if len(pen) < 3 or any(g not in hisse[t] or g not in s for g in pen):
            continue
        kayit.append(dict(
            kap_id=kap_id, ticker=t, t0=t0, car_c=float(car_c), skor=skor, bayrak=bayrak,
            alfa=k[0], beta=k[1], gamma=k[2], se_b=np.sqrt(cov[1, 1]), se_g=np.sqrt(cov[2, 2]),
            alfa_e=ke[0], beta_e=ke[1], se_e=se_e, r2_c=r2_c, r2_e=r2_e,
            rm=[piyasa[g] for g in pen], sf=[s[g] for g in pen], ri=[hisse[t][g] for g in pen],
        ))

    d = pd.DataFrame(kayit)
    d["beta_k"] = kucult(d["beta"].to_numpy(), d["se_b"].to_numpy())
    d["gamma_k"] = kucult(d["gamma"].to_numpy(), d["se_g"].to_numpy())
    d["car_d"] = [
        sum(ri - (r.alfa + r.beta_k * rm + r.gamma_k * sf)
            for ri, rm, sf in zip(r.ri, r.rm, r.sf))
        for r in d.itertuples()
    ]
    d["beta_ek"] = kucult(d["beta_e"].to_numpy(), d["se_e"].to_numpy())
    d["car_e"] = [
        sum(ri - (r.alfa_e + r.beta_ek * (rm + sf)) for ri, rm, sf in zip(r.ri, r.rm, r.sf))
        for r in d.itertuples()
    ]
    print(f"açıklanan varyans (medyan R²): XU100 {d['r2_c'].median():.3f} · "
          f"eşit ağırlıklı BIST {d['r2_e'].median():.3f}")
    print(f"E betası (küçültülmüş): ort {d['beta_ek'].mean():.3f}")
    print(f"E: ort %{d['car_e'].mean() * 100:+.2f}  medyan %{d['car_e'].median() * 100:+.2f} · "
          f"D ile korelasyon {np.corrcoef(d['car_d'], d['car_e'])[0, 1]:.4f} · "
          f"C ile {np.corrcoef(d['car_c'], d['car_e'])[0, 1]:.4f}")
    fark = d["car_d"] - d["car_c"]

    print("=" * 72)
    print(f"bildirim: {len(d)}  (C'de beta_kaynak=tahmin olanlar)")
    print(f"γ (küçük hisse duyarlılığı) ham: ort {d['gamma'].mean():+.3f} medyan "
          f"{d['gamma'].median():+.3f} · küçültülmüş ort {d['gamma_k'].mean():+.3f} "
          f"· γ>0 oranı %{(d['gamma_k'] > 0).mean() * 100:.0f}")
    print(f"β iki faktörde: ort {d['beta_k'].mean():.3f}")
    for ad, kol in (("C", "car_c"), ("D", "car_d")):
        print(f"  {ad}: ort %{d[kol].mean() * 100:+.2f}  medyan %{d[kol].median() * 100:+.2f}  "
              f"std %{d[kol].std() * 100:.2f}")
    print(f"  korelasyon {np.corrcoef(d['car_c'], d['car_d'])[0, 1]:.4f} · ort mutlak fark "
          f"{fark.abs().mean() * 100:.2f}p · |fark|>1p {int((fark.abs() > .01).sum())} · "
          f"işaret değişen {int(((d['car_c'] > 0) != (d['car_d'] > 0)).sum())}")

    eyl = d["t0"] >= date(2026, 9, 9)
    print(f"\n9 Eylül sonrası t0 (fon krizi): n={int(eyl.sum())}")
    if eyl.any():
        print(f"  C ort %{d.loc[eyl, 'car_c'].mean() * 100:+.2f} → D ort "
              f"%{d.loc[eyl, 'car_d'].mean() * 100:+.2f}")
    print(f"kriz öncesi: C ort %{d.loc[~eyl, 'car_c'].mean() * 100:+.2f} → D ort "
          f"%{d.loc[~eyl, 'car_d'].mean() * 100:+.2f}")

    d["kademe"] = pd.cut(pd.to_numeric(d["skor"]), [-1, 2.5, 3.5, 6],
                         labels=["rutin", "onemli", "mega"], right=False)
    print("\nModül C panel medyanları (kademe | tahta, n≥20):")
    for (k, t), g in d.groupby(["kademe", "bayrak"], observed=True):
        if len(g) >= 20:
            print(f"  {k}|{t:<10} n={len(g):>3}  C %{g['car_c'].median() * 100:+.2f}  "
                  f"D %{g['car_d'].median() * 100:+.2f}  E %{g['car_e'].median() * 100:+.2f}")
    print("\nHiçbir şey yazılmadı.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(KOK / "scripts"))
    raise SystemExit(main())
