"""K1 · Rejim sınaması: bulgular başka para rejimlerinde de var mı?

Ön kayıt: docs/arastirma/2026-09-28-k1-on-kayit.md (hipotezler, tanımlar,
karar kuralları sonuçlardan önce sabitlendi). Bu betik yalnız okur: LLM
yok, ücret yok, veritabanına yazmaz.

    python scripts/analiz_k1_rejim.py            # bütün tablolar
    python scripts/analiz_k1_rejim.py --kaynak   # + C döneminde bülten/yfinance karşılaştırması (DB okur)

Girdiler:
  - data/ham_rejim/thb/        Borsa İstanbul günlük bültenleri (rejim_arsivi.py bulten)
  - data/ham_rejim/liste/      KAP listesi 2020-01 → 2023-08 (rejim_arsivi.py kap)
  - data/ham/liste*/           KAP listesi 2023-09 → (canlı hat)
Çıktı: data/ham_rejim/k1_olaylar.csv (olay başına ölçüler, yeniden üretim için).

Tanımlar üretimdeki koddan içe aktarılıyor, kopyalanmıyor: t0 `tepki.t0_bul`,
beta `tepki.beta_tahmin` + `vasicek_kucult`, hacim profili ve karışan
açıklama `analiz_gecerlilik`, pencereler `skor_gecerlilik`.
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from analiz_gecerlilik import (  # noqa: E402
    KATEGORILER,
    _sabit,
    hafta,
    karisan,
    olay_profili,
    ols_kumeli,
    piyasa_hacim_endeksi,
    piyasa_profili,
)
from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.backfill import YENI_IS_ILISKISI  # noqa: E402
from kap_radar.bulten import marj, zip_oku  # noqa: E402
from kap_radar.tepki import BetaTahmini, beta_tahmin, t0_bul, vasicek_kucult  # noqa: E402
from skor_gecerlilik import OLAY_PENCERE, TAHMIN_BAS, bas, yildiz  # noqa: E402

ISTANBUL = ZoneInfo("Europe/Istanbul")
REJIM_KOK = KOK / "data" / "ham_rejim"
PANEL = REJIM_KOK / "panel.pkl"
CIKTI = REJIM_KOK / "k1_olaylar.csv"

DONEMLER = (
    ("A", "gevşek para", date(2020, 1, 1), date(2023, 5, 31)),
    ("A1", "  pandemi ve bireysel akın", date(2020, 1, 1), date(2021, 12, 31)),
    ("A2", "  seçim öncesi ralli", date(2022, 1, 1), date(2023, 5, 31)),
    ("B", "sıkılaştırma", date(2023, 6, 1), date(2024, 8, 31)),
    ("C", "bulguların dönemi", date(2024, 9, 1), date(2026, 9, 25)),
)
# V90 alt sınırı (skor_gecerlilik.LIMIT_ESIGI); üst sınır günün marjı.
LIMIT_ALT = 0.09
V90_GUN = 90
ON_HACIM_GUNLERI = (-4, -3, -2, -1)
PROFIL_GUNLERI = tuple(range(-5, 6))
# %80 güç, iki yönlü %5: MDE ≈ (1,96 + 0,84) · SE.
MDE_KATSAYI = 2.8


# ---------------------------------------------------------------- veri

def panel_yukle() -> pd.DataFrame:
    """Bültenlerden pay-günü paneli; önbellek `panel.pkl`."""
    if PANEL.exists():
        return pd.read_pickle(PANEL)
    satir = []
    for yol in sorted((REJIM_KOK / "thb").glob("*/*.zip")):
        for x in zip_oku(yol):
            g = x.getiri
            satir.append((x.tarih, x.ticker, x.kapanis, x.adet, x.hacim_tl,
                          np.nan if g is None else g))
    p = pd.DataFrame(satir, columns=["tarih", "ticker", "kapanis", "adet", "hacim", "r"])
    p["marj"] = p["tarih"].map(marj)
    p.to_pickle(PANEL)
    return p


def liste_tablosu() -> pd.DataFrame:
    """İki KAP arşivi birlikte: (ticker, gun, konu, idx, zaman), bütün türler."""
    kayit: dict[int, dict] = {}
    for kok in (REJIM_KOK, KOK / "data" / "ham"):
        kayit.update(HamArsiv(kok).liste_kayitlari())
    satir = []
    for k in kayit.values():
        z = datetime.strptime(k["publishDate"], "%d.%m.%Y %H:%M:%S").replace(tzinfo=ISTANBUL)
        for t in (x.strip() for x in (k.get("stockCodes") or "").split(",")):
            if t:
                satir.append((t, z.date(), k.get("subject") or "", int(k["disclosureIndex"]), z))
    return pd.DataFrame(satir, columns=["ticker", "gun", "konu", "idx", "zaman"])


def olaylar_kur(liste: pd.DataFrame, takvim: list[date], paylar: set[str]) -> pd.DataFrame:
    """"Yeni İş İlişkisi" olayları, t0'lı ve (pay, t0) başına tekil."""
    o = liste[(liste["konu"] == YENI_IS_ILISKISI) & liste["ticker"].isin(paylar)].copy()
    o = o[(o["gun"] >= DONEMLER[0][2]) & (o["gun"] <= DONEMLER[-1][3])]
    o["t0"] = [t0_bul(z, takvim) for z in o["zaman"]]
    o = o.dropna(subset=["t0"]).sort_values("zaman")
    o = o.drop_duplicates(["ticker", "t0"], keep="first").reset_index(drop=True)
    return o.rename(columns={"idx": "kap_index"})


# ------------------------------------------------------------- ölçüler

def seriler(p: pd.DataFrame):
    """Pay başına getiri (marjı aşanlar hariç) ve adet serileri, piyasa getirisi."""
    temiz = p[p["r"].notna() & (p["r"].abs() <= p["marj"])]
    getiri = {t: g.set_index("tarih")["r"] for t, g in temiz.groupby("ticker")}
    ham_getiri = {t: g.set_index("tarih")["r"] for t, g in p[p["r"].notna()].groupby("ticker")}
    adet = {t: g.set_index("tarih")["adet"] for t, g in p.groupby("ticker")}
    piyasa = temiz.groupby("tarih")["r"].mean()
    return getiri, ham_getiri, adet, piyasa


def marj_asan(olay, ham_getiri, marjlar, takvim, bas_k, son_k) -> pd.Series:
    """[t0+bas_k, t0+son_k] içinde marjı aşan gün var mı (sermaye işlemi)."""
    ix = {g: i for i, g in enumerate(takvim)}
    out = {}
    for i, o in olay.iterrows():
        i0 = ix[o["t0"]]
        gunler = takvim[max(0, i0 + bas_k): min(len(takvim), i0 + son_k + 1)]
        s = ham_getiri.get(o["ticker"])
        if s is None:
            out[i] = False
            continue
        r = s.reindex(gunler).dropna()
        out[i] = any(abs(x) > marjlar[g] for g, x in r.items())
    return pd.Series(out)


def v90(olay, getiri, marjlar, takvim) -> pd.Series:
    """Önceki 90 işlem gününde %9 ≤ |r| ≤ marj olan gün sayısı (≥ 30 geçerli gün)."""
    ix = {g: i for i, g in enumerate(takvim)}
    out = {}
    for i, o in olay.iterrows():
        i0 = ix[o["t0"]]
        s = getiri.get(o["ticker"])
        if s is None:
            continue
        r = s.reindex(takvim[max(0, i0 - V90_GUN): i0]).dropna()
        if len(r) >= 30:
            out[i] = float((r.abs() >= LIMIT_ALT).sum())
    return pd.Series(out, dtype=float)


def car3(olay, getiri, piyasa, takvim) -> pd.DataFrame:
    """Piyasa modeli CAR [t0, t0+2]; beta dönem içinde Vasicek ile küçültülür.

    Tahmin penceresinden aynı payın diğer olay pencereleri ve marjı aşan
    günler dışlı (ikincisi `getiri`'de zaten yok). Tahmin çıkmayan olay
    (yeni halka arz) dönem çapası β ve α = 0 alır, üretimdeki `evren_ort`
    gibi.
    """
    ix = {g: i for i, g in enumerate(takvim)}
    pz = piyasa.to_dict()
    pencereler: dict[str, set[date]] = {}
    for _, o in olay.iterrows():
        i0 = ix[o["t0"]]
        pencereler.setdefault(o["ticker"], set()).update(takvim[i0: i0 + OLAY_PENCERE])
    tahmin: dict[int, BetaTahmini] = {}
    for i, o in olay.iterrows():
        s = getiri.get(o["ticker"])
        if s is None:
            continue
        i0 = ix[o["t0"]]
        kendi = set(takvim[i0: i0 + OLAY_PENCERE])
        b = beta_tahmin(s.to_dict(), pz, takvim, o["t0"], pencereler[o["ticker"]] - kendi)
        if b is not None:
            tahmin[i] = b
    satir = {}
    for kod, _, bas_g, son_g in DONEMLER:
        if kod in ("A1", "A2"):
            continue  # A'nın çapası kullanılır
        sec = [i for i in tahmin if bas_g <= olay.at[i, "gun"] <= son_g]
        if not sec:
            continue
        capa, kucuk = vasicek_kucult([tahmin[i] for i in sec])
        kb = dict(zip(sec, kucuk))
        for i, o in olay[(olay["gun"] >= bas_g) & (olay["gun"] <= son_g)].iterrows():
            s = getiri.get(o["ticker"])
            if s is None:
                continue
            beta, alfa = (kb[i], tahmin[i].alfa) if i in kb else (capa, 0.0)
            i0 = ix[o["t0"]]
            gunler = takvim[i0: i0 + OLAY_PENCERE]
            if len(gunler) < OLAY_PENCERE or any(g not in s.index or g not in pz for g in gunler):
                continue
            satir[i] = {"car3": sum(s[g] - alfa - beta * pz[g] for g in gunler),
                        "beta": beta, "beta_kaynak": "olay" if i in kb else "capa"}
    return pd.DataFrame.from_dict(satir, orient="index")


# --------------------------------------------------------------- sınavlar

def donem_olaylari(v: pd.DataFrame, bas_g: date, son_g: date) -> pd.DataFrame:
    return v[(v["gun"] >= bas_g) & (v["gun"] <= son_g)]


def ortalama(d: pd.DataFrame, kolon: str):
    """(n, pay sayısı, ortalama, iki yönlü t, SE)."""
    d = d[d[kolon].notna()]
    if len(d) < 30:
        return None
    k = {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}
    s = _sabit(d[kolon].to_numpy(float), k)
    ort, t = s["iki yönlü"]
    return len(d), d["ticker"].nunique(), ort, t, abs(ort / t) if t else float("nan")


def egim(d: pd.DataFrame, y: str, x: str):
    d = d[d[y].notna() & d[x].notna()]
    if len(d) < 30:
        return None
    k = {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}
    s = ols_kumeli(d[y].to_numpy(float), d[x].to_numpy(float), k)
    b, t = s["iki yönlü"]
    return len(d), d["ticker"].nunique(), b, t, abs(b / t) if t else float("nan")


def satir_yaz(ad: str, r, bicim: str) -> None:
    if r is None:
        print(f"  {ad:<30} yetersiz gözlem")
        return
    n, h, m, t, se = r
    if bicim == "log%":
        deger, mde = f"{(math.exp(m) - 1) * 100:+7.1f}%", f"{(math.exp(MDE_KATSAYI * se) - 1) * 100:5.1f}%"
    else:
        deger, mde = f"{m * 100:+7.2f}p", f"{MDE_KATSAYI * se * 100:5.2f}p"
    print(f"  {ad:<30} n={n:>5} pay={h:>4}  {deger}  t={t:+6.2f}{yildiz(t):<3}  MDE {mde}")


def sinavlar(v: pd.DataFrame) -> None:
    for kod, ad, bas_g, son_g in DONEMLER:
        d = donem_olaylari(v, bas_g, son_g)
        bas(f"{kod} · {ad.strip()} ({bas_g} → {son_g}) · {len(d)} olay, {d['ticker'].nunique()} pay")
        hv = d[~d["sermaye_hacim"]]
        print("  H1 · bildirim günü hacmi")
        satir_yaz("AV [t0, t0+2]", ortalama(hv, "av"), "log%")
        satir_yaz("AV, piyasaya göre", ortalama(hv, "av_duz"), "log%")
        print("  H2 · ön hacim [t0−4, t0−1]")
        satir_yaz("havuz", ortalama(hv, "on_hacim"), "log%")
        satir_yaz("önceki 5 günde açıklama yok", ortalama(hv[hv["once_temiz"] == True], "on_hacim"), "log%")  # noqa: E712
        print("  H3 · ortalama tepki")
        cv = d[~d["sermaye_car"]]
        satir_yaz("CAR3", ortalama(cv, "car3"), "p")
        print("  H4 · oynak tahta (CAR3 ~ V90, puan / limit günü)")
        satir_yaz("eğim", egim(cv, "car3", "v90"), "p")
        print("  H5 · olay penceresinde başka açıklama yok (sıkı)")
        satir_yaz("AV", ortalama(hv[hv["olay_temiz"] == True], "av"), "log%")  # noqa: E712
        satir_yaz("CAR3", ortalama(cv[cv["olay_temiz"] == True], "car3"), "p")  # noqa: E712


def yillik(v: pd.DataFrame) -> None:
    bas("KEŞİF · yıla göre (betimleme, hipotez değil)")
    print(f"  {'yıl':<6}{'olay':>6}{'ay başı':>9}{'AV':>9}{'t':>7}{'CAR3':>9}{'t':>7}{'V90 ort':>9}")
    for y, d in v.groupby(v["gun"].map(lambda g: g.year)):
        ay = d["gun"].map(lambda g: (g.year, g.month)).nunique()
        a = ortalama(d[~d["sermaye_hacim"]], "av")
        c = ortalama(d[~d["sermaye_car"]], "car3")
        a_s = f"{(math.exp(a[2]) - 1) * 100:+8.1f}%{a[3]:>7.2f}" if a else f"{'—':>9}{'':>7}"
        c_s = f"{c[2] * 100:+8.2f}p{c[3]:>7.2f}" if c else f"{'—':>9}{'':>7}"
        print(f"  {y:<6}{len(d):>6}{len(d) / ay:>9.1f}{a_s}{c_s}{d['v90'].mean():>9.1f}")


def _z(a, b) -> str:
    if a is None or b is None:
        return "—"
    return f"{(a[2] - b[2]) / math.sqrt(a[4] ** 2 + b[4] ** 2):+.2f}"


def kesif(v: pd.DataFrame) -> None:
    """Ön kayıtta 'keşif' diye işaretlenen, hipotez olmayan kırılımlar."""
    d = {kod: donem_olaylari(v, b, s) for kod, _, b, s in DONEMLER}
    tum = donem_olaylari(v, DONEMLER[0][2], DONEMLER[-1][3])
    hv = lambda x: x[~x["sermaye_hacim"]]  # noqa: E731
    cv = lambda x: x[~x["sermaye_car"]]  # noqa: E731

    bas("KEŞİF 1 · bütün dönemler birlikte (2020-01 → 2026-09)")
    satir_yaz("AV", ortalama(hv(tum), "av"), "log%")
    satir_yaz("AV, piyasaya göre", ortalama(hv(tum), "av_duz"), "log%")
    satir_yaz("ön hacim, önceki 5 gün temiz", ortalama(hv(tum)[hv(tum)["once_temiz"] == True], "on_hacim"), "log%")  # noqa: E712
    satir_yaz("CAR3", ortalama(cv(tum), "car3"), "p")
    satir_yaz("CAR3, olay penceresi temiz", ortalama(cv(tum)[cv(tum)["olay_temiz"] == True], "car3"), "p")  # noqa: E712
    satir_yaz("CAR3 ~ V90", egim(cv(tum), "car3", "v90"), "p")

    bas("KEŞİF 2 · dönem farkları, z = (a − b) / √(se_a² + se_b²)")
    for ad, kol, suz, fn in (("AV", "av", hv, ortalama), ("CAR3", "car3", cv, ortalama),
                             ("CAR3 ~ V90", "car3", cv, None)):
        r = {k: (egim(suz(x), "car3", "v90") if fn is None else fn(suz(x), kol)) for k, x in d.items()}
        print(f"  {ad:<12} C−A {_z(r['C'], r['A'])}   C−B {_z(r['C'], r['B'])}   "
              f"A−B {_z(r['A'], r['B'])}   A2−A1 {_z(r['A2'], r['A1'])}")

    bas("KEŞİF 3 · oynak tahta: V90 dağılımı ve bir standart sapmalık etki")
    print(f"  {'dönem':<6}{'V90 ort':>9}{'medyan':>8}{'SS':>7}{'eğim·SS':>10}{'t':>7}  V90≥8 CAR3 / V90≤1 CAR3")
    for k, x in d.items():
        x = cv(x)
        e = egim(x, "car3", "v90")
        ss = x["v90"].std()
        yuk = ortalama(x[x["v90"] >= 8], "car3")
        dus = ortalama(x[x["v90"] <= 1], "car3")
        f = lambda r: f"{r[2] * 100:+.2f}p (n {r[0]})" if r else "—"  # noqa: E731
        print(f"  {k:<6}{x['v90'].mean():>9.1f}{x['v90'].median():>8.0f}{ss:>7.1f}"
              f"{(e[2] * ss * 100 if e else float('nan')):>+9.2f}p{(e[3] if e else float('nan')):>7.2f}  {f(yuk)} / {f(dus)}")

    bas("KEŞİF 4 · olay penceresindeki açıklamanın türü (CAR3)")
    diger = [k for k in KATEGORILER if k != "başka yeni iş"]
    for k, x in d.items():
        x = cv(x).copy()
        x["baska_is"] = x["kat_başka yeni iş"] > 0
        x["diger_tur"] = x[[f"kat_{c}" for c in diger]].sum(axis=1) > 0
        sat = []
        for ad, m in (("hiç yok", ~x["baska_is"] & ~x["diger_tur"]),
                      ("yalnız başka yeni iş", x["baska_is"] & ~x["diger_tur"]),
                      ("diğer tür var", x["diger_tur"])):
            r = ortalama(x[m & x["kat_var"]], "car3")
            sat.append(f"{ad} {r[2] * 100:+.2f}p t {r[3]:+.1f} n {r[0]}" if r else f"{ad} —")
        print(f"  {k:<4} " + " | ".join(sat))

    bas("KEŞİF 5 · aynı şirketler: üç dönemin üçünde de olayı olan paylar")
    ortak = set.intersection(*(set(d[k]["ticker"]) for k in ("A", "B", "C")))
    print(f"  {len(ortak)} pay")
    for k in ("A", "B", "C"):
        x = d[k][d[k]["ticker"].isin(ortak)]
        a, c = ortalama(hv(x), "av"), ortalama(cv(x), "car3")
        print(f"  {k}  AV {(math.exp(a[2]) - 1) * 100:+.1f}% t {a[3]:+.2f} (n {a[0]})   "
              f"CAR3 {c[2] * 100:+.2f}p t {c[3]:+.2f} (n {c[0]})")


def spekulasyon(v: pd.DataFrame, p: pd.DataFrame) -> None:
    """Ay düzeyinde piyasa çapı spekülasyon ölçüsü ve olay etkisi.

    Ölçü: o ay işlem gören pay-günlerinin kaçta kaçı %9 ≤ |r| ≤ marj
    (limite yakın gün). Bütün dönemlerde aynı vekil; devre kesici ve VBTS
    kayıtları 2020 için doğrulanmadığından kullanılmıyor. Tercil sınırları
    2020-01 → 2026-09 ayları üzerinden.
    """
    t = p[p["r"].notna() & (p["r"].abs() <= p["marj"])].copy()
    t["ay"] = pd.to_datetime(t["tarih"]).dt.to_period("M")
    ay = t.groupby("ay").apply(lambda d: (d["r"].abs() >= LIMIT_ALT).mean(), include_groups=False)
    sinir = ay.quantile([1 / 3, 2 / 3]).to_numpy()
    sinif = pd.cut(ay, [-1, sinir[0], sinir[1], 2], labels=["sakin", "orta", "spekülatif"])
    bas("KEŞİF 6 · piyasa çapında spekülasyon (ay tercili, 2020-01 → 2026-09)")
    print(f"  limite yakın pay-günü payı: tercil sınırları %{sinir[0] * 100:.2f} / %{sinir[1] * 100:.2f}")
    for s in ("sakin", "orta", "spekülatif"):
        aylar = sorted(str(a) for a in sinif[sinif == s].index)
        yillar = pd.Series([a[:4] for a in aylar]).value_counts().sort_index().to_dict()
        print(f"  {s:<11} {len(aylar)} ay, yıllara göre {yillar}")
    x = v.copy()
    x["ay"] = pd.to_datetime(x["t0"]).dt.to_period("M")
    x["sinif"] = x["ay"].map(sinif)
    x["ay_oran"] = x["ay"].map(ay)
    for s in ("sakin", "orta", "spekülatif"):
        g = x[x["sinif"] == s]
        satir_yaz(f"{s}: AV", ortalama(g[~g["sermaye_hacim"]], "av"), "log%")
        satir_yaz(f"{s}: AV, piyasaya göre", ortalama(g[~g["sermaye_hacim"]], "av_duz"), "log%")
        satir_yaz(f"{s}: CAR3", ortalama(g[~g["sermaye_car"]], "car3"), "p")
    hv = x[~x["sermaye_hacim"]]
    cv = x[~x["sermaye_car"]]
    print("  sürekli: olay ayının limit günü payı (yüzde puan başına)")
    e = egim(hv.assign(o=hv["ay_oran"] * 100), "av", "o")
    print(f"    AV    eğim {e[2]:+.3f} log / puan  t={e[3]:+.2f}{yildiz(e[3])}  n={e[0]}")
    e = egim(cv.assign(o=cv["ay_oran"] * 100), "car3", "o")
    print(f"    CAR3  eğim {e[2] * 100:+.3f}p / puan  t={e[3]:+.2f}{yildiz(e[3])}  n={e[0]}")


def fon_kirilimi(v: pd.DataFrame) -> None:
    """C'de fon pompası tezi: bulgular fonların yoğun tuttuğu niş paylardan mı geliyor?

    Hüseyin'in "spekülasyon"u piyasa havası değil, belirli düşük dolaşımlı
    payların sonradan tasfiye edilen fonlarca
    yükseltilmesi. Sınıf 27.09 notuyla aynı: tasfiye fonlarının Ağustos 2026
    pozisyonu / payın günlük işlem hacmi (analiz_piyasa_rejimi). Portföy
    olaydan SONRA ölçülüyor: sınıf betimleyici, nedensel değil. 2020–24 için
    fon portföyü yok; bu kırılım yalnız C'de.
    """
    import psycopg

    from kap_radar.ayarlar import dsn_bul
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        fon = pd.read_sql("select ticker, tasfiye_tl::float as tasfiye_tl, "
                          "gunluk_hacim_tl::float as hacim_tl from hisse_fon_guncel", b)
    fon["gun"] = fon["tasfiye_tl"] / fon["hacim_tl"]
    c = donem_olaylari(v, DONEMLER[-1][2], DONEMLER[-1][3]).copy()
    gun = c["ticker"].map(fon.set_index("ticker")["gun"]).fillna(0)
    c["fon"] = np.select([gun == 0, gun < 0.5], ["tutmuyor", "< 0,5 gün"], default="yoğun ≥ 0,5 gün")
    bas("KEŞİF 7 · C'de fon yoğunluğu (Hüseyin'in fon pompası tezi)")
    yogun = c[c["fon"] == "yoğun ≥ 0,5 gün"]
    print("  yoğun gruptaki paylar (olay sayısı):",
          ", ".join(f"{t} {n}" for t, n in yogun["ticker"].value_counts().items()))
    hv = lambda x: x[~x["sermaye_hacim"]]  # noqa: E731
    cv = lambda x: x[~x["sermaye_car"]]  # noqa: E731
    for ad, x in (("tutmuyor", c[c["fon"] == "tutmuyor"]), ("< 0,5 gün", c[c["fon"] == "< 0,5 gün"]),
                  ("yoğun ≥ 0,5 gün", yogun), ("C, yoğun grup hariç", c[c["fon"] != "yoğun ≥ 0,5 gün"])):
        print(f"  {ad}")
        satir_yaz("  AV", ortalama(hv(x), "av"), "log%")
        satir_yaz("  CAR3", ortalama(cv(x), "car3"), "p")
        satir_yaz("  CAR3 ~ V90", egim(cv(x), "car3", "v90"), "p")
        satir_yaz("  CAR3, V90 ≥ 8", ortalama(cv(x)[cv(x)["v90"] >= 8], "car3"), "p")


def kaynak_karsilastir(v: pd.DataFrame) -> None:
    """C döneminde bülten hattı ile veritabanındaki yfinance hattı aynı şeyi mi ölçüyor?"""
    import psycopg

    from kap_radar.ayarlar import dsn_bul
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        db = pd.read_sql("select b.kap_index, tp.t0 as t0_db, tp.car_3g::float as car3_db "
                         "from bildirim b join tepki tp on tp.kap_id = b.kap_id", b)
    bas("KAYNAK · C döneminde bülten ve yfinance hattı")
    m = v.merge(db, on="kap_index", how="inner")
    print(f"  eşleşen olay {len(m)}; t0 aynı: %{(m['t0'] == m['t0_db']).mean() * 100:.1f}")
    mm = m[m["car3"].notna() & m["car3_db"].notna()]
    r = float(np.corrcoef(mm["car3"], mm["car3_db"])[0, 1])
    print(f"  CAR3 ikisi de var: {len(mm)}  korelasyon {r:.3f}  ortalama bülten {mm['car3'].mean() * 100:+.2f}p"
          f"  DB {mm['car3_db'].mean() * 100:+.2f}p  fark medyanı {(mm['car3'] - mm['car3_db']).median() * 100:+.2f}p")


# ------------------------------------------------------------------- ana

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kaynak", action="store_true", help="C'de veritabanıyla karşılaştır")
    args = ap.parse_args()

    p = panel_yukle()
    takvim = sorted(p["tarih"].unique())
    marjlar = {g: marj(g) for g in takvim}
    liste = liste_tablosu()
    getiri, ham_getiri, adet, piyasa = seriler(p)
    olay = olaylar_kur(liste, takvim, set(adet))
    print(f"panel {len(p):,} pay-günü, {len(takvim)} işlem günü; olay {len(olay)}")

    prof = olay_profili(olay, adet, takvim, PROFIL_GUNLERI)
    m = piyasa_hacim_endeksi(p.rename(columns={"adet": "v"})[["ticker", "tarih", "v"]])
    pprof = piyasa_profili(olay, m, takvim, PROFIL_GUNLERI)
    v = olay.join(prof).join(pprof[["av"]].rename(columns={"av": "piyasa_av"}))
    v["av_duz"] = v["av"] - v["piyasa_av"]
    v["on_hacim"] = v[list(ON_HACIM_GUNLERI)].mean(axis=1, skipna=False)
    v["sermaye_hacim"] = marj_asan(olay, ham_getiri, marjlar, takvim, -TAHMIN_BAS, OLAY_PENCERE - 1)
    v["sermaye_car"] = marj_asan(olay, ham_getiri, marjlar, takvim, 0, OLAY_PENCERE - 1)
    v["v90"] = v90(olay, getiri, marjlar, takvim)
    v = v.join(car3(olay, getiri, piyasa, takvim))

    kar = karisan(olay, liste, takvim)
    once = [c for c in kar.columns if c.startswith("once ")]
    olayda = list(KATEGORILER)
    v["once_temiz"] = (kar[once].sum(axis=1) == 0).reindex(v.index)
    v["olay_temiz"] = (kar[olayda].sum(axis=1) == 0).reindex(v.index)
    for c in olayda:
        v[f"kat_{c}"] = kar[c].reindex(v.index)
    v["kat_var"] = v.index.isin(kar.index)

    v.drop(columns=["zaman"]).to_csv(CIKTI, index=False)
    print(f"olay ölçüleri: {CIKTI.relative_to(KOK)}")
    print(f"hacim sınavından sermaye işlemiyle çıkan {int(v['sermaye_hacim'].sum())}, "
          f"CAR'dan çıkan {int(v['sermaye_car'].sum())}; beta çapadan {int((v.get('beta_kaynak') == 'capa').sum())}")

    sinavlar(v)
    yillik(v)
    kesif(v)
    spekulasyon(v, p)
    if args.kaynak:
        kaynak_karsilastir(v)
        fon_kirilimi(v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
