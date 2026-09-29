"""D1-K · K çarpanının örneklem dışı sınaması (AS1).

Soru: Skorun K çarpanı (karşı taraf açık/gizli × ilk bildirim/güncelleme:
1,00 / 0,85 / 0,70 / 0,50) 19.09'da ilk yılın 2×2 tablosundan kuruldu.
O tablonun dört iddiası (K-H1…K-H4) bulgular kurulurken hiç görülmemiş
yılda (2024-09 → 2025-09-21) da var mı?

Ön kayıt: docs/arastirma/2026-09-29-arastirma-haritasi.md §6 "D1-K"
(commit df9a7f8, sonuçlardan önce). Karar kuralları K1 ön kaydından
(docs/arastirma/2026-09-28-k1-on-kayit.md). Sonuç notu:
docs/arastirma/2026-09-29-k-carpani-sinamasi.md.

Yalnız okur: LLM yok, ücret yok, veritabanına yazmaz, KAP'a gitmez,
dosya yazmaz. Tanımlar içe aktarılıyor, kopyalanmıyor: olay sorgusu,
dönemler ve anormal hacim `skor_gecerlilik`, kümelenmiş regresyon ve ISO
hafta `analiz_gecerlilik`, MDE katsayısı `analiz_k1_rejim`, K ve f(r)
`kap_radar.skor`.

    python scripts/analiz_k_carpani.py              # hücreler, K-H1…K-H4, ikincil, dönem farkı,
                                                    # sağlamlık, K = 1 olsaydı (betimleme)
    python scripts/analiz_k_carpani.py --mutabakat  # + ilk yılın 19.09 tablosundan bugüne adım adım

`--mutabakat` 19.09'un olay matrisini okur (data/ozellikler.csv, commit
19f630e'de dondurulmuş: β = 1 CAR'ları ve eski "alan dolu" kuralı).

Uygulama kararları (sonuçlara bakılmadan, notun "Veri ve yöntem"inde):
  - Evren: veritabanının yayın evreni (`akis` görünümü: kapı, bağ, elle
    karar). Olaylar `skor_gecerlilik.yukle` ile aynı sorgudan gelir, sonra
    `akis`'teki kap_id'lere süzülür. Tekilleştirme yok (§7 gibi).
  - Hücre tablosu §7 gibi: n = CAR3'ü olan olay; AV ortalaması o olaylar
    üzerinden.
  - Sınavlarda her ölçünün kendi örneklemi: CAR_k'si (ya da AV'si) olan
    olaylar. Model doygun: dört hücrenin üçü gösterge, sabit = taban
    hücre. Aranan fark son katsayı; t pay + ISO hafta (t0) iki yönlü.
  - Hüküm için "ilk yıl etkisi" haritadaki 19.09 rakamları.
"""

from __future__ import annotations

import argparse
import math
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from analiz_gecerlilik import _sabit, hafta, ols_kumeli  # noqa: E402
from analiz_k1_rejim import MDE_KATSAYI  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.skor import f_oran, guvenilirlik, kademe  # noqa: E402
from skor_gecerlilik import (  # noqa: E402
    ANALIZ_BASI,
    anormal_hacim,
    bas,
    donem_suz,
    hacim_serileri,
    yildiz,
    yukle,
)

ESIK = 1.96
ACIK_ILK, ACIK_GUNC, GIZLI_ILK, GIZLI_GUNC = (
    "açık + ilk", "açık + güncelleme", "gizli + ilk", "gizli + güncelleme")
HUCRELER = (ACIK_ILK, ACIK_GUNC, GIZLI_ILK, GIZLI_GUNC)
DONEM_ADI = {"sinama": "SINAMA · 2024-09 → 2025-09-21 (örneklem dışı)",
             "tumu": "İKİ YIL BİRLİKTE",
             "analiz": "ANALİZ · 2025-09-22 → (K'nın türetildiği yıl, bugünkü veri)"}

# 19.09 tablosu (skor-kanit-taramasi §4; AV sütunu 21.09 skor_gecerlilik §7,
# metodoloji K bölümü). Haritadaki hipotez tablosu bunlardan.
ILK_YIL = {
    ACIK_ILK: {"n": 327, "car1": 1.16, "car3": 1.23, "av": 0.351},
    ACIK_GUNC: {"n": 55, "car1": 0.50, "car3": 0.68, "av": 0.317},
    GIZLI_ILK: {"n": 213, "car1": 0.84, "car3": 0.02, "av": 0.259},
    GIZLI_GUNC: {"n": 6, "car1": -0.75, "car3": -5.18, "av": 0.615},
}

# K-H1, K-H3 ve K-H4'ün ikili farkları: (hedef, taban), hedef − taban > 0 beklenir.
KH1 = (ACIK_ILK, GIZLI_ILK)
KH3 = (ACIK_ILK, ACIK_GUNC)
KH4 = ((ACIK_ILK, GIZLI_ILK), (ACIK_ILK, ACIK_GUNC), (ACIK_GUNC, GIZLI_ILK))

# 19.09 olay matrisi: fiyat serisi 2025-09-07'de başlıyordu (data/fiyat.log);
# 21.09'daki AV'yi taklit etmek için hacim bu aralığa kırpılır.
ILK_FIYAT = (pd.Timestamp("2025-09-07").date(), pd.Timestamp("2026-09-19").date())
ILK_SON = pd.Timestamp("2026-09-19", tz="Europe/Istanbul")  # 19.09 matrisinin son günü 18.09

# bbac018 öncesi kural (skor_gecerlilik SORGU'nun eski hâli): alan boş değilse "açık".
ESKI_KURAL = """
select kap_id, (kap_alanlari->>'karsi_taraf' is not null
                and kap_alanlari->>'karsi_taraf' <> '') as kt_eski
from bildirim
"""


# ---------------------------------------------------------------- veri

def hucre(acik: bool, gunc: bool) -> str:
    return {(True, False): ACIK_ILK, (True, True): ACIK_GUNC,
            (False, False): GIZLI_ILK, (False, True): GIZLI_GUNC}[(bool(acik), bool(gunc))]


def olaylari_kur():
    """skor_gecerlilik ile aynı yol + yayın evreni bayrağı + eski kural."""
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        olay, fiyat, endeks = yukle(b)
        yayin = set(pd.read_sql("select kap_id from akis", b)["kap_id"])
        eski = pd.read_sql(ESKI_KURAL, b)
    takvim = list(endeks["tarih"])
    olay["av"] = anormal_hacim(olay, hacim_serileri(fiyat), takvim)
    for k in ("etki_skoru", "ciro_orani", "car_1g", "car_3g", "car_5g"):
        olay[k] = pd.to_numeric(olay[k], errors="coerce")
    olay = olay.merge(eski, on="kap_id", how="left")
    olay["yayinda"] = olay["kap_id"].isin(yayin)
    olay["hucre"] = [hucre(a, g) for a, g in zip(olay["kt_acik"], olay["guncelleme_mi"])]
    olay["hucre_eski"] = [hucre(a, g) for a, g in zip(olay["kt_eski"], olay["guncelleme_mi"])]
    olay["K"] = [float(guvenilirlik(karsi_taraf_acik=bool(a), guncelleme_mi=bool(g)))
                 for a, g in zip(olay["kt_acik"], olay["guncelleme_mi"])]
    return olay, fiyat, endeks, takvim


def kumeler(d: pd.DataFrame) -> dict[str, np.ndarray]:
    return {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}


# ------------------------------------------------------------ ölçüler

def hucre_tablosu(d: pd.DataFrame, kol: str = "hucre") -> pd.DataFrame:
    """§7 gibi: CAR3'ü olan olaylar; CAR puan, AV log."""
    c = d.dropna(subset=["car_3g"])
    satir = {}
    for h in HUCRELER:
        x = c[c[kol] == h]
        satir[h] = {
            "n": len(x), "pay": x["ticker"].nunique(),
            "CAR1 ort": x["car_1g"].mean() * 100, "CAR1 med": x["car_1g"].median() * 100,
            "CAR3 ort": x["car_3g"].mean() * 100, "CAR3 med": x["car_3g"].median() * 100,
            "CAR5 ort": x["car_5g"].mean() * 100, "CAR5 med": x["car_5g"].median() * 100,
            "AV ort": x["av"].mean(), "n AV": int(x["av"].notna().sum()),
        }
    return pd.DataFrame.from_dict(satir, orient="index")


def fark(d: pd.DataFrame, y: str, hedef: str, taban: str, kol: str = "hucre"):
    """hedef − taban, doygun hücre modelinde; iki yönlü kümeli t, SE, MDE."""
    x = d[d[y].notna() & d["t0"].notna()]
    nh, nt = int((x[kol] == hedef).sum()), int((x[kol] == taban).sum())
    if nh < 2 or nt < 2:
        return None
    diger = [h for h in HUCRELER if h not in (hedef, taban) and (x[kol] == h).any()]
    X = np.column_stack([(x[kol] == h).to_numpy(float) for h in [*diger, hedef]])
    b, t = ols_kumeli(x[y].to_numpy(float), X, kumeler(x))["iki yönlü"]
    se = abs(b / t) if t else float("nan")
    return {"b": b, "t": t, "se": se, "mde": MDE_KATSAYI * se, "n_hedef": nh, "n_taban": nt}


def ic_fark(d: pd.DataFrame, h: str, kol: str = "hucre"):
    """Hücre içinde CAR3 − CAR1 ortalaması (K-H2); iki yönlü kümeli."""
    x = d[(d[kol] == h) & d["car_3g"].notna() & d["car_1g"].notna() & d["t0"].notna()]
    if len(x) < 3:
        return None
    b, t = _sabit((x["car_3g"] - x["car_1g"]).to_numpy(float), kumeler(x))["iki yönlü"]
    se = abs(b / t) if t else float("nan")
    return {"b": b, "t": t, "se": se, "mde": MDE_KATSAYI * se, "n": len(x),
            "pay": x["ticker"].nunique(), "car1": x["car_1g"].mean(), "car3": x["car_3g"].mean()}


def hukum(r, etki: float) -> str:
    """K1 kuralları; beklenen işaret `etki`nin işareti.

    Aynı işaret, |t| < 1,96 ve MDE < |ilk yıl etkisi| hem "yön aynı,
    sonuçsuz: etki daha küçük" hem "tekrarlanmadı" tanımına giriyor. K1
    notu H2/A'da ikincisini seçti; burada da ikincisi (daha katı olan).
    """
    if r is None or not np.isfinite(r["t"]):
        return "sınanamadı"
    ayni = np.sign(r["b"]) == np.sign(etki)
    if abs(r["t"]) >= ESIK:
        return "tekrarlandı" if ayni else "tekrarlanmadı (ters, anlamlı)"
    if r["mde"] < abs(etki):
        return ("tekrarlanmadı (etki daha küçük: MDE < ilk yıl)" if ayni
                else "tekrarlanmadı (yön ters, MDE < ilk yıl)")
    return "yön aynı, sonuçsuz (güç yetmedi)" if ayni else "yön ters, sonuçsuz (güç yetmedi)"


def sirali_hukum(hukumler: list[str]) -> str:
    """K-H4 bütünü: üç ikili fark da tekrarlandıysa tekrarlandı; biri
    tekrarlanmadıysa tekrarlanmadı; gerisi sonuçsuz (sonuçtan önce sabit)."""
    if all(h == "tekrarlandı" for h in hukumler):
        return "tekrarlandı"
    if any(h.startswith("tekrarlanmadı") for h in hukumler):
        return "tekrarlanmadı"
    return "sonuçsuz"


# ------------------------------------------------------------ yazdırma

def p(v: float) -> str:
    return f"{v * 100:+.2f}"


def satir(ad: str, r, etki: float | None, olcek: float = 100.0, bicim: str = "{:+.2f}") -> str:
    """Tek sınav satırı; `etki` None ise betimleme (hüküm yok)."""
    if r is None:
        return f"  {ad:<38} yetersiz gözlem"
    b, se, mde = (bicim.format(v * olcek) for v in (r["b"], r["se"], r["mde"]))
    n = f"n {r['n_hedef']}/{r['n_taban']}" if "n_hedef" in r else f"n {r['n']}"
    lo, hi = (bicim.format(v * olcek) for v in (r["b"] - ESIK * r["se"], r["b"] + ESIK * r["se"]))
    bas_ = (f"  {ad:<38} fark {b} (SE {se.lstrip('+')}, t {r['t']:+.2f}{yildiz(r['t']):<3}) "
            f"%95 [{lo}, {hi}] MDE {mde.lstrip('+')}")
    if etki is None:
        return f"{bas_}  {n}"
    return f"{bas_}  ilk yıl {bicim.format(etki * olcek)}  {n}  → {hukum(r, etki)}"


def ilk_yil_etkisi(hedef: str, taban: str, olcu: str) -> float:
    k = ILK_YIL[hedef][olcu] - ILK_YIL[taban][olcu]
    return k / 100 if olcu.startswith("car") else k


def hipotezler(d: pd.DataFrame, kol: str = "hucre") -> dict:
    """K-H1…K-H4; dönüş {ad: (sonuç, hüküm)}, dönem farkı için."""
    out = {}
    e1 = ilk_yil_etkisi(*KH1, "car3")
    r = fark(d, "car_3g", *KH1, kol=kol)
    print(satir("K-H1 CAR3 açık+ilk − gizli+ilk", r, e1))
    out["K-H1"] = (r, hukum(r, e1))
    for y, ad in (("car_1g", "CAR1"), ("car_5g", "CAR5")):
        print(satir(f"     ({ad}, betimleme)", fark(d, y, *KH1, kol=kol), None))

    e2 = (ILK_YIL[GIZLI_ILK]["car3"] - ILK_YIL[GIZLI_ILK]["car1"]) / 100
    r = ic_fark(d, GIZLI_ILK, kol=kol)
    print(satir("K-H2 gizli+ilk CAR3 − CAR1", r, e2))
    if r:
        print(f"  {'':<38} (CAR1 {p(r['car1'])}, CAR3 {p(r['car3'])}, pay {r['pay']})")
    out["K-H2"] = (r, hukum(r, e2))
    for h in (ACIK_ILK, ACIK_GUNC):
        rr = ic_fark(d, h, kol=kol)
        if rr:
            print(f"     ({h} CAR3 − CAR1, betimleme) {p(rr['b'])} t {rr['t']:+.2f} n {rr['n']}")

    e3 = ilk_yil_etkisi(*KH3, "car3")
    r = fark(d, "car_3g", *KH3, kol=kol)
    print(satir("K-H3 CAR3 açık+ilk − açık+güncelleme", r, e3))
    out["K-H3"] = (r, hukum(r, e3))

    c = d.dropna(subset=["av"])
    ort = {h: c.loc[c[kol] == h, "av"].mean() for h in (GIZLI_ILK, ACIK_GUNC, ACIK_ILK)}
    sira = " < ".join(sorted(ort, key=ort.get))
    print("  K-H4 AV sıralaması (beklenen: gizli+ilk < açık+güncelleme < açık+ilk; AV'si olan bütün olaylar)")
    print(f"       gözlenen: {sira}  ("
          + ", ".join(f"{h} {v:.3f}" for h, v in ort.items()) + ")")
    hs = []
    for hedef, taban in KH4:
        e = ilk_yil_etkisi(hedef, taban, "av")
        r = fark(d, "av", hedef, taban, kol=kol)
        print(satir(f"     AV {hedef} − {taban}", r, e, olcek=1.0, bicim="{:+.3f}"))
        hs.append(hukum(r, e))
        out[f"K-H4 {hedef} − {taban}"] = (r, hs[-1])
    print(f"  K-H4 bütün: {sirali_hukum(hs)}")
    return out


def donem_farki(a: dict, b: dict) -> None:
    """K1 kuralı: z = (a − b) / √(se_a² + se_b²); işaret ve büyüklük tutarlılığı esas."""
    bas("DÖNEM FARKI · analiz − sınama, z = (a − b) / √(se_a² + se_b²)")
    for ad in a:
        ra, rb = a[ad][0], b[ad][0]
        if ra is None or rb is None:
            print(f"  {ad:<44} —")
            continue
        olcek, bicim = (1.0, "{:+.3f}") if ad.startswith("K-H4") else (100.0, "{:+.2f}")
        z = (ra["b"] - rb["b"]) / math.sqrt(ra["se"] ** 2 + rb["se"] ** 2)
        print(f"  {ad:<44} analiz {bicim.format(ra['b'] * olcek)}  sınama {bicim.format(rb['b'] * olcek)}"
              f"  z {z:+.2f}")


def ikincil(d: pd.DataFrame) -> None:
    """Skorlu bildirimlerde CAR3 ~ gizli + güncelleme + f(r), iki yönlü kümeli."""
    s = d[d["etki_skoru"].notna() & d["car_3g"].notna() & d["ciro_orani"].notna()
          & d["t0"].notna()].copy()
    s["gizli"] = (~s["kt_acik"].astype(bool)).astype(float)
    s["guncelleme"] = s["guncelleme_mi"].astype(bool).astype(float)
    s["f_r"] = [float(f_oran(Decimal(str(v)))) for v in s["ciro_orani"]]
    adlar = ("gizli", "guncelleme", "f_r")
    parca = []
    for hedef in adlar:
        sira = [a for a in adlar if a != hedef] + [hedef]
        b, t = ols_kumeli(s["car_3g"].to_numpy(float), s[sira].to_numpy(float), kumeler(s))["iki yönlü"]
        se = abs(b / t) if t else float("nan")
        parca.append(f"{hedef} {b * 100:+.2f} (t {t:+.2f}{yildiz(t)}, MDE {MDE_KATSAYI * se * 100:.2f})")
    print(f"  n {len(s)} pay {s['ticker'].nunique()} · gizli %{s['gizli'].mean() * 100:.0f}, "
          f"güncelleme %{s['guncelleme'].mean() * 100:.0f}, f(r) ort {s['f_r'].mean():.3f}")
    print("  CAR3 (puan) ~ " + " · ".join(parca))


def secenek_etkisi(v: pd.DataFrame) -> None:
    """Betimleme: yayındaki skorlu bildirimlerde K = 1 olsaydı ne değişirdi.

    S kademesi `kap_radar.skor.kademe` (Modül C akran grubu). Sitedeki
    rutin/önemli/mega etiketi 24.09'dan beri r'den okunuyor, K'dan
    etkilenmiyor. Ayrıca saklı skorun bugünkü sınıflamayla tutarlılığı.
    """
    s = v[v["etki_skoru"].notna() & v["ciro_orani"].notna()].copy()
    f = [f_oran(Decimal(str(r))) for r in s["ciro_orani"]]
    s["S_hesap"] = [float(min(Decimal(5), 5 * x * Decimal(str(k)))) for x, k in zip(f, s["K"])]
    s["S_k1"] = [float(min(Decimal(5), 5 * x)) for x in f]
    s["kad"] = [kademe(Decimal(str(round(x, 2)))) for x in s["etki_skoru"]]
    s["kad_k1"] = [kademe(Decimal(str(round(x, 2)))) for x in s["S_k1"]]
    bas("SEÇENEK ETKİSİ · yayındaki skorlu bildirimler, K = 1 olsaydı (betimleme)")
    print(f"  skorlu {len(s)} · K dağılımı: "
          + ", ".join(f"{k:.2f} → {n}" for k, n in s["K"].value_counts().sort_index().items()))
    uyumsuz = (s["etki_skoru"] - s["S_hesap"]).abs() > 0.011
    print(f"  saklı S ile 5·f(r)·K(bugünkü sınıf) farklı (> 0,01): {int(uyumsuz.sum())}")
    deg = s["kad"] != s["kad_k1"]
    print(f"  S değişen {int((s['K'] < 1).sum())} · S kademesi değişen {int(deg.sum())}: "
          + ", ".join(f"{a} → {b} {n}" for (a, b), n in
                      s[deg].groupby(["kad", "kad_k1"]).size().items()))
    print(f"  ortalama S {s['etki_skoru'].mean():.2f} → {s['S_k1'].mean():.2f}")


def tablo_yaz(t: pd.DataFrame) -> None:
    print(t.to_string(float_format="{:+.2f}".format,
                      formatters={"AV ort": "{:+.3f}".format, "n": "{:d}".format,
                                  "pay": "{:d}".format, "n AV": "{:d}".format}))


# --------------------------------------------------------- mutabakat

def ozet(d: pd.DataFrame, kol: str) -> str:
    """n / CAR3 / (gizli+ilk CAR1) tek satır."""
    c = d.dropna(subset=["car_3g"])
    parca = []
    for h in HUCRELER:
        x = c[c[kol] == h]
        parca.append(f"{len(x):>4} {x['car_3g'].mean() * 100:+6.2f}")
    g = c[c[kol] == GIZLI_ILK]
    return "  ".join(parca) + f"   | gizli+ilk CAR1 {g['car_1g'].mean() * 100:+.2f}"


def av_ozet(d: pd.DataFrame, kol: str) -> str:
    c = d.dropna(subset=["car_3g"])
    return "  ".join(f"{c.loc[c[kol] == h, 'av'].mean():+.3f} ({int(c.loc[c[kol] == h, 'av'].notna().sum()):>3})"
                     for h in HUCRELER)


def mutabakat(olay: pd.DataFrame, fiyat: pd.DataFrame, takvim: list) -> None:
    oz = pd.read_csv(KOK / "data" / "ozellikler.csv", dtype={"kap_id": str})
    oz["t0"] = pd.to_datetime(oz["t0"]).dt.date
    oz["guncelleme_mi"] = oz["guncelleme"].astype(bool)
    oz["hucre_1909"] = [hucre(a, g) for a, g in zip(oz["karsi_taraf_acik"], oz["guncelleme_mi"])]
    bugun = olay.set_index("kap_id")
    oz = oz.join(bugun[["hucre", "hucre_eski", "yayinda", "av"]], on="kap_id")
    oz = oz.join(bugun[["car_1g", "car_3g", "car_5g"]].add_suffix("_bugun"), on="kap_id")

    bas("MUTABAKAT · ilk yıl: 19.09 tablosundan bugünkü tabloya (CAR3, puan)")
    print(f"  {'adım':<52}" + "".join(f"{h:>13}" for h in HUCRELER))
    print(f"  {'19.09 (kanıt taraması §4)':<52}" + "".join(
        f"{ILK_YIL[h]['n']:>6} {ILK_YIL[h]['car3']:+6.2f}" for h in HUCRELER)
        + f"   | gizli+ilk CAR1 {ILK_YIL[GIZLI_ILK]['car1']:+.2f}")
    m0 = oz.copy()
    print(f"  {'M0 19.09 matrisi: β=1 CAR, alan dolu kuralı':<52}{ozet(m0, 'hucre_1909')}")
    print(f"  {'M1 + bugünkü sınıflama (bbac018)':<52}{ozet(m0, 'hucre')}")
    m2 = oz.drop(columns=["car_1g", "car_3g", "car_5g"]).rename(columns=lambda c: c.replace("_bugun", ""))
    print(f"  {'M2 + bugünkü CAR (EW piyasa modeli, Vasicek)':<52}{ozet(m2, 'hucre')}")
    print(f"  {'M2b bugünkü CAR, eski kural (yalnız model etkisi)':<52}{ozet(m2, 'hucre_eski')}")
    a = donem_suz(olay, "analiz")
    a18 = a[pd.to_datetime(a["yayin_zamani"], utc=True) < ILK_SON]
    print(f"  {'M3 bugünkü olay seti, aynı pencere (→ 18.09)':<52}{ozet(a18, 'hucre')}")
    print(f"  {'M4 + 19.09 sonrası olaylar (analiz dönemi tamamı)':<52}{ozet(a, 'hucre')}")
    print(f"  {'M5 + yayın evreni süzgeci (ana tablo)':<52}{ozet(a[a['yayinda']], 'hucre')}")
    yeni = set(a18["kap_id"]) - set(oz["kap_id"])
    eksik = set(oz["kap_id"]) - set(a18["kap_id"])
    print(f"  19.09 matrisinde olup bugün pencerede olmayan {len(eksik)}, yeni {len(yeni)}; "
          f"19.09 setinin yayın dışı kalan {int((~oz['yayinda'].fillna(False)).sum())}")
    deg = oz[oz["hucre_1909"] != oz["hucre"]]
    print(f"  Sınıfı değişen: {len(deg)} / {len(oz)} ·",
          ", ".join(f"{a_} → {b_} {n}" for (a_, b_), n in
                    deg.groupby(["hucre_1909", "hucre"]).size().items()))
    ci = oz.dropna(subset=["car_3g", "car_3g_bugun"])
    print(f"  CAR3 β=1 ↔ bugün: olay {len(ci)}, korelasyon {np.corrcoef(ci['car_3g'], ci['car_3g_bugun'])[0, 1]:.3f}, "
          f"ortalama {ci['car_3g'].mean() * 100:+.2f} → {ci['car_3g_bugun'].mean() * 100:+.2f}, "
          f"|fark| > 1 puan {int(((ci['car_3g'] - ci['car_3g_bugun']).abs() > 0.01).sum())}")

    bas("MUTABAKAT · ilk yıl AV (parantezde AV'si olan olay)")
    print(f"  {'adım':<52}" + "".join(f"{h:>15}" for h in HUCRELER))
    print(f"  {'19.09/21.09 (metodoloji K bölümü)':<52}" + "".join(
        f"{ILK_YIL[h]['av']:>+9.3f}      " for h in HUCRELER))
    kirpik = fiyat[(fiyat["tarih"] >= ILK_FIYAT[0]) & (fiyat["tarih"] <= ILK_FIYAT[1])]
    a0 = oz.drop(columns=["av"]).copy()
    a0["ticker"] = a0["ticker"].astype(str)
    a0["av"] = anormal_hacim(a0, hacim_serileri(kirpik), takvim)
    a0 = a0[a0["car_3g"].notna()]
    print(f"  {'A0 19.09 seti, fiyat 2025-09-07 → (21.09 taklidi), eski kural':<52}{av_ozet(a0, 'hucre_eski')}"
          f"  toplam AV {int(a0['av'].notna().sum())}")
    a1 = oz.drop(columns=["av"]).copy()
    a1["av"] = anormal_hacim(a1, hacim_serileri(fiyat), takvim)
    a1 = a1[a1["car_3g"].notna()]
    print(f"  {'A1 + bugünkü fiyat geçmişi (2024-01 →)':<52}{av_ozet(a1, 'hucre_eski')}"
          f"  toplam AV {int(a1['av'].notna().sum())}")
    print(f"  {'A2 + bugünkü sınıflama (bbac018)':<52}{av_ozet(a1, 'hucre')}")
    print(f"  {'A3 bugünkü olay seti, analiz tamamı, eski kural':<52}{av_ozet(a, 'hucre_eski')}")
    print(f"  {'A4 bugünkü olay seti, analiz tamamı, yeni kural':<52}{av_ozet(a, 'hucre')}")
    print(f"  {'A5 + yayın evreni (ana tablo)':<52}{av_ozet(a[a['yayinda']], 'hucre')}")

    bas("MUTABAKAT · 24.09 örneklem dışı AV satırı (metodoloji :511) bugünkü sınıflamayla")
    s = donem_suz(olay, "sinama")
    print("  24.09 yayımlanan: sınama gizli+ilk 0,397 > açık+ilk 0,317 (eski kural)")
    for ad, d, kol in (("eski kural, süzgeçsiz", s, "hucre_eski"), ("yeni kural, süzgeçsiz", s, "hucre"),
                       ("yeni kural, yayın evreni", s[s["yayinda"]], "hucre")):
        print(f"  {ad:<52}{av_ozet(d, kol)}")
        print(f"  {'   n, CAR3':<52}{ozet(d, kol)}")


# -------------------------------------------------------------- ana

def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="D1-K: K çarpanının örneklem dışı sınaması")
    ap.add_argument("--mutabakat", action="store_true", help="ilk yılı 19.09 tablosuyla karşılaştır")
    args = ap.parse_args()

    olay, fiyat, endeks, takvim = olaylari_kur()
    v = olay[olay["yayinda"]]
    print(f"olay (skor_gecerlilik sorgusu) {len(olay)} · yayın evreninde {len(v)} · "
          f"t0'lı {int(v['t0'].notna().sum())} · CAR3'lü {int(v['car_3g'].notna().sum())} · "
          f"AV'li {int(v['av'].notna().sum())} · analiz başı {ANALIZ_BASI.date()}")

    sonuc = {}
    for donem in ("sinama", "tumu", "analiz"):
        d = donem_suz(v, donem)
        bas(f"{DONEM_ADI[donem]} · {len(d)} olay, {d['ticker'].nunique()} pay")
        print("  Hücreler (CAR puan; AV log; n = CAR3'ü olan):")
        tablo_yaz(hucre_tablosu(d))
        print()
        sonuc[donem] = hipotezler(d)
        print("\n  İkincil · skorlu bildirimler:")
        ikincil(d)
    donem_farki(sonuc["analiz"], sonuc["sinama"])

    bas("SAĞLAMLIK · sınama yılı (asimetri: hükmü yalnız zayıflatabilir)")
    s_tum = donem_suz(olay, "sinama")
    s_yay = s_tum[s_tum["yayinda"]]
    tekil = (s_yay.dropna(subset=["t0"]).sort_values("yayin_zamani")
             .drop_duplicates(["ticker", "t0"], keep="first"))
    for ad, d in (("yayın süzgeci yok (skor_gecerlilik evreni)", s_tum),
                  ("(pay, t0) tekil, K1 kuralı", tekil)):
        print(f"\n  -- {ad}: {len(d)} olay")
        hipotezler(d)

    secenek_etkisi(v)

    if args.mutabakat:
        mutabakat(olay, fiyat, takvim)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
