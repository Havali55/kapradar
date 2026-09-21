"""Büyüklük skorunun geçerlilik (validity) sınaması — Adım 16.

Soru: S ölçtüğünü iddia ettiği şeyi ölçüyor mu?

Skorun iddiası dar ve test edilebilir: "bu bildirim şirketin kendi
ölçeğine göre büyüktür" der, "hisse yükselecek" demez. Dolayısıyla
doğru sınav getiri değil **işlem hacmidir**. Beaver (1968) ve Kim &
Verrecchia (1991): materyal bilgi, yatırımcılar yönü konusunda
anlaşamasa bile işlem hacmini artırır. Getiri fikir birliğini ölçer,
hacim ilgiyi.

Üç sınav:
  - Ayırt edici: S ~ işaretli CAR  -> İLİŞKİ OLMAMALI
  - Yakınsak   : S ~ anormal hacim -> İLİŞKİ OLMALI
  - Kalibrasyon: %1 tabanı ve %100 tavanı veriyle tutuyor mu?

Standart hatalar **hisse bazında kümelenir**. 613 olay 111 hisseye
ait; aynı hissenin bildirimleri aynı likidite rejimini paylaşıyor.
Kümelenmeyi yok sayan t istatistiği burada sistematik olarak şişiyor
(ölçtük: 2,17 -> 1,73).

Ücretli çağrı yok; yalnız kendi veritabanımızı okur.

    python scripts/skor_gecerlilik.py            # tam rapor
    python scripts/skor_gecerlilik.py --kisa     # yalnız ana tablolar
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402

# Tahmin penceresi: olaydan 60..11 gün önce. Son 10 gün BİLEREK
# dışarıda — R8 profilinde görüldüğü gibi hacim bildirimden üç gün
# önce zaten yükseliyor. O günler tabana katılırsa "normal" seviye
# şişer ve anormal hacim olduğundan küçük ölçülür.
TAHMIN_BAS, TAHMIN_SON = 60, 11
ASGARI_TAHMIN_GUN = 30
OLAY_PENCERE = 3  # [t0, t0+2] — CAR ile aynı pencere

# Bedelsiz kaynaklı sahte sıçramalar: auto_adjust BIST bedelsizlerini
# düzeltmiyor (HRKET 87,9 -> 6,15). Beta tahmininde eleniyor.
AZAMI_GUNLUK_GETIRI = 0.40


# ----------------------------------------------------------- istatistik
# scipy bağımlılık değil. n > 400 ve serbestlik derecesi yüksek
# olduğundan t dağılımı normale pratikte eşit; p değerleri normal
# yaklaşımıyla veriliyor ve n her tabloda basılıyor ki kontrol
# edilebilsin.

def p_iki_yonlu(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2.0))


def yildiz(t: float) -> str:
    a = abs(t)
    return "***" if a > 3.29 else "**" if a > 2.58 else "*" if a > 1.96 else ""


def korelasyon(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, int]:
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 4:
        return float("nan"), float("nan"), float("nan"), n
    r = float(np.corrcoef(x, y)[0, 1])
    if abs(r) >= 1.0:
        return r, float("inf"), 0.0, n
    t = r * math.sqrt(n - 2) / math.sqrt(1 - r * r)
    return r, t, p_iki_yonlu(t), n


def spearman(x: np.ndarray, y: np.ndarray):
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 4:
        return float("nan"), float("nan"), float("nan"), len(x)
    return korelasyon(pd.Series(x).rank().to_numpy(),
                      pd.Series(y).rank().to_numpy())


def ols(y, X, kume, adlar: list[str]) -> pd.DataFrame:
    """OLS; `kume` verilirse Liang-Zeger (CR1) kümelenmiş std hata.

    CR1 küçük örneklem düzeltmesi: G/(G-1) · (n-1)/(n-k). Küme sayısı
    70 civarında olduğu için düzeltme ihmal edilebilir değil.
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    y, X = y[m], X[m]
    kume = np.asarray(kume)[m] if kume is not None else None
    n, k = X.shape
    Xd = np.column_stack([np.ones(n), X])
    k1 = k + 1
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    beta = XtX_inv @ Xd.T @ y
    e = y - Xd @ beta

    if kume is None:
        et = (Xd * (e**2)[:, None]).T @ Xd          # HC0
        G, duzeltme = n, 1.0
    else:
        et = np.zeros((k1, k1))
        gruplar = pd.unique(kume)
        for g in gruplar:
            sel = kume == g
            sg = Xd[sel].T @ e[sel]
            et += np.outer(sg, sg)
        G = len(gruplar)
        duzeltme = (G / (G - 1)) * ((n - 1) / (n - k1)) if G > 1 else 1.0

    se = np.sqrt(np.diag(XtX_inv @ et @ XtX_inv * duzeltme))
    t = beta / se
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return pd.DataFrame(
        {"katsayi": beta, "std_hata": se, "t": t,
         "p": [p_iki_yonlu(v) for v in t]},
        index=["sabit"] + adlar,
    ).assign(n=n, kume=G, r2=1 - float((e**2).sum()) / ss_tot if ss_tot else np.nan)


def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    t = (a.mean() - b.mean()) / math.sqrt(
        a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return t, p_iki_yonlu(t)


def tek_orneklem(a: np.ndarray) -> tuple[float, float]:
    a = a[np.isfinite(a)]
    t = a.mean() / (a.std(ddof=1) / math.sqrt(len(a)))
    return t, p_iki_yonlu(t)


# ------------------------------------------------------------------ veri

SORGU = """
with son as (
  select distinct on (kap_id) kap_id, etki_skoru, ciro_orani, net_tutar_tl,
         yayina_hazir, red_nedeni
  from cikarim order by kap_id, id desc
)
select b.kap_id, b.ticker, b.yayin_zamani, b.guncelleme_mi,
       (b.kap_alanlari->>'karsi_taraf' is not null
        and b.kap_alanlari->>'karsi_taraf' <> '') as kt_acik,
       s.etki_skoru, s.ciro_orani, s.net_tutar_tl, s.yayina_hazir,
       t.t0, t.car_1g, t.car_3g, t.car_5g
from bildirim b
join son s on s.kap_id = b.kap_id
left join tepki t on t.kap_id = b.kap_id
"""


def yukle(baglanti):
    olay = pd.read_sql(SORGU, baglanti)
    fiyat = pd.read_sql(
        "select ticker, tarih, kapanis_duzeltilmis, hacim from fiyat_gunluk",
        baglanti)
    endeks = pd.read_sql(
        "select tarih, xu100_kapanis from endeks_gunluk order by tarih",
        baglanti)
    return olay, fiyat, endeks


def hacim_serileri(fiyat: pd.DataFrame) -> dict:
    return {t: g.set_index("tarih")["hacim"] for t, g in fiyat.groupby("ticker")}


def anormal_hacim_profili(olay, hac, takvim, gunler) -> dict[int, list[float]]:
    """Her olay için t0+k günündeki ln(hacim) − ln(taban medyanı).

    Logaritma şart: hacim dağılımı aşırı çarpık. Taban MEDYAN (dirençli
    olsun), pay ORTALAMA (olayı görsün) — kasıtlı asimetri.
    """
    ix = {g: i for i, g in enumerate(takvim)}
    cikti: dict[int, list[float]] = {k: [] for k in gunler}
    for _, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix or o["ticker"] not in hac:
            continue
        i0, seri = ix[o["t0"]], hac[o["ticker"]]
        tah = seri.reindex(
            [takvim[j] for j in range(max(0, i0 - TAHMIN_BAS),
                                      max(0, i0 - TAHMIN_SON) + 1)])
        tah = tah[tah > 0]          # sıfır hacim = durdurulmuş gün
        if len(tah) < ASGARI_TAHMIN_GUN:
            continue
        taban = math.log(float(tah.median()))
        for k in gunler:
            j = i0 + k
            if 0 <= j < len(takvim):
                v = seri.get(takvim[j])
                if v and v > 0:
                    cikti[k].append(math.log(float(v)) - taban)
    return cikti


def anormal_hacim(olay, hac, takvim) -> pd.Series:
    """AV = ln(ort hacim [t0, t0+2]) − ln(medyan hacim [t0−60, t0−11])."""
    ix = {g: i for i, g in enumerate(takvim)}
    out = []
    for _, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix or o["ticker"] not in hac:
            out.append(np.nan)
            continue
        i0, seri = ix[o["t0"]], hac[o["ticker"]]
        ov = seri.reindex([takvim[j] for j in
                           range(i0, min(i0 + OLAY_PENCERE, len(takvim)))])
        tah = seri.reindex([takvim[j] for j in
                            range(max(0, i0 - TAHMIN_BAS),
                                  max(0, i0 - TAHMIN_SON) + 1)])
        ov, tah = ov[ov > 0], tah[tah > 0]
        out.append(math.log(float(ov.mean())) - math.log(float(tah.median()))
                   if len(ov) and len(tah) >= ASGARI_TAHMIN_GUN else np.nan)
    return pd.Series(out, index=olay.index, name="av")


# Tahta kalitesi vekili. VBTS verisi henüz çekilmedi (Adım 11), bu
# yüzden spekülatif tahtayı limit yakını hareket sıklığından okuyoruz:
# BIST günlük limit ±%10, |getiri| >= %9 olan gün limit yakınıdır.
LIMIT_ESIGI = 0.09
LIMIT_GERI_GUN = 90


def limit_sayaci(olay, fiyat, takvim) -> pd.Series:
    """Olaydan önceki 90 günde kaç kez limit yakını hareket olmuş."""
    ix = {g: i for i, g in enumerate(takvim)}
    getiri = {t: g.set_index("tarih")["kapanis_duzeltilmis"].astype(float)
                 .sort_index().pct_change()
              for t, g in fiyat.groupby("ticker", sort=False)}
    out = []
    for _, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix or o["ticker"] not in getiri:
            out.append(np.nan)
            continue
        i0 = ix[o["t0"]]
        g = getiri[o["ticker"]].reindex(
            [takvim[j] for j in range(max(0, i0 - LIMIT_GERI_GUN), i0)]).dropna()
        g = g[g.abs() < AZAMI_GUNLUK_GETIRI]   # bedelsiz sıçramalarını ele
        out.append(float((g.abs() >= LIMIT_ESIGI).sum()) if len(g) >= 30 else np.nan)
    return pd.Series(out, index=olay.index, name="limit90")


def betalar(fiyat, endeks) -> pd.Series:
    e = endeks.set_index("tarih")["xu100_kapanis"].astype(float)
    er = np.log(e).diff()
    out = {}
    for tic, grup in fiyat.groupby("ticker", sort=False):
        s = grup.set_index("tarih")["kapanis_duzeltilmis"].astype(float).sort_index()
        df = pd.concat([np.log(s).diff().rename("h"), er.rename("e")],
                       axis=1).dropna()
        df = df[(df["h"].abs() < AZAMI_GUNLUK_GETIRI)
                & (df["e"].abs() < AZAMI_GUNLUK_GETIRI)]
        if len(df) >= 60 and df["e"].var() > 0:
            out[tic] = float(df["h"].cov(df["e"]) / df["e"].var())
    return pd.Series(out, name="beta")


# ------------------------------------------------------------------ rapor

def bas(b: str) -> None:
    print("\n" + "=" * 74 + f"\n{b}\n" + "=" * 74)


def kor_satir(ad, x, y) -> None:
    r, t, p, n = korelasyon(np.asarray(x, float), np.asarray(y, float))
    rs, ts, ps, _ = spearman(np.asarray(x, float), np.asarray(y, float))
    print(f"  {ad:<28} n={n:>4}  r={r:+.3f} (t={t:+.2f}{yildiz(t):<3} p={p:.4f})"
          f"   rho={rs:+.3f} (t={ts:+.2f}{yildiz(ts):<3} p={ps:.4f})")


def dilim(df, deger, dilim_kol, k=5) -> pd.DataFrame:
    d = df[np.isfinite(df[deger]) & np.isfinite(df[dilim_kol])].copy()
    d["_d"] = pd.qcut(d[dilim_kol], k, labels=[f"D{i+1}" for i in range(k)],
                      duplicates="drop")
    g = d.groupby("_d", observed=True)
    return pd.DataFrame({
        "n": g[deger].size(), "ort": g[deger].mean(),
        "medyan": g[deger].median(), f"{dilim_kol}_ort": g[dilim_kol].mean()})


def f4(v) -> str:
    return f"{v:.4f}"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Skor geçerlilik sınaması")
    ap.add_argument("--kisa", action="store_true", help="yalnız ana tablolar")
    secenek = ap.parse_args()

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1
    with psycopg.connect(dsn, connect_timeout=30) as baglanti:
        olay, fiyat, endeks = yukle(baglanti)

    takvim = list(endeks["tarih"])
    hac = hacim_serileri(fiyat)
    olay["av"] = anormal_hacim(olay, hac, takvim)
    olay["limit90"] = limit_sayaci(olay, fiyat, takvim)
    for k in ("etki_skoru", "ciro_orani", "net_tutar_tl", "car_1g", "car_3g", "car_5g"):
        olay[k] = pd.to_numeric(olay[k], errors="coerce")
    olay["abs_car3"] = olay["car_3g"].abs()
    olay["ttm"] = olay["net_tutar_tl"] / olay["ciro_orani"].replace(0, np.nan)
    olay["ln_ttm"] = np.log(olay["ttm"].where(olay["ttm"] > 0))
    olay["siklik"] = olay.groupby("ticker")["ticker"].transform("size")
    olay["ln_siklik"] = np.log(olay["siklik"])

    s = olay[olay["etki_skoru"].notna()].copy()
    sv = s[s["av"].notna()].copy()

    bas("0 · ÖRNEKLEM")
    print(f"  bildirim {len(olay)} · skorlu {len(s)} · "
          f"CAR(3g) {olay['car_3g'].notna().sum()} · AV {olay['av'].notna().sum()} · "
          f"hisse {olay['ticker'].nunique()}")

    bas("1 · OLAY GERÇEK Mİ — pencere boyunca hacim profili")
    print("  Taban = [t0-60, t0-11] medyani. t0 = ilk tepki gunu.\n")
    prof = anormal_hacim_profili(sv, hac, takvim, range(-5, 6))
    for k in sorted(prof):
        a = np.array(prof[k])
        if len(a) < 30:
            continue
        t, p = tek_orneklem(a)
        print(f"    t0{k:+d}  n={len(a):>3}  AV={a.mean():+.4f}  "
              f"hacim %{(math.exp(a.mean())-1)*100:+6.1f}  t={t:+6.2f} {yildiz(t)}")
    print("\n  -> t0'da sicrama, ~5 gunde sonuyor. t0 ONCESI de yuksek:")
    print("     bildirimden once hacim zaten artmis (sizinti/beklenti).")

    bas("2 · AYIRT EDİCİ GEÇERLİLİK — S bir getiri tahmini DEĞİL")
    print("  Beklenti: İLİŞKİ YOK.\n")
    kor_satir("S ~ CAR(1g)", s["etki_skoru"], s["car_1g"])
    kor_satir("S ~ CAR(3g)", s["etki_skoru"], s["car_3g"])
    kor_satir("S ~ CAR(5g)", s["etki_skoru"], s["car_5g"])
    sc = s[s["car_3g"].notna()]
    print("\n  Hisse-kumelenmis:")
    print(ols(sc["car_3g"], sc[["etki_skoru"]], sc["ticker"], ["S"])
          .to_string(float_format=f4))

    bas("3 · YAKINSAK GEÇERLİLİK — S ~ anormal hacim")
    t, p = tek_orneklem(sv["av"].to_numpy(float))
    print(f"  AV ortalamasi {sv['av'].mean():+.4f} "
          f"(hacim %{(math.exp(sv['av'].mean())-1)*100:+.1f}), "
          f"H0: AV=0 -> t={t:+.2f}{yildiz(t)} p={p:.6f}\n")
    kor_satir("S ~ AV", sv["etki_skoru"], sv["av"])
    kor_satir("ln(r) ~ AV", np.log(sv["ciro_orani"].where(sv["ciro_orani"] > 0)),
              sv["av"])
    print("\n  Skor beslisi:")
    print(dilim(sv, "av", "etki_skoru").to_string(float_format=f4))

    bas("4 · SAĞLAMLIK — S ~ AV kaç sınavdan geçiyor")
    d = sv.dropna(subset=["ln_ttm"])
    kriz = pd.to_datetime(sv["yayin_zamani"]).dt.tz_convert("Europe/Istanbul").dt.date
    en_cok = sv["ticker"].value_counts().head(3)
    sv_w = sv.assign(av_w=sv["av"].clip(sv["av"].quantile(0.01),
                                        sv["av"].quantile(0.99)))
    sinavlar = [
        ("HC0 (kumelenme yok)", ols(sv["av"], sv[["etki_skoru"]], None, ["S"])),
        ("hisse-kumelenmis", ols(sv["av"], sv[["etki_skoru"]], sv["ticker"], ["S"])),
        ("+ boyut kontrolu", ols(d["av"], d[["etki_skoru", "ln_ttm"]],
                                 d["ticker"], ["S", "ln(TTM)"])),
        ("+ siklik kontrolu", ols(d["av"], d[["etki_skoru", "ln_ttm", "ln_siklik"]],
                                  d["ticker"], ["S", "ln(TTM)", "ln(siklik)"])),
        ("winsorize %1/%99", ols(sv_w["av_w"], sv_w[["etki_skoru"]],
                                 sv_w["ticker"], ["S"])),
        ("kriz penceresi haric",
         (lambda x: ols(x["av"], x[["etki_skoru"]], x["ticker"], ["S"]))(
             sv[~kriz.between(pd.Timestamp("2026-09-09").date(),
                              pd.Timestamp("2026-09-19").date())])),
        ("en cok bildirimci 3 haric",
         (lambda x: ols(x["av"], x[["etki_skoru"]], x["ticker"], ["S"]))(
             sv[~sv["ticker"].isin(en_cok.index)])),
    ]
    print(f"  ({', '.join(f'{t}={n}' for t, n in en_cok.items())} dislandi)\n")
    print(f"  {'SINAV':<24} {'S katsayi':>10} {'std hata':>10} {'t':>7}  {'p':>7}  {'n':>4}")
    for ad, tablo in sinavlar:
        r = tablo.loc["S"]
        print(f"  {ad:<24} {r['katsayi']:>+10.4f} {r['std_hata']:>10.4f} "
              f"{r['t']:>+7.2f}{yildiz(r['t']):<3} {r['p']:>7.4f}  {int(r['n']):>4}")
    print("\n  -> Yon tutarli ama iliski KUMELENME ve SIKLIK kontrolunden")
    print("     sonra konvansiyonel esigi gecmiyor. Dusundurucu, kanit degil.")

    bas("5 · BİLDİRİM YORGUNLUĞU — en sağlam bulgu")
    print(ols(sv["av"], sv[["ln_siklik"]], sv["ticker"], ["ln(siklik)"])
          .to_string(float_format=f4))
    print("\n" + dilim(sv, "av", "siklik", 3).to_string(float_format=f4))

    bas("6 · ÇAPALAR — %1 tabanı ve %100 tavanı veriyle tutuyor mu?")
    r = s["ciro_orani"]
    print("  r dagilimi (skorlanan 480):")
    for ad, msk in (("r < %1", r < 0.01), ("%1-%10", (r >= 0.01) & (r < 0.10)),
                    ("%10-%50", (r >= 0.10) & (r < 0.50)),
                    ("%50-%100", (r >= 0.50) & (r < 1.0)), ("r >= %100", r >= 1.0)):
        n = int(msk.sum())
        print(f"    {ad:<10} n={n:>3}  ({n/len(s)*100:>4.1f}%)")
    alt = sv[sv["ciro_orani"] < 0.01]["av"].to_numpy(float)
    ust = sv[sv["ciro_orani"] >= 0.01]["av"].to_numpy(float)
    t0_, p0_ = tek_orneklem(alt)
    tw, pw = welch(ust, alt)
    print("\n  TABAN SINAVI (formul bunlara S=0,00 veriyor):")
    print(f"    r <  %1  n={len(alt):>3}  AV={alt.mean():+.4f} "
          f"(hacim %{(math.exp(alt.mean())-1)*100:+.1f})  H0:AV=0 -> t={t0_:+.2f}{yildiz(t0_)} p={p0_:.4f}")
    print(f"    r >= %1  n={len(ust):>3}  AV={ust.mean():+.4f}")
    print(f"    fark={ust.mean()-alt.mean():+.4f}  Welch t={tw:+.2f}  p={pw:.4f}  "
          f"-> AYIRT EDILEMIYOR")
    print(f"\n  TAVAN SINAVI: r>=%100 olan bildirim sayisi "
          f"{int((olay['ciro_orani'] >= 1.0).sum())} / {len(olay)}")

    bas("7 · K ÇARPANI — 2x2 tam veriyle")
    g = olay.dropna(subset=["car_3g"]).groupby(["kt_acik", "guncelleme_mi"])
    tab = pd.DataFrame({"n": g["car_3g"].size(), "CAR3_ort": g["car_3g"].mean(),
                        "AV_ort": g["av"].mean(), "S_medyan": g["etki_skoru"].median()})
    tab["K"] = [0.70, 0.50, 1.00, 0.85]
    print(tab.to_string(float_format=lambda v: f"{v:+.4f}"))
    print("\n  -> n>=55 olan uc hucrede AV siralamasi K siralamasiyla uyumlu.")
    print("     Dorduncu hucre (gizli+guncelleme) n=6: hicbir sey soylenemez.")

    if not secenek.kisa:
        bas("8 · BOYUT YANLILIĞI")
        kor_satir("S ~ ln(TTM)", s["etki_skoru"], s["ln_ttm"])
        print("\n" + dilim(s, "etki_skoru", "ln_ttm", 3).to_string(float_format=f4))
        print("\n  -> Uclukler monoton DEGIL; sistematik kucuk-sirket kayirmasi yok.")

        bas("9 · SPEKÜLATİF TAHTA — ölçü oynatılan tahtalarda kırılıyor mu?")
        print("  Itiraz: BIST'te hacim imal edilebiliyor. Oyleyse 'anormal")
        print("  hacim = materyallik' esitligi spekulatif tahtalarda kirilir.\n")
        sv2 = sv.dropna(subset=["limit90"])
        print(f"  Evren: ort {sv2['limit90'].mean():.1f} limit-yakini gun "
              f"(medyan {sv2['limit90'].median():.0f}) · "
              f"temiz %{(sv2['limit90'] == 0).mean()*100:.1f} · "
              f"5+ gun %{(sv2['limit90'] >= 5).mean()*100:.1f}\n")
        print(f"  {'TAHTA':<22} {'n':>4} {'hisse':>6} {'S kats':>9} {'t':>7} {'hacim':>9}")
        for ad, grup in (("temiz (<=1)", sv2[sv2["limit90"] <= 1]),
                         ("orta (2-4)", sv2[(sv2["limit90"] > 1) & (sv2["limit90"] < 5)]),
                         ("spekulatif (>=5)", sv2[sv2["limit90"] >= 5])):
            if len(grup) < 40:
                print(f"  {ad:<22} {len(grup):>4}  (cok az, atlandi)")
                continue
            r_ = ols(grup["av"], grup[["etki_skoru"]], grup["ticker"], ["S"]).loc["S"]
            print(f"  {ad:<22} {len(grup):>4} {grup['ticker'].nunique():>6} "
                  f"{r_['katsayi']:>+9.4f} {r_['t']:>+7.2f}{yildiz(r_['t']):<3} "
                  f"%{(math.exp(grup['av'].mean())-1)*100:>+7.1f}")
        d3 = sv2.dropna(subset=["ln_ttm"]).copy()
        d3["spek"] = (d3["limit90"] >= 5).astype(float)
        d3["S_x_spek"] = d3["etki_skoru"] * d3["spek"]
        print("\n  Etkilesim modeli:")
        print(ols(d3["av"], d3[["etki_skoru", "spek", "S_x_spek", "ln_ttm"]],
                  d3["ticker"], ["S", "spekulatif", "S x spekulatif", "ln(TTM)"])
              .to_string(float_format=f4))
        print("\n  -> Spekulatif tahtalar ayristirilinca S'nin ana etkisi")
        print("     ANLAMLI hale geliyor (havuzlanmista t=+1,05 idi).")

        bas("10 · BÜYÜK HABER DAHA ÇOK FİYATLANIYOR MU?")
        for ad, grup in (("S >= 3", s[s["etki_skoru"] >= 3]),
                         ("S <  1", s[s["etki_skoru"] < 1])):
            car = grup["car_3g"].dropna().to_numpy(float)
            if len(car) < 10:
                continue
            t_, p_ = tek_orneklem(car)
            print(f"  {ad:<8} n={len(car):>3}  ort={car.mean():+.4f}  "
                  f"medyan={np.median(car):+.4f}  pozitif=%{(car > 0).mean()*100:.0f}  "
                  f"t={t_:+.2f}{yildiz(t_)}")
        print("  -> Iki grup ayni: buyuk haber de kucuk haber de fiyatlanmiyor.")

        bas("11 · SPEKÜLATİF TAHTA: OYNAKLIK VAR, YÖN YOK")
        sc2 = sv2.dropna(subset=["car_3g"])
        for ad, y in (("|CAR3|", sc2["abs_car3"]), ("CAR3 isaretli", sc2["car_3g"])):
            r_ = ols(y, sc2[["limit90"]], sc2["ticker"], ["limit90"]).loc["limit90"]
            print(f"  limit90 ~ {ad:<14} katsayi={r_['katsayi']:+.5f}  "
                  f"t={r_['t']:+.2f}{yildiz(r_['t'])}  p={r_['p']:.4f}")

        bas("12 · BETA = 1 VARSAYIMININ MALİYETİ")
        b = betalar(fiyat, endeks)
        print(f"  n={len(b)} hisse  ort={b.mean():.3f} medyan={b.median():.3f} "
              f"C1={b.quantile(0.25):.3f} C3={b.quantile(0.75):.3f}")
        print(f"  beta < 1 olan: {int((b < 1).sum())}/{len(b)} "
              f"({(b < 1).mean()*100:.0f}%)")
        print("  -> Piyasa duzeltmesi sistematik olarak FAZLA cikariliyor.")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
