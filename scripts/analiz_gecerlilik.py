"""Bulguların geçerlilik tehditleri: rejim, güç, kirlenme, kümelenme.

Kullanım:  python scripts/analiz_gecerlilik.py

Hiçbir şey yazmaz, ağa çıkmaz, LLM yok. Girdi: veritabanı (akis, tepki,
tahta_durumu, fiyat, endeks, faktör, kur, dönem büyümesi) ve yerel KAP
liste arşivi (data/ham/liste*, tüm bildirim türleri).

docs/arastirma/2026-09-27-gecerlilik-degerlendirmesi.md bu betiğin
çıktısını tartışır. Sorular (Hüseyin'in itirazından, 2026-09-27):

  1. Rejim: örneklem hangi piyasada toplandı? (yarıyıllık endeks, USD,
     oynaklık, TMS 29 katsayısından yıllık enflasyon)
  2. Güç: iki yıl ve ~1.250 olay neyi ayırt etmeye yetiyor?
  3. Sermaye işlemi: ±%10 fiyat marjını aşan gün (bedelsiz, bölünme)
     CAR ya da hacim penceresine giriyor mu?
  4. Piyasa hacmi: anormal hacim, borsanın genel hacim dalgasından
     arındırılınca ayakta mı? (Bulgu 1 ve 2)
  5. Karışan açıklama: aynı pencerede finansal rapor, sermaye işlemi,
     geri alım gibi başka bir açıklama varsa bulgular temiz alt
     örneklemde de duruyor mu?
  6. Zaman kümelenmesi: aynı haftaya düşen olaylar ortak piyasa şokunu
     paylaşıyor. Hisse + hafta iki yönlü kümelenmiş t ne diyor?
  7. Dönem kararlılığı: bulgular yarıyıllara bölününce ne kadar oynuyor?
  8. Payda: TMS 29'a geçiş 2024 ara dönem köprülerini nasıl etkiliyor?
  9. Fiyat marjı: tavan serisi tepkiyi 3 günlük pencereden taşırıyor mu?
"""

from __future__ import annotations

import math
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from skor_gecerlilik import (  # noqa: E402
    ASGARI_TAHMIN_GUN,
    OLAY_PENCERE,
    TAHMIN_BAS,
    TAHMIN_SON,
    bas,
    ols,
    yildiz,
)

# Borsa İstanbul pay piyasasında günlük fiyat marjı ±%10. Kapanıştan
# kapanışa bundan büyük hareket normal işlemle oluşamaz: sermaye işlemi
# (bedelsiz, bölünme, bedelli) ya da veri hatası. Yuvarlama payı %0,5.
MARJ = 0.105

# Bulgu 12'nin tedbirli / temiz tanımı (tahta bayrağıyla aynı eşikler).
TEDBIRLI_V90, TEMIZ_V90 = 8, 4

# Karışan açıklama kategorileri: KAP "subject" alanında geçen ifade.
# "Özel Durum Açıklaması (Genel)" çok geniş (dava, atama, tesis ziyareti)
# ve "Olağan Dışı Fiyat ve Miktar Hareketleri" Borsa'nın tepkiye sorusu;
# ikisi ayrı sayılıyor, sıkı tanıma girmiyor.
KATEGORILER = {
    "finansal rapor": ("Finansal Rapor", "Faaliyet Raporu"),
    "sermaye işlemi": ("Sermaye Artırımı", "Kayıtlı Sermaye Tavanı", "Bedelsiz"),
    "geri alım": ("Payların Geri Alınmasına",),
    "kâr payı": ("Kar Payı",),
    "birleşme / edinim": ("Birleşme", "Bölünme", "Finansal Duran Varlık Edinimi"),
    "ihale": ("İhale Süreci",),
    "başka yeni iş": ("Yeni İş İlişkisi",),
}
GENIS = {
    "özel durum (genel)": ("Özel Durum Açıklaması (Genel)",),
    "olağandışı hareket": ("Olağan Dışı Fiyat",),
}

SORGU = """
select a.kap_id, b.kap_index, a.ticker, a.yayin_zamani, a.etki_skoru::float as s,
       a.car_3g::float as car3, t.v90, (coalesce(t.vbts_kademe, 0) > 0) as vbts, tp.t0
from akis a
join bildirim b on b.kap_id = a.kap_id
left join tahta_durumu t on t.kap_id = a.kap_id
left join tepki tp on tp.kap_id = a.kap_id
"""


# ------------------------------------------------------------ istatistik

def _sandvic(Xd, e, kume):
    """Kümelenmiş "et" matrisi ve CR1 düzeltmesi."""
    gruplar = pd.unique(kume)
    et = np.zeros((Xd.shape[1], Xd.shape[1]))
    for g in gruplar:
        sel = kume == g
        sg = Xd[sel].T @ e[sel]
        et += np.outer(sg, sg)
    G, (n, k) = len(gruplar), Xd.shape
    return et * (G / (G - 1)) * ((n - 1) / (n - k)), G


def ols_kumeli(y, X, kumeler: dict[str, np.ndarray]) -> dict[str, tuple[float, float]]:
    """Katsayı ve her kümeleme için t. "iki yönlü" = hisse + hafta (CGM 2011).

    Dönüş: {kümeleme adı: (son değişkenin katsayısı, t)}.
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    X = X[:, None] if X.ndim == 1 else X
    Xd = np.column_stack([np.ones(len(y)), X])
    ekmek = np.linalg.pinv(Xd.T @ Xd)
    beta = ekmek @ Xd.T @ y
    e = y - Xd @ beta
    sonuc = {}
    etler = {ad: _sandvic(Xd, e, np.asarray(k))[0] for ad, k in kumeler.items()}
    if {"hisse", "hafta"} <= kumeler.keys():
        kesisim = np.array([f"{a}|{b}" for a, b in zip(kumeler["hisse"], kumeler["hafta"])])
        etler["iki yönlü"] = etler["hisse"] + etler["hafta"] - _sandvic(Xd, e, kesisim)[0]
    for ad, et in etler.items():
        V = ekmek @ et @ ekmek
        se = math.sqrt(V[-1, -1]) if V[-1, -1] > 0 else float("nan")
        sonuc[ad] = (float(beta[-1]), float(beta[-1] / se))
    return sonuc


def _sabit(y, kumeler):
    """Ortalama ve kümelenmiş t (sabit terimli regresyon)."""
    Xd = np.ones((len(y), 1))
    ort = float(y.mean())
    e = y - ort
    sonuc = {}
    etler = {ad: _sandvic(Xd, e, np.asarray(k))[0] for ad, k in kumeler.items()}
    if {"hisse", "hafta"} <= kumeler.keys():
        kesisim = np.array([f"{a}|{b}" for a, b in zip(kumeler["hisse"], kumeler["hafta"])])
        etler["iki yönlü"] = etler["hisse"] + etler["hafta"] - _sandvic(Xd, e, kesisim)[0]
    for ad, et in etler.items():
        v = float(et[0, 0]) / len(y) ** 2
        sonuc[ad] = (ort, ort / math.sqrt(v) if v > 0 else float("nan"))
    return sonuc


def t_satiri(sonuc: dict[str, tuple[float, float]]) -> str:
    return "  ".join(f"{ad} t={t:+.2f}{yildiz(t)}" for ad, (_, t) in sonuc.items())


def hafta(g: date) -> str:
    y, w, _ = g.isocalendar()
    return f"{y}-W{w:02d}"


def yariyil(g: date) -> str:
    return f"{g.year}Y{1 if g.month <= 6 else 2}"


# -------------------------------------------------------------- veriler

def yukle():
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        olay = pd.read_sql(SORGU, b)
        fiyat = pd.read_sql(
            "select ticker, tarih, kapanis_duzeltilmis::float as p, hacim::float as v "
            "from fiyat_gunluk", b)
        endeks = pd.read_sql(
            "select tarih, xu100_kapanis::float as x from endeks_gunluk order by tarih", b)
        ew = pd.read_sql(
            "select tarih, ew_getiri::float as ew from faktor_gunluk order by tarih", b)
        usd = pd.read_sql(
            "select tarih, tl_karsiligi::float as usd from kur_gunluk "
            "where para_birimi = 'USD' order by tarih", b)
        k = pd.read_sql(
            "select donem_sonu, ay_sayisi, katsayi::float as k from donem_buyume "
            "where reel and katsayi is not null", b)
    return olay, fiyat, endeks, ew, usd, k


def liste_tablosu() -> pd.DataFrame:
    """Yerel KAP liste arşivi: (ticker, gün, konu, indeks), tüm türler."""
    satir = []
    for k in HamArsiv(KOK / "data" / "ham").liste_kayitlari().values():
        gun = pd.to_datetime(k["publishDate"], format="%d.%m.%Y %H:%M:%S").date()
        for t in (x.strip() for x in (k.get("stockCodes") or "").split(",")):
            if t:
                satir.append((t, gun, k.get("subject") or "", k["disclosureIndex"]))
    return pd.DataFrame(satir, columns=["ticker", "gun", "konu", "idx"])


# ---------------------------------------------------------------- ölçüler

def olay_profili(olay, hacim, takvim, gunler) -> pd.DataFrame:
    """Olay başına ln(hacim[t0+k]) − ln(medyan taban). skor_gecerlilik ile aynı taban."""
    ix = {g: i for i, g in enumerate(takvim)}
    satir = {}
    for i, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix or o["ticker"] not in hacim:
            continue
        i0, seri = ix[o["t0"]], hacim[o["ticker"]]
        tah = seri.reindex([takvim[j] for j in range(max(0, i0 - TAHMIN_BAS),
                                                     max(0, i0 - TAHMIN_SON) + 1)])
        tah = tah[tah > 0]
        if len(tah) < ASGARI_TAHMIN_GUN:
            continue
        taban = math.log(float(tah.median()))
        d = {}
        for k in gunler:
            j = i0 + k
            if 0 <= j < len(takvim):
                v = seri.get(takvim[j])
                d[k] = math.log(v) - taban if v and v > 0 else np.nan
        # Olay penceresi AV'si (Bulgu 1'in ölçüsü): ln(ort hacim) − taban.
        ov = seri.reindex([takvim[j] for j in range(i0, min(i0 + OLAY_PENCERE, len(takvim)))])
        ov = ov[ov > 0]
        d["av"] = math.log(float(ov.mean())) - taban if len(ov) else np.nan
        satir[i] = d
    return pd.DataFrame.from_dict(satir, orient="index")


def piyasa_hacim_endeksi(fiyat) -> pd.Series:
    """Gün başına, hisselerin kendi medyanına göre ln hacminin medyanı."""
    f = fiyat[fiyat["v"] > 0].copy()
    f["lv"] = np.log(f["v"])
    f["lv"] -= f.groupby("ticker")["lv"].transform("median")
    return f.groupby("tarih")["lv"].median()


def piyasa_profili(olay, m, takvim, gunler) -> pd.DataFrame:
    """Aynı taban ve pencereyle piyasanın 'anormal hacmi'."""
    ix = {g: i for i, g in enumerate(takvim)}
    satir = {}
    for i, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix:
            continue
        i0 = ix[o["t0"]]
        tah = m.reindex([takvim[j] for j in range(max(0, i0 - TAHMIN_BAS),
                                                  max(0, i0 - TAHMIN_SON) + 1)]).dropna()
        if len(tah) < ASGARI_TAHMIN_GUN:
            continue
        taban = float(tah.median())
        d = {k: float(m.get(takvim[i0 + k], np.nan)) - taban
             for k in gunler if 0 <= i0 + k < len(takvim)}
        ov = m.reindex([takvim[j] for j in range(i0, min(i0 + OLAY_PENCERE, len(takvim)))]).dropna()
        # Hisse AV'si ln(ortalama) kullanıyor; piyasa tarafında ortalamanın
        # logu yerine logların ortalaması: fark gün içi dağılımdan, küçük.
        d["av"] = float(ov.mean()) - taban if len(ov) else np.nan
        satir[i] = d
    return pd.DataFrame.from_dict(satir, orient="index")


def marj_ihlali(olay, getiri, takvim, bas_k, son_k) -> pd.Series:
    """[t0+bas_k, t0+son_k] içinde |günlük getiri| > MARJ var mı?"""
    ix = {g: i for i, g in enumerate(takvim)}
    out = {}
    for i, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix or o["ticker"] not in getiri:
            continue
        i0 = ix[o["t0"]]
        g = getiri[o["ticker"]].reindex(
            [takvim[j] for j in range(max(1, i0 + bas_k), min(len(takvim), i0 + son_k + 1))])
        out[i] = bool((g.abs() > MARJ).any())
    return pd.Series(out)


def karisan(olay, liste, takvim) -> pd.DataFrame:
    """Olay ve öncesi penceresinde aynı hissenin diğer açıklamaları.

    Olay penceresi: [t0−1, t0+2] işlem günleri arasındaki takvim günleri
    (t0−1 akşamı açıklanan her şey t0 fiyatına girer). Öncesi: [t0−5, t0−1).
    Arşivin bittiği günden sonrasına uzanan pencere bilinmiyor (NaN).
    """
    ix = {g: i for i, g in enumerate(takvim)}
    son_gun = liste["gun"].max()
    grup = {t: g for t, g in liste.groupby("ticker")}
    tum = {**KATEGORILER, **GENIS}
    satir = {}
    for i, o in olay.iterrows():
        if pd.isna(o["t0"]) or o["t0"] not in ix:
            continue
        i0 = ix[o["t0"]]
        if i0 - 5 < 0 or i0 + 2 >= len(takvim) or takvim[i0 + 2] > son_gun:
            continue
        g = grup.get(o["ticker"])
        d = {ad: 0 for ad in tum} | {f"once {ad}": 0 for ad in tum}
        if g is not None:
            g = g[g["idx"] != o["kap_index"]]
            olayda = g[(g["gun"] >= takvim[i0 - 1]) & (g["gun"] <= takvim[i0 + 2])]
            once = g[(g["gun"] >= takvim[i0 - 5]) & (g["gun"] < takvim[i0 - 1])]
            for ad, kaliplar in tum.items():
                d[ad] = int(olayda["konu"].str.contains("|".join(map(_kacis, kaliplar))).sum())
                d[f"once {ad}"] = int(once["konu"].str.contains("|".join(map(_kacis, kaliplar))).sum())
        satir[i] = d
    return pd.DataFrame.from_dict(satir, orient="index")


def _kacis(s: str) -> str:
    return re.escape(s)


# ------------------------------------------------------------------ bölümler

def rejim(olay, endeks, ew, usd, k):
    bas("1 · REJİM: ÖRNEKLEM HANGİ PİYASADA TOPLANDI?")
    e = endeks.set_index("tarih")["x"]
    u = usd.set_index("tarih")["usd"].reindex(e.index).ffill()
    f = ew.set_index("tarih")["ew"].reindex(e.index).fillna(0)
    ew_seviye = (1 + f).cumprod()
    xr = np.log(e).diff()
    print(f"  {'dönem':<8}{'olay':>6}{'XU100 TL':>10}{'XU100 USD':>11}{'EW BIST':>9}"
          f"{'EW oynaklık':>13}{'kötü gün':>10}")
    gunler = pd.Series(e.index, index=e.index)
    olay_yy = pd.to_datetime(olay["yayin_zamani"], utc=True).dt.tz_convert("Europe/Istanbul")
    for yy, d in gunler.groupby(gunler.map(yariyil)):
        ilk, son = d.index[0], d.index[-1]
        onceki = e.index[max(0, e.index.get_loc(ilk) - 1)]
        tl = e[son] / e[onceki] - 1
        dol = (e[son] / u[son]) / (e[onceki] / u[onceki]) - 1
        ewr = ew_seviye[son] / ew_seviye[onceki] - 1
        vol = f.loc[ilk:son].std() * math.sqrt(250)
        kotu = int((xr.loc[ilk:son] < -0.03).sum())
        n = int((olay_yy.dt.date.map(yariyil) == yy).sum())
        # Kur arşivi 2024 ortasında başlıyor; öncesinde USD getirisi yok.
        dol_s = f"{dol*100:>+10.1f}%" if np.isfinite(dol) else f"{'—':>11}"
        print(f"  {yy:<8}{n:>6}{tl*100:>+9.1f}%{dol_s}{ewr*100:>+8.1f}%"
              f"{vol*100:>12.1f}%{kotu:>10}")
    ilk = date(2024, 9, 2)
    ilk = e.index[e.index >= ilk][0]
    son = e.index[-1]
    print(f"  Örneklem ({ilk} → {son}): XU100 TL {(e[son]/e[ilk]-1)*100:+.1f}%, "
          f"USD {((e[son]/u[son])/(e[ilk]/u[ilk])-1)*100:+.1f}%, "
          f"EW {(ew_seviye[son]/ew_seviye[ilk]-1)*100:+.1f}%, "
          f"USD/TL {(u[son]/u[ilk]-1)*100:+.1f}%")
    print("  En kötü 6 XU100 günü:",
          ", ".join(f"{g} {r*100:+.1f}%" for g, r in xr.nsmallest(6).items()))
    # TMS 29 katsayısı = 12 aylık TÜFE oranı (şirketlerin kendi yeniden
    # ifadesi). 2024 ara dönemleri HARİÇ: karşılaştırılan 2023 ara
    # dönemlerinin ilk yayını TMS 29 öncesi, tarihî maliyetle; oran orada
    # enflasyonu değil geçişi ölçüyor (bkz. bölüm 8).
    kk = k[k["ay_sayisi"].isin([3, 6, 9, 12])].groupby("donem_sonu")["k"].agg(["median", "size"])
    kk = kk[kk["size"] >= 20]
    print("  Yıllık enflasyon vekili (TMS 29 katsayısı medyanı, dönem sonu):",
          ", ".join(f"{d} %{(m-1)*100:.0f}{' (geçiş, TÜFE değil)' if d < date(2024, 12, 31) else ''}"
                    for d, m in kk["median"].items()))


def guc(v, prof):
    bas("2 · GÜÇ: İKİ YIL NEYİ AYIRT ETMEYE YETİYOR?  (80% güç, iki yönlü %5: MDE ≈ 2,8 × SE)")
    for ad, y, kume in (("ortalama AV [t0,t0+2]", prof["av"], v.loc[prof.index, "ticker"]),
                        ("ortalama CAR3", v["car3"], v["ticker"])):
        m = y.notna()
        r = ols(y[m], np.zeros((int(m.sum()), 0)), kume[m], []).loc["sabit"]
        print(f"  {ad:<24} n={int(r.n):>4} hisse={int(r.kume):>3}  ort={r.katsayi*100:+.2f}  "
              f"SE={r.std_hata*100:.2f}  MDE≈{2.8*r.std_hata*100:.2f} puan")
    d = v.dropna(subset=["s"])
    r = ols(d["car3"], d[["s"]], d["ticker"], ["s"]).loc["s"]
    print(f"  CAR3 ~ S eğimi            n={int(r.n):>4}  SE={r.std_hata*100:.3f} puan/S  "
          f"MDE≈{2.8*r.std_hata*100:.2f} puan/S (0→5 aralığında {14*r.std_hata*100:.1f} puan)")
    a = prof.join(v[["s", "ticker"]]).dropna(subset=["s", "av"])
    r = ols(a["av"], a[["s"]], a["ticker"], ["s"]).loc["s"]
    print(f"  AV ~ S eğimi              n={int(r.n):>4}  SE={r.std_hata:.4f}/S  "
          f"MDE≈{2.8*r.std_hata:.3f}/S (ölçülen +0,04…+0,07)")


def sermaye_islemi(v, getiri, takvim, fiyat):
    bas(f"3 · SERMAYE İŞLEMİ: ±%10 MARJINI AŞAN GÜN (|r| > %{MARJ*100:.1f})")
    tum = pd.concat(getiri.values()).dropna()
    print(f"  Fiyat serisinin tamamında: {len(tum)} hisse-günü, marj aşan {int((tum.abs() > MARJ).sum())} "
          f"(|r| ≥ %50: {int((tum.abs() >= 0.5).sum())})")
    car = marj_ihlali(v, getiri, takvim, 0, 2)
    av = marj_ihlali(v, getiri, takvim, -TAHMIN_BAS, 2)
    print(f"  CAR3 penceresinde [t0, t0+2]: {int(car.sum())} / {len(car)}")
    print(f"  Hacim penceresinde [t0−60, t0+2]: {int(av.sum())} / {len(av)}  "
          "(hacim pay adedi: bedelsiz pay sayısını, dolayısıyla hacmi mekanik artırır)")
    return av


def piyasa_hacmi(v, prof, pprof, av_ihlal):
    bas("4 · PİYASA HACMİ: ANORMAL HACİM BORSANIN GENEL DALGASINDAN ARINDIRILINCA")
    ortak = prof.index.intersection(pprof.index)
    print(f"  {'gün':<7}{'ham':>9}{'t':>7}{'piyasa':>9}{'düzeltilmiş':>13}{'t (hisse)':>11}{'t (2 yön)':>11}")
    for k in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 5, "av"]:
        h = prof.loc[ortak, k]
        pz = pprof.loc[ortak, k]
        m = h.notna() & pz.notna()
        kum = {"hisse": v.loc[ortak[m], "ticker"].to_numpy(),
               "hafta": v.loc[ortak[m], "t0"].map(hafta).to_numpy()}
        ham = _sabit(h[m].to_numpy(), kum)
        duz = _sabit((h[m] - pz[m]).to_numpy(), kum)
        print(f"  {str(k):<7}{(math.exp(ham['hisse'][0])-1)*100:>+8.1f}%{ham['hisse'][1]:>+7.2f}"
              f"{(math.exp(pz[m].mean())-1)*100:>+8.1f}%{(math.exp(duz['hisse'][0])-1)*100:>+12.1f}%"
              f"{duz['hisse'][1]:>+11.2f}{duz['iki yönlü'][1]:>+11.2f}")
    temiz = ortak[~av_ihlal.reindex(ortak).fillna(False).astype(bool)]
    h = (prof.loc[temiz, "av"] - pprof.loc[temiz, "av"]).dropna()
    kum = {"hisse": v.loc[h.index, "ticker"].to_numpy(), "hafta": v.loc[h.index, "t0"].map(hafta).to_numpy()}
    r = _sabit(h.to_numpy(), kum)
    print(f"  Sermaye işlemi olmayan pencerelerde düzeltilmiş AV: n={len(h)} "
          f"{(math.exp(r['hisse'][0])-1)*100:+.1f}%  {t_satiri(r)}")


def karisan_bolumu(v, prof, pprof, kar):
    bas("5 · KARIŞAN AÇIKLAMA: AYNI PENCEREDE BAŞKA BİR AÇIKLAMA")
    kv = v.join(kar, how="inner")
    print(f"  Arşivin kapsadığı olay: {len(kv)} (liste arşivi {LISTE_SON} tarihinde bitiyor)")
    print(f"  {'kategori':<22}{'[t0−1,t0+2]':>14}{'[t0−5,t0−1)':>14}")
    for ad in [*KATEGORILER, *GENIS]:
        print(f"  {ad:<22}{int((kv[ad] > 0).sum()):>9} (%{(kv[ad] > 0).mean()*100:>4.1f})"
              f"{int((kv['once ' + ad] > 0).sum()):>8} (%{(kv['once ' + ad] > 0).mean()*100:>4.1f})")
    sikı = (kv[list(KATEGORILER)] > 0).any(axis=1)
    sikı_once = (kv[[f"once {a}" for a in KATEGORILER]] > 0).any(axis=1)
    print(f"  Sıkı tanımla karışan: olayda {int(sikı.sum())} (%{sikı.mean()*100:.1f}), "
          f"öncesinde {int(sikı_once.sum())} (%{sikı_once.mean()*100:.1f})")
    temiz = kv[~sikı]

    def b12(d, ad):
        d = d.dropna(subset=["car3", "v90"])
        kum = {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}
        r = ols_kumeli(d["car3"], d[["v90"]], kum)
        ted = d[(d["v90"] > TEDBIRLI_V90) | d["vbts"]]["car3"]
        tem = d[(d["v90"] <= TEMIZ_V90) & ~d["vbts"]]["car3"]
        print(f"  B12 {ad:<22} n={len(d):>4}  v90={r['hisse'][0]*100:+.3f} puan/gün  {t_satiri(r)}"
              f"  | tedbirli {ted.mean()*100:+.2f}% (n={len(ted)}) temiz {tem.mean()*100:+.2f}% (n={len(tem)})")

    def b11(d, ad):
        d = d.dropna(subset=["car3", "s"])
        kum = {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}
        r = ols_kumeli(d["car3"], d[["s"]], kum)
        print(f"  B11 {ad:<22} n={len(d):>4}  CAR3~S={r['hisse'][0]*100:+.3f} puan/S  {t_satiri(r)}")

    def b1(d, ad):
        ix = d.index.intersection(prof.index).intersection(pprof.index)
        h = (prof.loc[ix, "av"] - pprof.loc[ix, "av"]).dropna()
        kum = {"hisse": d.loc[h.index, "ticker"].to_numpy(), "hafta": d.loc[h.index, "t0"].map(hafta).to_numpy()}
        r = _sabit(h.to_numpy(), kum)
        print(f"  B1  {ad:<22} n={len(h):>4}  düzeltilmiş AV {(math.exp(r['hisse'][0])-1)*100:+.1f}%  {t_satiri(r)}")

    def b2(d, ad):
        ix = d.index.intersection(prof.index).intersection(pprof.index)
        once = (prof.loc[ix, [-4, -3, -2, -1]].mean(axis=1) - pprof.loc[ix, [-4, -3, -2, -1]].mean(axis=1)).dropna()
        kum = {"hisse": d.loc[once.index, "ticker"].to_numpy(), "hafta": d.loc[once.index, "t0"].map(hafta).to_numpy()}
        r = _sabit(once.to_numpy(), kum)
        print(f"  B2  {ad:<22} n={len(once):>4}  [t0−4,t0−1] düzeltilmiş {(math.exp(r['hisse'][0])-1)*100:+.1f}%  {t_satiri(r)}")

    for f in (b1, b2, b11, b12):
        f(kv, "arşiv kapsamı (hepsi)")
        f(temiz, "karışmasız (sıkı)")
    b2(kv[~sikı_once & ~sikı], "öncesi de karışmasız")

    # "Başka yeni iş" gerçek bir karışan değil, aynı türden haber: şirket
    # birkaç gün içinde ikinci bir iş duyurmuş, iki olayın pencereleri üst
    # üste biniyor. Onu ayrı tutunca diğer türlerin etkisi görünüyor.
    diger = [a for a in KATEGORILER if a != "başka yeni iş"]
    yalniz_diger = (kv[diger] > 0).any(axis=1)
    once_diger = (kv[[f"once {a}" for a in diger]] > 0).any(axis=1)
    b12(kv[~yalniz_diger], "diğer türler hariç")
    b12(kv[kv["başka yeni iş"] == 0], "başka yeni iş hariç")
    b2(kv[~once_diger & ~yalniz_diger], "önce: diğer türler yok")
    b2(kv[(kv["once başka yeni iş"] == 0) & ~sikı], "önce: başka yeni iş yok")

    # Güç mü, etki mi? Karışmasız alt örneklem kadar rastgele alt örneklem.
    d = kv.dropna(subset=["car3", "v90"])
    n_temiz = int((~(d[list(KATEGORILER)] > 0).any(axis=1)).sum())
    rng = np.random.default_rng(7)
    ks, ts = [], []
    for _ in range(300):
        s = d.sample(n_temiz, random_state=int(rng.integers(1_000_000_000)))
        kum = {"hisse": s["ticker"].to_numpy(), "hafta": s["t0"].map(hafta).to_numpy()}
        r = ols_kumeli(s["car3"], s[["v90"]], kum)
        ks.append(r["hisse"][0] * 100)
        ts.append(r["iki yönlü"][1])
    print(f"  B12 rastgele {n_temiz}'lik alt örneklem (300 kez): katsayı medyan {np.median(ks):+.3f} "
          f"[%5 {np.percentile(ks, 5):+.3f}, %95 {np.percentile(ks, 95):+.3f}], "
          f"iki yönlü |t| > 1,96 oranı %{np.mean(np.abs(ts) > 1.96)*100:.0f}")


def kararlilik(v, prof, pprof):
    bas("7 · DÖNEM KARARLILIĞI (yarıyıl; t hisse-kümelenmiş)")
    v = v.copy()
    v["yy"] = v["t0"].map(lambda g: yariyil(g) if isinstance(g, date) else None)
    ix = prof.index.intersection(pprof.index)
    v.loc[ix, "avd"] = prof.loc[ix, "av"] - pprof.loc[ix, "av"]
    print(f"  {'yarıyıl':<8}{'n':>5}{'AV düz.':>10}{'t':>7}{'CAR3':>9}{'t':>7}{'B12 v90':>10}{'t':>7}{'CAR3~S':>9}{'t':>7}")
    for yy, d in v.groupby("yy"):
        a = d.dropna(subset=["avd"])
        c = d.dropna(subset=["car3"])
        ra = ols(a["avd"], np.zeros((len(a), 0)), a["ticker"], []).loc["sabit"] if len(a) > 20 else None
        rc = ols(c["car3"], np.zeros((len(c), 0)), c["ticker"], []).loc["sabit"] if len(c) > 20 else None
        cv = c.dropna(subset=["v90"])
        r12 = ols(cv["car3"], cv[["v90"]], cv["ticker"], ["v90"]).loc["v90"] if len(cv) > 30 else None
        cs = c.dropna(subset=["s"])
        r11 = ols(cs["car3"], cs[["s"]], cs["ticker"], ["s"]).loc["s"] if len(cs) > 30 else None

        def f(r, carp=100, fmt="{:+.2f}"):
            return (f"{fmt.format(r.katsayi*carp):>9}{r.t:>+7.2f}" if r is not None else f"{'—':>9}{'':>7}")
        print(f"  {yy:<8}{len(d):>5}{f(ra, 100, '{:+.1f}')}{f(rc)}{f(r12, 100, '{:+.3f}')}{f(r11, 100, '{:+.2f}')}")


def zaman_kumelenmesi(v):
    bas("6 · ZAMAN KÜMELENMESİ: AYNI HAFTANIN OLAYLARI ORTAK ŞOKU PAYLAŞIYOR")
    d = v.dropna(subset=["car3"])
    haftalar = d["t0"].map(hafta)
    print(f"  CAR3'lü olay {len(d)}, hafta {haftalar.nunique()}, hisse {d['ticker'].nunique()}; "
          f"olay/hafta medyan {haftalar.value_counts().median():.0f}, en kalabalık hafta "
          f"{haftalar.value_counts().max()}")
    kum = {"hisse": d["ticker"].to_numpy(), "hafta": haftalar.to_numpy()}
    r = _sabit(d["car3"].to_numpy(), kum)
    print(f"  Ortalama CAR3 {r['hisse'][0]*100:+.2f}%  {t_satiri(r)}")
    tp = d.groupby(haftalar)["car3"].mean()
    t_tp = tp.mean() / (tp.std(ddof=1) / math.sqrt(len(tp)))
    print(f"  Takvim-zaman portföyü (haftalık ortalama, {len(tp)} hafta): ort {tp.mean()*100:+.2f}%  "
          f"t={t_tp:+.2f}{yildiz(t_tp)}")
    dv = d.dropna(subset=["v90"])
    kum = {"hisse": dv["ticker"].to_numpy(), "hafta": dv["t0"].map(hafta).to_numpy()}
    print(f"  B12 CAR3 ~ v90   {t_satiri(ols_kumeli(dv['car3'], dv[['v90']], kum))}")
    ds = d.dropna(subset=["s"])
    kum = {"hisse": ds["ticker"].to_numpy(), "hafta": ds["t0"].map(hafta).to_numpy()}
    print(f"  B11 CAR3 ~ S     {t_satiri(ols_kumeli(ds['car3'], ds[['s']], kum))}")


def payda_kusuru():
    bas("8 · PAYDA: TMS 29 GEÇİŞİ 2024 KÖPRÜLERİNİ BOZUYOR")
    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        k = pd.read_sql(
            "select donem_sonu, ay_sayisi, percentile_cont(0.5) within group (order by katsayi)::float as k, "
            "count(*) as n from donem_buyume where katsayi is not null "
            "and donem_sonu in ('2024-09-30', '2024-12-31') and ay_sayisi in (9, 12) group by 1, 2", b)
        d = pd.read_sql(
            """select extract(year from t.donem_sonu)::int as yil, t.yontem,
                      (t.enflasyon_carpani is not null) as duzeltmeli,
                      avg(t.enflasyon_carpani)::float as carpan, count(*) as n,
                      min(a.yayin_zamani)::date as ilk, max(a.yayin_zamani)::date as son
               from akis a
               join lateral (select * from ttm_seri t where t.ticker = a.ticker
                             and t.gecerlilik_basi <= a.yayin_zamani
                             order by t.gecerlilik_basi desc limit 1) t on true
               where a.ciro_orani is not null
               group by 1, 2, 3 order by 1, 2, 3""", b)
    for _, r in k.iterrows():
        print(f"  k medyanı {r['donem_sonu']} ({r['ay_sayisi']} ay): {r['k']:.3f} (n={r['n']})")
    print("  9 aylık düzeltme (Ara 2023 → Eyl 2024) 12 aylıktan (Ara 2023 → Ara 2024) büyük olamaz;")
    print("  köprü 9A2024'te k^(9/12) uyguluyor. Skorlu bildirimlerin paydası:")
    for _, r in d.iterrows():
        c = f"çarpan ort {r['carpan']:.3f}" if r["duzeltmeli"] else "düzeltmesiz"
        print(f"    {r['yil']} {r['yontem']:<12} {c:<22} n={r['n']:>4}  {r['ilk']} → {r['son']}")


def marj_kesmesi(v, getiri, takvim):
    """±%10 marjı büyük tepkiyi günlere yayar: CAR3 onu kesiyor mu?"""
    bas("9 · FİYAT MARJI: TAVAN/TABAN SERİSİ TEPKİYİ 3 GÜNDEN TAŞIRIYOR MU?")
    ix = {g: i for i, g in enumerate(takvim)}
    satir = []
    for i, o in v.dropna(subset=["car3"]).iterrows():
        if o["t0"] not in ix or o["ticker"] not in getiri:
            continue
        i0 = ix[o["t0"]]
        g = getiri[o["ticker"]].reindex([takvim[j] for j in range(i0, min(i0 + 6, len(takvim)))])
        if g.isna().any() or len(g) < 6:
            continue
        satir.append((i, bool((g.iloc[:3] >= 0.095).any()), bool((g.iloc[:3] <= -0.095).any()),
                      float(g.iloc[3:].sum()), o["s"]))
    d = pd.DataFrame(satir, columns=["i", "tavan", "taban", "sonrasi", "s"]).set_index("i")
    print(f"  CAR3 penceresinde en az bir tavan (≥ %9,5): {int(d['tavan'].sum())} / {len(d)} "
          f"(%{d['tavan'].mean()*100:.1f}), taban: {int(d['taban'].sum())}")
    for ad, m in (("tavan görenler", d["tavan"]), ("görmeyenler", ~d["tavan"] & ~d["taban"])):
        x = d.loc[m, "sonrasi"]
        t = x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 else float("nan")
        print(f"  {ad:<16} n={len(x):>4}  [t0+3, t0+5] ham getiri ort {x.mean()*100:+.2f}%  t={t:+.2f}")
    s = d.dropna(subset=["s"])
    for ad, m in (("S ≥ 3", s["s"] >= 3), ("S < 1", s["s"] < 1)):
        print(f"  {ad:<6} tavan payı %{s.loc[m, 'tavan'].mean()*100:.1f} (n={int(m.sum())})")


LISTE_SON: date | None = None


def main() -> int:
    global LISTE_SON
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    olay, fiyat, endeks, ew, usd, k = yukle()
    takvim = list(endeks["tarih"])
    getiri = {t: g.set_index("tarih")["p"].sort_index().pct_change()
              for t, g in fiyat.groupby("ticker")}
    hacim = {t: g.set_index("tarih")["v"] for t, g in fiyat.groupby("ticker")}
    gunler = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 5]

    v = olay.dropna(subset=["t0"]).copy()
    print(f"olay (yayında, t0'lı): {len(v)} · CAR3'lü {v['car3'].notna().sum()} · "
          f"{v['ticker'].nunique()} hisse · {min(v['t0'])} → {max(v['t0'])}")

    rejim(olay, endeks, ew, usd, k)
    prof = olay_profili(v, hacim, takvim, gunler)
    pprof = piyasa_profili(v, piyasa_hacim_endeksi(fiyat), takvim, gunler)
    guc(v, prof)
    av_ihlal = sermaye_islemi(v, getiri, takvim, fiyat)
    piyasa_hacmi(v, prof, pprof, av_ihlal)
    liste = liste_tablosu()
    LISTE_SON = liste["gun"].max()
    karisan_bolumu(v, prof, pprof, karisan(v, liste, takvim))
    zaman_kumelenmesi(v)
    kararlilik(v, prof, pprof)
    payda_kusuru()
    marj_kesmesi(v, getiri, takvim)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
