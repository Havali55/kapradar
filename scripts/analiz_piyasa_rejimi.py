"""Piyasa rejimi: 2019–2026 çerçevesi, aylık spekülasyon ölçüleri, bulguların rejime duyarlılığı.

Kullanım:  python scripts/analiz_piyasa_rejimi.py

Hiçbir şey yazmaz, LLM yok. Ağa yalnız yfinance için çıkar (ücretsiz):
XU100 ve USD/TRY 2019'dan beri; veritabanımızdaki seriler 2024-01'de
başlıyor, seçim öncesi dönem için başka kaynak yok.

docs/arastirma/2026-09-27-gecerlilik-degerlendirmesi.md §3 ve §4'ü
besliyor. Sorular:

  A. Seçim öncesi (negatif reel faiz) ile sonrası (sıkı para) piyasa
     davranışı olarak ne kadar farklı? Örneklemimiz hangisinde?
  B. Son yıl gerçekten daha mı spekülatif? Ölçüler Borsa İstanbul'un
     kendi KAP kayıtlarından: pay bazında devre kesici, VBTS tedbiri,
     "olağan dışı fiyat ve miktar hareketleri" sorusu; bir de küçük
     hisselerin (eşit ağırlıklı) büyük endeksten ayrışması.
  C. Bulgular spekülatif aylarda ve sonradan tasfiye edilen fonların
     tuttuğu hisselerde farklı mı?

Politika faizi dönemleri (TCMB PPK kararları; kaynak notta):
  2019-07 → 2023-05  gevşek: faiz enflasyonun çok altında
  2023-06 → 2024-12  sıkılaştırma: %8,5 → %50
  2025-01 → …        kademeli indirim, reel faiz pozitif (Nisan 2025 ara artış)
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
import yfinance as yf

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from analiz_gecerlilik import (  # noqa: E402
    _sabit,
    hafta,
    olay_profili,
    ols_kumeli,
    piyasa_hacim_endeksi,
    piyasa_profili,
    yukle,
)
from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.baglam import DEVRE_KESICI_BASLADI, DEVRE_KESICI_KONUSU, VBTS_OZETI  # noqa: E402
from skor_gecerlilik import bas  # noqa: E402

REJIMLER = (
    ("gevşek para", date(2019, 7, 1), date(2023, 5, 31)),
    ("sıkılaştırma", date(2023, 6, 1), date(2024, 12, 31)),
    ("kademeli indirim", date(2025, 1, 1), date(2026, 12, 31)),
)
OLAGANDISI_KONU = "Olağan Dışı Fiyat ve Miktar Hareketleri"
# Örneklem dışı sınama yılı ile analiz yılının sınırı (skor_gecerlilik.ANALIZ_BASI).
SON_YIL_BASI = date(2025, 9, 22)


def yf_seri(kod: str) -> pd.Series:
    d = yf.download(kod, start="2019-01-01", progress=False, auto_adjust=False)
    d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
    s = d["Close"].dropna()
    s.index = s.index.date
    return s


def yariyil(g: date) -> str:
    return f"{g.year}Y{1 if g.month <= 6 else 2}"


# ---------------------------------------------------------------- A

def uzun_donem() -> list[date]:
    bas("A · 2019–2026: SEÇİM ÖNCESİ VE SONRASI (XU100, yfinance)")
    x = yf_seri("XU100.IS")
    u = yf_seri("TRY=X").reindex(x.index).ffill()
    usd = x / u
    r = np.log(x).diff()
    print(f"  {'yarıyıl':<8}{'TL':>9}{'USD':>9}{'oynaklık':>10}   rejim")
    for yy, gunler in pd.Series(x.index, index=x.index).groupby(lambda g: yariyil(g)):
        ilk, son = gunler.index[0], gunler.index[-1]
        onceki = x.index[max(0, x.index.get_loc(ilk) - 1)]
        rejim = next((ad for ad, b, s in REJIMLER if b <= ilk <= s), "gevşek para (öncesi)")
        print(f"  {yy:<8}{(x[son]/x[onceki]-1)*100:>+8.1f}%{(usd[son]/usd[onceki]-1)*100:>+8.1f}%"
              f"{r.loc[ilk:son].std()*math.sqrt(250)*100:>9.1f}%   {rejim}")
    print(f"  {'rejim':<18}{'gün':>6}{'yıllık TL':>11}{'yıllık USD':>12}{'oynaklık':>10}{'−%3 gün/yıl':>13}")
    for ad, b, s in REJIMLER:
        m = [g for g in x.index if b <= g <= s]
        if len(m) < 20:
            continue
        yil = (m[-1] - m[0]).days / 365.25
        tl = (x[m[-1]] / x[m[0]]) ** (1 / yil) - 1
        dl = (usd[m[-1]] / usd[m[0]]) ** (1 / yil) - 1
        rr = r.loc[m[0]:m[-1]]
        print(f"  {ad:<18}{len(m):>6}{tl*100:>+10.1f}%{dl*100:>+11.1f}%{rr.std()*math.sqrt(250)*100:>9.1f}%"
              f"{(rr < -0.03).sum() / yil:>13.1f}")
    return list(x.index)


# ---------------------------------------------------------------- B

def aylik_spekulasyon(takvim_yf: list[date]) -> pd.DataFrame:
    bas("B · AYLIK SPEKÜLASYON ÖLÇÜLERİ (Borsa İstanbul'un KAP kayıtları)")
    devre = defaultdict(int)
    devre_hisse = defaultdict(set)
    vbts = defaultdict(int)
    olagandisi = defaultdict(int)
    for k in HamArsiv(KOK / "data" / "ham").liste_kayitlari().values():
        z = datetime.strptime(k["publishDate"], "%d.%m.%Y %H:%M:%S").date()
        ay = f"{z.year}-{z.month:02d}"
        if k.get("subject") == DEVRE_KESICI_KONUSU and any(
            s in (k.get("summary") or "").lower() for s in DEVRE_KESICI_BASLADI
        ):
            devre[ay] += 1
            for t in (k.get("relatedStocks") or "").split(","):
                if t.strip():
                    devre_hisse[ay].add(t.strip())
        elif VBTS_OZETI in (k.get("summary") or ""):
            vbts[ay] += 1
        if k.get("subject") == OLAGANDISI_KONU:
            olagandisi[ay] += 1

    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        ew = pd.read_sql("select tarih, ew_getiri::float as ew from faktor_gunluk", b)
        xu = pd.read_sql("select tarih, xu100_kapanis::float as x from endeks_gunluk order by tarih", b)
    xu["r"] = xu["x"].pct_change()
    m = ew.merge(xu[["tarih", "r"]], on="tarih")
    m["ay"] = m["tarih"].map(lambda g: f"{g.year}-{g.month:02d}")
    ayrisma = m.groupby("ay").apply(
        lambda g: (1 + g["ew"]).prod() - (1 + g["r"]).prod(), include_groups=False)

    seans = defaultdict(int)
    for g in takvim_yf:
        seans[f"{g.year}-{g.month:02d}"] += 1
    aylar = sorted(a for a in devre if a >= "2023-09" and seans.get(a))
    son_ay = max(aylar)
    df = pd.DataFrame({
        "devre_seans": [devre[a] / seans[a] for a in aylar],
        "devre_hisse": [len(devre_hisse[a]) for a in aylar],
        "vbts": [vbts[a] for a in aylar],
        "olagandisi": [olagandisi[a] for a in aylar],
        "ew_xu_ayrisma": [ayrisma.get(a, np.nan) for a in aylar],
    }, index=pd.Index(aylar, name="ay"))
    print(f"  (liste arşivi son ay {son_ay} yarım ay)")
    print(f"  {'ay':<9}{'devre/seans':>12}{'hisse':>7}{'VBTS':>6}{'olağandışı':>12}{'EW−XU100':>10}")
    for a, s in df.iterrows():
        ayr = f"{s['ew_xu_ayrisma']*100:>+9.1f}%" if np.isfinite(s["ew_xu_ayrisma"]) else f"{'—':>10}"
        print(f"  {a}  {s['devre_seans']:>11.1f}{int(s['devre_hisse']):>7}{int(s['vbts']):>6}"
              f"{int(s['olagandisi']):>12}{ayr}")
    # İki örneklem yılı ve öncesi.
    def donem(a):
        g = date(int(a[:4]), int(a[5:]), 15)
        return ("2023-09→2024-08 (örneklem öncesi)" if g < date(2024, 9, 1) else
                "2024-09→2025-09 (sınama yılı)" if g < SON_YIL_BASI else "2025-09→2026-09 (analiz yılı)")
    ozet = df.groupby(df.index.map(donem)).agg(
        devre_seans=("devre_seans", "mean"), devre_hisse=("devre_hisse", "mean"),
        vbts=("vbts", "mean"), olagandisi=("olagandisi", "mean"), ayrisma=("ew_xu_ayrisma", "sum"))
    print(f"\n  {'dönem (aylık ortalama)':<36}{'devre/seans':>12}{'hisse/ay':>10}{'VBTS/ay':>9}{'olağandışı/ay':>15}{'Σ EW−XU':>9}")
    for ad, s in ozet.iterrows():
        print(f"  {ad:<36}{s['devre_seans']:>12.1f}{s['devre_hisse']:>10.0f}{s['vbts']:>9.1f}"
              f"{s['olagandisi']:>15.1f}{s['ayrisma']*100:>+8.1f}%")
    return df


# ---------------------------------------------------------------- C

def rejime_duyarlilik(aylik: pd.DataFrame):
    bas("C · BULGULAR SPEKÜLATİF AYLARDA VE FON HİSSELERİNDE FARKLI MI?")
    olay, fiyat, endeks, *_ = yukle()
    takvim = list(endeks["tarih"])
    hacim = {t: g.set_index("tarih")["v"] for t, g in fiyat.groupby("ticker")}
    v = olay.dropna(subset=["t0"]).copy()
    prof = olay_profili(v, hacim, takvim, [0])
    pprof = piyasa_profili(v, piyasa_hacim_endeksi(fiyat), takvim, [0])
    ix = prof.index.intersection(pprof.index)
    v.loc[ix, "avd"] = prof.loc[ix, "av"] - pprof.loc[ix, "av"]

    # Ay tercilleri: piyasa çapında devre kesici yoğunluğu (seans başına).
    esik = aylik["devre_seans"].quantile([1 / 3, 2 / 3]).to_numpy()
    ay_sinif = {a: ("sakin" if d <= esik[0] else "orta" if d <= esik[1] else "spekülatif")
                for a, d in aylik["devre_seans"].items()}
    v["ay_sinif"] = v["t0"].map(lambda g: ay_sinif.get(f"{g.year}-{g.month:02d}"))
    print(f"  Ay sınıfı: piyasa devre kesicisi/seans tercilleri {esik[0]:.1f} / {esik[1]:.1f}")

    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        fon = pd.read_sql("select ticker, tasfiye_tl::float as tasfiye_tl, "
                          "gunluk_hacim_tl::float as hacim_tl from hisse_fon_guncel", b)
    # Yoğunluk: tasfiye fonlarının pozisyonu hissenin kaç günlük işlem hacmi.
    # Tutup tutmamak kaba bir ölçü (büyük hisseler de tutuluyor); pozisyonun
    # hacme oranı fonun o tahtadaki ağırlığını söylüyor.
    fon["gun"] = fon["tasfiye_tl"] / fon["hacim_tl"]
    gun = v["ticker"].map(fon.set_index("ticker")["gun"]).fillna(0)
    v["fon_sinif"] = np.select(
        [gun == 0, gun < 0.5, gun >= 0.5],
        ["tutmuyor", "tutuyor, < 0,5 gün hacim", "yoğun, ≥ 0,5 gün hacim"], default="?")
    print("  Fon sınıfı: Ağustos 2026 portföylerinde tasfiye fonlarının pozisyonu / günlük hacim "
          "(portföy olaydan SONRA ölçülüyor: sınıf betimleyici, nedensel değil)")

    def satir(ad, d):
        kum = lambda x: {"hisse": x["ticker"].to_numpy(), "hafta": x["t0"].map(hafta).to_numpy()}  # noqa: E731
        a = d.dropna(subset=["avd"])
        c = d.dropna(subset=["car3"])
        cv = c.dropna(subset=["v90"])
        ra = _sabit(a["avd"].to_numpy(), kum(a)) if len(a) > 20 else None
        rc = _sabit(c["car3"].to_numpy(), kum(c)) if len(c) > 20 else None
        r12 = ols_kumeli(cv["car3"], cv[["v90"]], kum(cv)) if len(cv) > 30 else None
        f = (lambda r, carp, dx: f"{r['hisse'][0]*carp:>+8.{dx}f} t2={r['iki yönlü'][1]:>+5.2f}"
             if r else f"{'—':>8} {'':>8}")
        print(f"  {ad:<24}{len(d):>5}  AV {f(ra, 100, 1)}  CAR3 {f(rc, 100, 2)}  B12 {f(r12, 100, 3)}")

    print(f"  {'grup':<24}{'n':>5}  {'AV düz. (%)':<22}{'CAR3 (%)':<24}{'B12 v90 (puan/gün)'}")
    for sinif in ("sakin", "orta", "spekülatif"):
        satir(f"ay: {sinif}", v[v["ay_sinif"] == sinif])
    for sinif in ("tutmuyor", "tutuyor, < 0,5 gün hacim", "yoğun, ≥ 0,5 gün hacim"):
        d = v[v["fon_sinif"] == sinif]
        satir(f"fon: {sinif}", d)
        print(f"  {'':<24}      ({d['ticker'].nunique()} hisse)")
    son = v["t0"].map(lambda g: g >= SON_YIL_BASI)
    satir("sınama yılı", v[~son])
    satir("analiz yılı", v[son])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    takvim = uzun_donem()
    aylik = aylik_spekulasyon(takvim)
    rejime_duyarlilik(aylik)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
