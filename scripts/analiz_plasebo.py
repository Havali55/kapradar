"""D1-P · Plasebo, sıra ve standardize sınavlar: ölçüm aleti olay yokken ne ölçüyor?

Ön kayıt: docs/arastirma/2026-09-29-arastirma-haritasi.md §6 "D1-P" (tanımlar
ve karar kuralları P1–P5 sonuçlardan önce commit'lendi, `df9a7f8`). Hat ve
dönemler: K1 (`2026-09-28-k1-on-kayit.md`, `scripts/analiz_k1_rejim.py`).
Sonuç notu: docs/arastirma/2026-09-29-plasebo-ve-sira-sinavlari.md.

    python scripts/analiz_plasebo.py              # hat kontrolü, plasebo (kat 10), sıra/standardize sınavlar
    python scripts/analiz_plasebo.py --kat 5      # 30 dakika sınırı aşılırsa (ön kayıt)
    python scripts/analiz_plasebo.py --cikti DIZIN   # olay tablolarını pickle olarak DIZIN'e yaz

Yalnız okur: LLM yok, ücret yok, ağa çıkmaz, veritabanına yazmaz. Girdiler K1
ile aynı (bülten paneli `data/ham_rejim/panel.pkl`, KAP liste arşivleri).
Varsayılan koşu hiçbir dosya yazmaz.

Tanımlar içe aktarılıyor, kopyalanmıyor: K1 olay kurulumu ve ölçüleri
(`analiz_k1_rejim`), hacim profili ve karışan açıklama (`analiz_gecerlilik`),
beta ve Vasicek (`tepki`), pencereler (`skor_gecerlilik`). Tek istisna
`car3_dislamali`: K1'in `car3` akışı, beta tahmininden dışlanan günler
dışarıdan verilecek biçimde. Sahte olaylarda dışlanan, payın GERÇEK olay
pencereleri olmalı (ön kayıt); `k1.car3` dışlamayı kendi girdisinden
kurduğu için sahte olaylarla doğrudan çağrılamıyor. Gerçek olaylarda
`k1.car3` ile birebir aynı sonucu verdiği hat kontrolünde sınanıyor.

Bölümler: hat kontrolü (K1 rakamları tutmazsa durur), plasebo tabloları,
P1–P5 hükümleri, sıra ve standardize sınavlar. Sonda "SONRADAN" başlıklı üç
bölüm sonuçlar görüldükten sonra eklendi: ön kayıtta yok, hüküm kurallarına
girmez, yalnız betimleme (kota, beta kaynağı, sınavların plasebo altında
davranışı).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

import analiz_k1_rejim as k1  # noqa: E402
from analiz_gecerlilik import (  # noqa: E402
    KATEGORILER,
    hafta,
    karisan,
    olay_profili,
    ols_kumeli,
    piyasa_hacim_endeksi,
    piyasa_profili,
)
from kap_radar.backfill import YENI_IS_ILISKISI  # noqa: E402
from kap_radar.bulten import marj  # noqa: E402
from kap_radar.tepki import (  # noqa: E402
    BETA_GENIS_PENCERE,
    BETA_PENCERE,
    BETA_SICRAMA_ESIGI,
    BETA_TAMPON,
    BetaTahmini,
    _ols,
    beta_tahmin,
    t0_bul,
    vasicek_kucult,
)
from skor_gecerlilik import OLAY_PENCERE, TAHMIN_BAS, bas, yildiz  # noqa: E402

KAT = 10
TOHUM = 20260929
DISLAMA = 10  # payın her "Yeni İş İlişkisi" t0'ının [t0−10, t0+10] işlem günü
ANA_DONEMLER = ("A", "B", "C")
DONEMLER = k1.DONEMLER + (("7Y", "yedi yıl", k1.DONEMLER[0][2], k1.DONEMLER[-1][3]),)
AV_LOG_GUNLERI = (0, 1, 2)
MDE = k1.MDE_KATSAYI
KRITIK = 1.96
# Corrado-Zivney S_U: yalnız en az bu kadar olayın düştüğü olay-zamanı günleri.
SIRA_ASGARI_N = 30
# Kolari-Pynnönen: ρ_ij için en az bu kadar ortak tahmin günü.
KP_ASGARI_ORTAK = 30

# K1 notundaki rakamlar (2026-09-28-k1-rejim-sinamasi.md §4 H1, H3):
# (AV %, t, CAR3 puan, t). Hat bunları tutturmazsa plaseboya geçilmez.
K1_REFERANS = {
    "A": (28.9, 6.43, 1.66, 4.86),
    "A1": (29.1, 3.65, 1.27, 2.99),
    "A2": (28.7, 5.27, 1.88, 4.29),
    "B": (22.0, 3.28, 0.85, 1.74),
    "C": (38.8, 9.39, 0.72, 3.32),
}


# ------------------------------------------------------------- ölçüler

def pencereler_kur(olay, takvim) -> dict[str, set[date]]:
    """Payın gerçek olay pencereleri [t0, t0+2] (k1.car3'teki gibi)."""
    ix = {g: i for i, g in enumerate(takvim)}
    out: dict[str, set[date]] = {}
    for _, o in olay.iterrows():
        i0 = ix[o["t0"]]
        out.setdefault(o["ticker"], set()).update(takvim[i0: i0 + OLAY_PENCERE])
    return out


def car3_dislamali(olay, getiri, piyasa, takvim, pencereler) -> pd.DataFrame:
    """k1.car3 ile aynı akış; beta tahmininden dışlanan pencereler parametre.

    Çıktıya ham beta ve α da ekleniyor (sıra ve standardize sınavların
    tahmin penceresi kalıntıları için).
    """
    ix = {g: i for i, g in enumerate(takvim)}
    pz = piyasa.to_dict()
    sozluk: dict[str, dict] = {}
    tahmin: dict[int, BetaTahmini] = {}
    for i, o in olay.iterrows():
        s = getiri.get(o["ticker"])
        if s is None:
            continue
        sd = sozluk.setdefault(o["ticker"], s.to_dict())
        i0 = ix[o["t0"]]
        kendi = set(takvim[i0: i0 + OLAY_PENCERE])
        b = beta_tahmin(sd, pz, takvim, o["t0"], pencereler.get(o["ticker"], set()) - kendi)
        if b is not None:
            tahmin[i] = b
    satir = {}
    for kod, _, bas_g, son_g in k1.DONEMLER:
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
                        "beta": beta, "beta_kaynak": "olay" if i in kb else "capa",
                        "alfa": alfa, "beta_ham": tahmin[i].beta if i in tahmin else np.nan}
    return pd.DataFrame.from_dict(satir, orient="index")


def olcu_kur(olay, liste, takvim, marjlar, ham_getiri, adet, m, car) -> pd.DataFrame:
    """K1 main'in olay ölçüleri (AV, piyasaya göre AV, ön hacim, sermaye
    işlemi, CAR3, karışan açıklama) + ikincil AV_log."""
    prof = olay_profili(olay, adet, takvim, k1.PROFIL_GUNLERI)
    pprof = piyasa_profili(olay, m, takvim, k1.PROFIL_GUNLERI)
    v = olay.join(prof).join(pprof[["av"]].rename(columns={"av": "piyasa_av"}))
    v["av_duz"] = v["av"] - v["piyasa_av"]
    v["on_hacim"] = v[list(k1.ON_HACIM_GUNLERI)].mean(axis=1, skipna=False)
    # AV_log = ort_k [ln adet(t0+k)] − ln(medyan taban), k = 0, 1, 2. Sıfır
    # adetli gün, AV'de olduğu gibi düşer (profilde NaN).
    v["av_log"] = v[list(AV_LOG_GUNLERI)].mean(axis=1, skipna=True)
    v["sermaye_hacim"] = k1.marj_asan(olay, ham_getiri, marjlar, takvim, -TAHMIN_BAS, OLAY_PENCERE - 1)
    v["sermaye_car"] = k1.marj_asan(olay, ham_getiri, marjlar, takvim, 0, OLAY_PENCERE - 1)
    v = v.join(car)
    kar = karisan(olay, liste, takvim)
    once = [c for c in kar.columns if c.startswith("once ")]
    v["once_temiz"] = (kar[once].sum(axis=1) == 0).reindex(v.index)
    v["olay_temiz"] = (kar[list(KATEGORILER)].sum(axis=1) == 0).reindex(v.index)
    return v


# ------------------------------------------------------------- plasebo

def plasebo_kur(olay, liste, takvim, p, kat: int, tohum: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Her (pay, A/B/C) için gerçek olay sayısının `kat` katı rastgele işlem günü.

    Aday gün: dönem içinde, payın bültende satırı olan (listelenmiş) gün;
    payın herhangi bir "Yeni İş İlişkisi" bildiriminin t0'ına 10 işlem
    gününden yakın olmayan; dışlama penceresi arşivin kapsadığı günlerde
    (t0−10 panelde, t0+10 ≤ liste arşivinin son günü). Seçim iadesiz.
    """
    ix = {g: i for i, g in enumerate(takvim)}
    n_gun = len(takvim)
    liste_son = liste["gun"].max()
    yi = liste[(liste["konu"] == YENI_IS_ILISKISI) & liste["ticker"].isin(set(olay["ticker"]))]
    yasak: dict[str, set[int]] = {}
    for t, z in zip(yi["ticker"], yi["zaman"]):
        t0 = t0_bul(z, takvim)
        if t0 is None:
            continue
        i0 = ix[t0]
        yasak.setdefault(t, set()).update(range(i0 - DISLAMA, i0 + DISLAMA + 1))
    aralik = p.groupby("ticker")["tarih"].agg(["min", "max"])
    donem = {kod: (b, s) for kod, _, b, s in k1.DONEMLER if kod in ANA_DONEMLER}
    rng = np.random.default_rng(tohum)
    satir, ozet = [], []
    for t in sorted(olay["ticker"].unique()):
        ilk, son = ix[aralik.at[t, "min"]], ix[aralik.at[t, "max"]]
        for kod in ANA_DONEMLER:
            b, s = donem[kod]
            n = int(((olay["ticker"] == t) & (olay["gun"] >= b) & (olay["gun"] <= s)).sum())
            if n == 0:
                continue
            aday = [j for j in range(max(ilk, DISLAMA), min(son, n_gun - 1 - DISLAMA) + 1)
                    if b <= takvim[j] <= s and j not in yasak.get(t, ())
                    and takvim[j + DISLAMA] <= liste_son]
            k = min(kat * n, len(aday))
            sec = sorted(rng.choice(np.array(aday, dtype=int), size=k, replace=False)) if k else []
            for j in sec:
                satir.append((t, takvim[j], takvim[j], -1, kod))
            ozet.append((t, kod, n, kat * n, len(aday), k))
    pl = pd.DataFrame(satir, columns=["ticker", "gun", "t0", "kap_index", "donem"])
    return pl, pd.DataFrame(ozet, columns=["ticker", "donem", "gercek", "hedef", "aday", "cekilen"])


# ------------------------------------------------------------- sınavlar

def ortalama(d, kolon):
    return k1.ortalama(d, kolon)


def fark(gercek: pd.DataFrame, plasebo: pd.DataFrame, kolon: str):
    """ölçü ~ sabit + gerçek olay göstergesi; pay + ISO hafta iki yönlü kümeli.

    Dönüş (n gerçek, n sahte, net katsayı, t, SE) ya da None.
    """
    d = pd.concat([gercek.assign(_g=1.0), plasebo.assign(_g=0.0)], ignore_index=True)
    d = d[d[kolon].notna()]
    ng, ns = int((d["_g"] == 1).sum()), int((d["_g"] == 0).sum())
    if ng < 30 or ns < 30:
        return None
    k = {"hisse": d["ticker"].to_numpy(), "hafta": d["t0"].map(hafta).to_numpy()}
    b, t = ols_kumeli(d[kolon].to_numpy(float), d["_g"].to_numpy(float), k)["iki yönlü"]
    return ng, ns, b, t, abs(b / t) if t else float("nan")


def bicim(r, tur: str, mde: bool = False) -> str:
    """K1 satir_yaz biçimi: log ölçü exp(m) − 1 yüzde, CAR puan."""
    if r is None:
        return "—"
    m, t, se = r[2], r[3], r[4]
    if tur == "log%":
        s = f"{(math.exp(m) - 1) * 100:+.1f}% t {t:+.2f}{yildiz(t)}"
        return s + (f" (MDE {(math.exp(MDE * se) - 1) * 100:.1f}%)" if mde else "")
    s = f"{m * 100:+.2f}p t {t:+.2f}{yildiz(t)}"
    return s + (f" (MDE {MDE * se * 100:.2f}p)" if mde else "")


def hukum(r, ref, referans_donem: bool = False) -> str:
    """K1 karar kuralları; ref = C'deki (aynı ölçüyle) etki."""
    if r is None:
        return "yetersiz gözlem"
    b, t, se = r[2], r[3], r[4]
    if referans_donem:
        return "ayakta (referans)" if abs(t) >= KRITIK and b > 0 else "referans sıfırdan ayrılmıyor"
    ayni = np.sign(b) == np.sign(ref[2])
    if abs(t) >= KRITIK:
        return "tekrarlandı" if ayni else "tekrarlanmadı (ters işaret)"
    if MDE * se > abs(ref[2]):
        return "yön aynı, güç yetmedi" if ayni else "ters işaret, sonuçsuz (güç yetmedi)"
    return "tekrarlanmadı (MDE < C'deki etki; etki bu dönemde daha küçük)"


def z(a, b) -> float:
    if a is None or b is None:
        return float("nan")
    return (a[2] - b[2]) / math.sqrt(a[4] ** 2 + b[4] ** 2)


def hv(x):
    return x[~x["sermaye_hacim"].astype(bool)]


def cv(x):
    return x[~x["sermaye_car"].astype(bool)]


def temiz(x):
    return x[x["olay_temiz"] == True]  # noqa: E712


def plasebo_raporu(v: pd.DataFrame, pl: pd.DataFrame) -> dict:
    """Dönem başına gerçek, plasebo ve net; P1–P5 için gereken her şey."""
    olcular = (("AV", "av", hv, "log%"), ("AV, piyasaya göre", "av_duz", hv, "log%"),
               ("AV_log (ikincil)", "av_log", hv, "log%"), ("ön hacim [t0−4, t0−1]", "on_hacim", hv, "log%"),
               ("CAR3", "car3", cv, "p"))
    sonuc: dict = {}
    for kod, ad, b, s in DONEMLER:
        g, x = k1.donem_olaylari(v, b, s), k1.donem_olaylari(pl, b, s)
        bas(f"PLASEBO · {kod} · {ad.strip()} · gerçek {len(g)}, P-geniş {len(x)}, P-temiz {int((x['olay_temiz'] == True).sum())}")  # noqa: E712
        for oad, kol, suz, tur in olcular:
            rg, rp, rn = ortalama(suz(g), kol), ortalama(suz(x), kol), fark(suz(g), suz(x), kol)
            rpt = ortalama(temiz(suz(x)), kol)
            rgt = ortalama(temiz(suz(g)), kol)
            rnt = fark(temiz(suz(g)), temiz(suz(x)), kol)
            sonuc[(kod, kol)] = {"gercek": rg, "plasebo": rp, "net": rn, "plasebo_temiz": rpt,
                                 "gercek_temiz": rgt, "net_temiz": rnt}
            print(f"  {oad}")
            print(f"    gerçek {bicim(rg, tur):<28} P-geniş {bicim(rp, tur):<28} n {rn[0] if rn else '—'}/{rn[1] if rn else '—'}")
            print(f"    NET (gerçek − P-geniş) {bicim(rn, tur, mde=True)}")
            print(f"    temiz: gerçek {bicim(rgt, tur):<22} P-temiz {bicim(rpt, tur):<22} NET {bicim(rnt, tur, mde=True)}")
        # P5'in "değilse ayrıca yazılır" kısmı: K1 H2'nin temiz alt kümesi
        # (önceki 5 günde açıklama yok) plasebonun aynı alt kümesine karşı.
        og, ox = g[g["once_temiz"] == True], x[x["once_temiz"] == True]  # noqa: E712
        r, rg, rn = ortalama(hv(ox), "on_hacim"), ortalama(hv(og), "on_hacim"), fark(hv(og), hv(ox), "on_hacim")
        sonuc[(kod, "on_hacim_once_temiz")] = {"gercek": rg, "plasebo": r, "net": rn}
        print(f"  P5 · önceki 5 günde açıklama yok, ön hacim: gerçek {bicim(rg, 'log%')}  P-geniş {bicim(r, 'log%')}  "
              f"NET {bicim(rn, 'log%', mde=True)}")
    return sonuc


def hukumler(sonuc: dict, v: pd.DataFrame) -> None:
    bas("P1–P3 · HÜKÜMLER NETE GÖRE (K1 kuralları; referans C'nin net etkisi)")
    for kol, ad, tur in (("av", "H1 · AV", "log%"), ("av_duz", "H1 · AV, piyasaya göre", "log%"), ("car3", "H3 · CAR3", "p")):
        ref = sonuc[("C", kol)]["net"]
        print(f"  {ad}")
        for kod, _, _, _ in DONEMLER:
            r = sonuc[(kod, kol)]
            p = r["plasebo"]
            tetik = "P tetiklendi" if p and abs(p[3]) >= KRITIK else "P tetiklenmedi"
            h = hukum(r["net"], ref, referans_donem=(kod == "C")) if kod != "7Y" else (
                "ayakta" if r["net"] and abs(r["net"][3]) >= KRITIK else "sonuçsuz")
            print(f"    {kod:<3} ham {bicim(r['gercek'], tur):<26} plasebo {bicim(p, tur):<26} ({tetik})  "
                  f"net {bicim(r['net'], tur, mde=True):<40} → {h}")
    bas("H5 · TEMİZ ALT KÜME: gerçek temiz − P-temiz (referans C'nin temiz neti)")
    for kol, ad, tur in (("av", "AV", "log%"), ("car3", "CAR3", "p")):
        ref = sonuc[("C", kol)]["net_temiz"]
        print(f"  {ad}")
        for kod, _, _, _ in DONEMLER:
            r = sonuc[(kod, kol)]
            h = hukum(r["net_temiz"], ref, referans_donem=(kod == "C")) if kod != "7Y" else (
                "ayakta" if r["net_temiz"] and abs(r["net_temiz"][3]) >= KRITIK else "sonuçsuz")
            print(f"    {kod:<3} ham {bicim(r['gercek_temiz'], tur):<26} P-temiz {bicim(r['plasebo_temiz'], tur):<26} "
                  f"net {bicim(r['net_temiz'], tur, mde=True):<40} → {h}")

    bas("P2 · DÖNEM FARKLARI, z = (a − b) / √(se_a² + se_b²): K1 (ham) ve net")
    for kol, ad in (("av", "AV"), ("av_duz", "AV, piyasaya göre"), ("car3", "CAR3"), ("av_log", "AV_log")):
        g = {k: sonuc[(k, kol)]["gercek"] for k in ("A", "B", "C")}
        n = {k: sonuc[(k, kol)]["net"] for k in ("A", "B", "C")}
        print(f"  {ad:<18} ham C−A {z(g['C'], g['A']):+.2f}  C−B {z(g['C'], g['B']):+.2f}   |   "
              f"net C−A {z(n['C'], n['A']):+.2f}  C−B {z(n['C'], n['B']):+.2f}")
        f = lambda r: f"{r[2]:+.4f}" if r else "—"  # noqa: E731
        print(f"  {'':<18} net log/puan: A {f(n['A'])}  B {f(n['B'])}  C {f(n['C'])}")


# ------------------------------------------------ sıra ve standardize sınavlar

def tahmin_kalintilari(v, getiri, piyasa, takvim, pencereler) -> dict[int, dict]:
    """Olay başına tahmin penceresi kalıntıları ve olay penceresi AR'leri.

    Pencere `beta_tahmin`'in kullandığıyla aynı (120 gün, t0−10 tamponu,
    yetmezse 250; payın diğer olay pencereleri, eksik gün ve |r| ≥ %50
    dışlı). Kalıntı CAR3'ün modeliyle: e = r − α − β·r_m (β küçültülmüş,
    α ham OLS). Ham β ve α'nın bu günlerden yeniden çıktığı ve AR
    toplamının CAR3'e eşit olduğu her olayda denetleniyor.
    """
    ix = {g: i for i, g in enumerate(takvim)}
    pz = piyasa.to_dict()
    sozluk: dict[str, dict] = {}
    out = {}
    for i, o in v.iterrows():
        sd = sozluk.setdefault(o["ticker"], getiri[o["ticker"]].to_dict())
        i0 = ix[o["t0"]]
        haric = pencereler[o["ticker"]] - set(takvim[i0: i0 + OLAY_PENCERE])
        bit = i0 - BETA_TAMPON
        ilk = max(1, bit - BETA_PENCERE)
        if _ols(sd, pz, takvim[ilk:bit], haric) is None:
            ilk = max(1, bit - BETA_GENIS_PENCERE)
        gun = [j for j in range(ilk, bit) if takvim[j] in sd and takvim[j] in pz
               and takvim[j] not in haric and abs(sd[takvim[j]]) < BETA_SICRAMA_ESIGI]
        r = np.array([sd[takvim[j]] for j in gun])
        rm = np.array([pz[takvim[j]] for j in gun])
        bh = float(((rm - rm.mean()) * (r - r.mean())).sum() / ((rm - rm.mean()) ** 2).sum())
        ah = float(r.mean() - bh * rm.mean())
        assert abs(bh - o["beta_ham"]) < 1e-9 and abs(ah - o["alfa"]) < 1e-9, (i, bh, o["beta_ham"])
        ev = takvim[i0: i0 + OLAY_PENCERE]
        ar = np.array([sd[g] - o["alfa"] - o["beta"] * pz[g] for g in ev])
        assert abs(ar.sum() - o["car3"]) < 1e-12
        out[i] = {"ilk": ilk, "bit": bit, "gun": np.array(gun), "e": r - o["alfa"] - o["beta"] * rm,
                  "rm": rm, "ar": ar, "rm_ev": np.array([pz[g] for g in ev]), "i0": i0,
                  "ticker": o["ticker"]}
    return out


def isaret_sinavi(ids, K, car) -> tuple[float, float, int]:
    """Genelleştirilmiş işaret sınavı (Cowan 1992), 3 günlük CAR'a uyarlı.

    p̂ = olay başına, tahmin penceresinin örtüşmeyen 3 günlük bloklarında
    (pencere başından; üç günü de kalıntılı bloklar) pozitif CAR payının
    olaylar üzerinden ortalaması. Z = (w − N p̂) / √(N p̂ (1 − p̂)).
    """
    oran = []
    for i in ids:
        k = K[i]
        e = dict(zip(k["gun"].tolist(), k["e"].tolist()))
        blok = []
        for j in range(k["ilk"], k["bit"] - OLAY_PENCERE + 1, OLAY_PENCERE):
            if all(j + d in e for d in range(OLAY_PENCERE)):
                blok.append(sum(e[j + d] for d in range(OLAY_PENCERE)) > 0)
        if blok:
            oran.append(np.mean(blok))
    p = float(np.mean(oran))
    n = len(ids)
    w = int((car > 0).sum())
    return (w - n * p) / math.sqrt(n * p * (1 - p)), p, w


def sira_sinavi(ids, K) -> float:
    """Çok günlü sıra sınavı: Corrado (1989), Corrado-Zivney (1992)
    standartlaştırılmış sıraları ve Campbell-Wasley (1993) CAR uyarlaması.

    U_it = sıra(A_it) / (M_i + 1), A_it olayın tahmin kalıntıları ve üç olay
    günü AR'si birlikte (M_i gün). Olay-zamanı günü t için
    Z_t = Σ_i (U_it − ½) / √N_t. S_U² = ortalama_t Z_t² (N_t ≥ 30 olan
    tahmin günleri ve üç olay günü). T = (Z_0 + Z_1 + Z_2) / (√3 · S_U).
    """
    toplam: dict[int, float] = {}
    sayi: dict[int, int] = {}
    for i in ids:
        k = K[i]
        a = np.concatenate([k["e"], k["ar"]])
        poz = np.concatenate([k["gun"] - k["i0"], np.arange(OLAY_PENCERE)])
        u = pd.Series(a).rank(method="average").to_numpy() / (len(a) + 1) - 0.5
        for t, x in zip(poz.tolist(), u.tolist()):
            toplam[t] = toplam.get(t, 0.0) + x
            sayi[t] = sayi.get(t, 0) + 1
    zt = {t: toplam[t] / math.sqrt(sayi[t]) for t in toplam}
    kullan = [t for t in zt if t >= 0 or sayi[t] >= SIRA_ASGARI_N]
    s = math.sqrt(sum(zt[t] ** 2 for t in kullan) / len(kullan))
    return sum(zt[t] for t in range(OLAY_PENCERE)) / (math.sqrt(OLAY_PENCERE) * s)


def bmp(ids, K) -> tuple[float, np.ndarray]:
    """BMP (Boehmer, Musumeci, Poulsen 1991), CAR3 için.

    SCAR_i = CAR_i / S_i, S_i² = s_i² [L + L²/T_i + (Σ_τ (R_mτ − R̄_m))² / Σ_t (R_mt − R̄_m)²],
    s_i² = Σ e² / (T_i − 2), L = 3. t = ort(SCAR) / (ss(SCAR) / √N).
    """
    sc = []
    for i in ids:
        k = K[i]
        T = len(k["e"])
        s2 = float((k["e"] ** 2).sum() / (T - 2))
        rmo = k["rm"].mean()
        ssm = float(((k["rm"] - rmo) ** 2).sum())
        L = OLAY_PENCERE
        var = s2 * (L + L * L / T + float((k["rm_ev"] - rmo).sum()) ** 2 / ssm)
        sc.append(k["ar"].sum() / math.sqrt(var))
    sc = np.array(sc)
    return float(sc.mean() / (sc.std(ddof=1) / math.sqrt(len(sc)))), sc


def kp_rbar(ids, K) -> tuple[float, int, float, int]:
    """Kolari-Pynnönen (2010) düzeltmesinin r̄'si, olay tarihleri dağınık örnekleme uyarlı.

    r̄ = SCAR'lar arası ortalama korelasyon, bütün i ≠ j çiftleri üzerinden.
    Olay pencereleri çakışmayan çiftte 0 (AR'ler farklı günlerde). Çakışan
    çiftte (o_ij ortak olay günü, 1–3) (o_ij / 3) · ρ_ij; ρ_ij iki olayın
    tahmin kalıntılarının ortak takvim günlerindeki Pearson korelasyonu
    (≥ 30 ortak gün; yoksa geçerli ρ'ların ortalaması).
    Dönüş: (r̄, çakışan çift, çakışan çiftlerde ρ ortalaması, aynı paylı çakışan çift).
    """
    idx = sorted(ids, key=lambda i: K[i]["i0"])
    i0 = np.array([K[i]["i0"] for i in idx])
    cift, ayni = [], 0
    for a in range(len(idx)):
        b = a + 1
        while b < len(idx) and i0[b] - i0[a] < OLAY_PENCERE:
            ka, kb = K[idx[a]], K[idx[b]]
            o = OLAY_PENCERE - (i0[b] - i0[a])
            ortak, pa, pb = np.intersect1d(ka["gun"], kb["gun"], return_indices=True)
            r = float(np.corrcoef(ka["e"][pa], kb["e"][pb])[0, 1]) if len(ortak) >= KP_ASGARI_ORTAK else np.nan
            cift.append((o, r))
            ayni += ka["ticker"] == kb["ticker"]
            b += 1
    n = len(idx)
    if not cift:
        return 0.0, 0, float("nan"), 0
    gecerli = [r for _, r in cift if np.isfinite(r)]
    ort = float(np.mean(gecerli)) if gecerli else 0.0
    toplam = sum(o / OLAY_PENCERE * (r if np.isfinite(r) else ort) for o, r in cift)
    return 2 * toplam / (n * (n - 1)), len(cift), ort, ayni


K1_HUKUM_H3 = {"A": "tekrarlandı", "A1": "tekrarlandı", "A2": "tekrarlandı",
               "B": "yön aynı, güç yetmedi", "C": "referans (t 3,32)", "7Y": "keşif (t 5,26)"}
K1_HUKUM_H5 = {"A": "ayakta", "A1": "sonuçsuz", "A2": "ayakta", "B": "sonuçsuz",
               "C": "sonuçsuz", "7Y": "ayakta"}


def batarya(d: pd.DataFrame, K: dict) -> dict:
    """Bir alt örneklemde dört sınav; d kendi betası olan, CAR3'lü olaylar."""
    ids = list(d.index)
    n = len(ids)
    gz, ph, _ = isaret_sinavi(ids, K, d["car3"])
    tb, _ = bmp(ids, K)
    rbar, nc, rho, ay = kp_rbar(ids, K)
    return {"n": n, "gz": gz, "ph": ph, "rk": sira_sinavi(ids, K), "tb": tb, "rbar": rbar, "nc": nc,
            "rho": rho, "ay": ay, "tkp": tb * math.sqrt((1 - rbar) / (1 + (n - 1) * rbar)),
            "kum": ortalama(d, "car3")}


def sira_raporu(v, getiri, piyasa, takvim, pencereler) -> None:
    c = cv(v)
    c = c[c["car3"].notna()]
    ornek = c[c["beta_kaynak"] == "olay"]
    bas(f"SIRA VE STANDARDİZE SINAVLAR · CAR3 · kendi betası olan {len(ornek)} / {len(c)} olay "
        f"(çapa betalı {len(c) - len(ornek)} olay tahmin penceresi olmadığından dışarıda)")
    K = tahmin_kalintilari(ornek, getiri, piyasa, takvim, pencereler)
    T = np.array([len(k["e"]) for k in K.values()])
    print(f"  tahmin günü: medyan {np.median(T):.0f}, en az {T.min()}, 250 günlük pencereye düşen "
          f"{sum(1 for k in K.values() if k['bit'] - k['ilk'] > BETA_PENCERE)}")
    for alt, suz, k1h in (("tam", lambda x: x, K1_HUKUM_H3), ("H5 temiz", temiz, K1_HUKUM_H5)):
        print(f"\n  {alt}: n | ort | medyan | pozitif | K1 t (tam örneklem / bu alt örneklem) | "
              f"işaret Z (p̂) | sıra T | BMP t | r̄ (çakışan çift, ρ ort.) | KP-BMP t | hüküm")
        for kod, _, b, s in DONEMLER:
            tam = suz(k1.donem_olaylari(c, b, s))
            d = suz(k1.donem_olaylari(ornek, b, s))
            if len(d) < 30:
                print(f"  {kod:<3} yetersiz")
                continue
            rt, r = ortalama(tam, "car3"), batarya(d, K)
            h = k1h[kod]
            if h in ("tekrarlandı", "ayakta") or kod in ("C", "7Y") and alt == "tam":
                ek = "standardize sınavda zayıflıyor" if abs(r["tkp"]) < KRITIK else "KP-BMP destekliyor"
            else:
                ek = "hüküm değişmez (asimetri)"
            print(f"  {kod:<3} {r['n']:>5} | {d['car3'].mean() * 100:+.2f}p | {d['car3'].median() * 100:+.2f}p | "
                  f"%{(d['car3'] > 0).mean() * 100:.1f} | {rt[3]:+.2f} / {r['kum'][3]:+.2f} | {r['gz']:+.2f} ({r['ph']:.3f}) | "
                  f"{r['rk']:+.2f} | {r['tb']:+.2f} | {r['rbar']:.5f} ({r['nc']}, {r['rho']:.3f}, aynı pay {r['ay']}) | "
                  f"{r['tkp']:+.2f} | {h} → {ek}")


# ------------------------------------ sonradan eklenen betimlemeler (hükme girmez)

def sonradan(v, pv, oz, getiri, piyasa, takvim, pencereler) -> None:
    """Sonuçlar görüldükten sonra eklendi; ön kayıtta yok, hüküm kurallarına girmez.

    1. Kota: sık bildirim yapan paylarda 10 kat için aday gün yetmedi.
       Kotası dolan (pay, dönem) çiftleriyle sınırlı net (bileşim eşit).
    2. Beta kaynağına göre CAR3: kendi betası olan ve çapa betalı (α = 0)
       olaylar, gerçek ve plasebo ayrı ayrı.
    3. Standardize sınavların plasebo altında davranışı (boyut denetimi).
    """
    bas("SONRADAN 1 · KOTASI DOLAN (PAY, DÖNEM) ÇİFTLERİYLE NET (betimleme, hüküm değil)")
    dolu = set(zip(oz.loc[oz["cekilen"] == oz["hedef"], "ticker"], oz.loc[oz["cekilen"] == oz["hedef"], "donem"]))
    etiket = pd.Series(index=v.index, dtype=object)
    for kod, _, b, s in k1.DONEMLER:
        if kod in ANA_DONEMLER:
            etiket[(v["gun"] >= b) & (v["gun"] <= s)] = kod
    vd = v[[(t, d) in dolu for t, d in zip(v["ticker"], etiket)]]
    pd_ = pv[[(t, d) in dolu for t, d in zip(pv["ticker"], pv["donem"])]]
    print(f"  kotası dolan çift {len(dolu)} / {len(oz)}; gerçek olay {len(vd)} / {len(v)}, sahte {len(pd_)} / {len(pv)}")
    for kod, _, b, s in DONEMLER:
        g, x = k1.donem_olaylari(vd, b, s), k1.donem_olaylari(pd_, b, s)
        sat = []
        for kol, suz, tur in (("av", hv, "log%"), ("car3", cv, "p"), ("on_hacim", hv, "log%")):
            sat.append(f"{kol} plasebo {bicim(ortalama(suz(x), kol), tur)} net {bicim(fark(suz(g), suz(x), kol), tur)}")
        print(f"  {kod:<3} " + " | ".join(sat))

    bas("SONRADAN 2 · BETA KAYNAĞINA GÖRE CAR3 (betimleme, hüküm değil)")
    for kod, _, b, s in DONEMLER:
        g, x = cv(k1.donem_olaylari(v, b, s)), cv(k1.donem_olaylari(pv, b, s))
        sat = []
        for kay in ("olay", "capa"):
            gg, xx = g[g["beta_kaynak"] == kay], x[x["beta_kaynak"] == kay]
            f = lambda d: bicim(ortalama(d, "car3"), "p") if len(d[d["car3"].notna()]) >= 30 else (  # noqa: E731
                f"{d['car3'].mean() * 100:+.2f}p (n {int(d['car3'].notna().sum())})")
            sat.append(f"{kay}: gerçek {f(gg)} plasebo {f(xx)} net {bicim(fark(gg, xx, 'car3'), 'p')}")
        print(f"  {kod:<3} " + " | ".join(sat))

    c = cv(pv)
    c = c[c["car3"].notna() & (c["beta_kaynak"] == "olay")]
    bas(f"SONRADAN 3 · STANDARDİZE SINAVLAR PLASEBO ALTINDA · kendi betası olan {len(c)} sahte olay (betimleme)")
    K = tahmin_kalintilari(c, getiri, piyasa, takvim, pencereler)
    print("  dönem: n | ort | pozitif | kümeli t | işaret Z (p̂) | sıra T | BMP t | r̄ | KP-BMP t")
    for kod, _, b, s in DONEMLER:
        d = k1.donem_olaylari(c, b, s)
        r = batarya(d, K)
        print(f"  {kod:<3} {r['n']:>6} | {d['car3'].mean() * 100:+.2f}p | %{(d['car3'] > 0).mean() * 100:.1f} | "
              f"{r['kum'][3]:+.2f} | {r['gz']:+.2f} ({r['ph']:.3f}) | {r['rk']:+.2f} | {r['tb']:+.2f} | "
              f"{r['rbar']:.5f} | {r['tkp']:+.2f}")


# ------------------------------------------------------------------- ana

def hat_kontrolu(v, olay, getiri, piyasa, takvim, pencereler) -> bool:
    bas("HAT KONTROLÜ · K1 olay rakamları içe aktarılan tanımlarla")
    ref_car = k1.car3(olay, getiri, piyasa, takvim)
    ortak = ref_car.index
    fark_car = (ref_car["car3"] - v.loc[ortak, "car3"]).abs().max()
    fark_beta = (ref_car["beta"] - v.loc[ortak, "beta"]).abs().max()
    ayni = (len(ref_car) == int(v["car3"].notna().sum())
            and (ref_car["beta_kaynak"] == v.loc[ortak, "beta_kaynak"]).all())
    print(f"  car3_dislamali ile k1.car3: olay {len(ref_car)}, azami fark CAR3 {fark_car:.1e}, beta {fark_beta:.1e}, "
          f"kaynak aynı {ayni}")
    tamam = ayni and fark_car < 1e-12 and fark_beta < 1e-12
    for kod, _, b, s in k1.DONEMLER:
        d = k1.donem_olaylari(v, b, s)
        a, c = ortalama(hv(d), "av"), ortalama(cv(d), "car3")
        bul = (round((math.exp(a[2]) - 1) * 100, 1), round(a[3], 2), round(c[2] * 100, 2), round(c[3], 2))
        esit = bul == K1_REFERANS[kod]
        tamam &= esit
        print(f"  {kod:<3} AV +%{bul[0]:.1f} t {bul[1]:.2f} (n {a[0]})  CAR3 {bul[2]:+.2f} t {bul[3]:.2f} (n {c[0]})  "
              f"K1 {K1_REFERANS[kod]}  {'TUTUYOR' if esit else 'TUTMUYOR'}")
    return tamam


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--kat", type=int, default=KAT, help="pay başına sahte olay = kat × gerçek olay")
    ap.add_argument("--cikti", type=Path, default=None, help="olay tablolarını pickle olarak bu dizine yaz")
    args = ap.parse_args()
    bas_zaman = time.time()

    p = k1.panel_yukle()
    takvim = sorted(p["tarih"].unique())
    marjlar = {g: marj(g) for g in takvim}
    liste = k1.liste_tablosu()
    getiri, ham_getiri, adet, piyasa = k1.seriler(p)
    olay = k1.olaylar_kur(liste, takvim, set(adet))
    m = piyasa_hacim_endeksi(p.rename(columns={"adet": "v"})[["ticker", "tarih", "v"]])
    pencereler = pencereler_kur(olay, takvim)
    print(f"panel {len(p):,} pay-günü, {len(takvim)} işlem günü; olay {len(olay)}; liste arşivi son gün {liste['gun'].max()}")

    v = olcu_kur(olay, liste, takvim, marjlar, ham_getiri, adet, m,
                 car3_dislamali(olay, getiri, piyasa, takvim, pencereler))
    if not hat_kontrolu(v, olay, getiri, piyasa, takvim, pencereler):
        print("\nHAT TUTMUYOR: plaseboya geçilmiyor.")
        return 1
    print(f"  hat tamam ({time.time() - bas_zaman:.0f} sn)")

    pl, oz = plasebo_kur(olay, liste, takvim, p, args.kat, TOHUM)
    bas(f"PLASEBO · kat {args.kat}, tohum {TOHUM}")
    print(f"  sahte olay {len(pl)} (hedef {int(oz['hedef'].sum())}); aday gün yetmeyen (pay, dönem) "
          f"{int((oz['aday'] < oz['hedef']).sum())} / {len(oz)}, eksik {int((oz['hedef'] - oz['cekilen']).sum())}")
    pv = olcu_kur(pl, liste, takvim, marjlar, ham_getiri, adet, m,
                  car3_dislamali(pl, getiri, piyasa, takvim, pencereler))
    for ad, x in (("gerçek", v), ("P-geniş", pv)):
        print(f"  {ad:<8} n {len(x)}; AV'li {int(hv(x)['av'].notna().sum())}, CAR3'lü {int(cv(x)['car3'].notna().sum())}, "
              f"sermaye (hacim/CAR) {int(x['sermaye_hacim'].sum())}/{int(x['sermaye_car'].sum())}, "
              f"çapa betalı {int((x['beta_kaynak'] == 'capa').sum())}, olay_temiz %{(x['olay_temiz'] == True).mean() * 100:.1f}")  # noqa: E712
    print(f"  plasebo ölçüleri tamam ({time.time() - bas_zaman:.0f} sn)")
    if args.cikti:
        args.cikti.mkdir(parents=True, exist_ok=True)
        v.drop(columns=["zaman"]).to_pickle(args.cikti / "gercek.pkl")
        pv.to_pickle(args.cikti / "plasebo.pkl")
        oz.to_pickle(args.cikti / "plasebo_ozet.pkl")

    sonuc = plasebo_raporu(v, pv)
    hukumler(sonuc, v)
    sira_raporu(v, getiri, piyasa, takvim, pencereler)
    sonradan(v, pv, oz, getiri, piyasa, takvim, pencereler)
    print(f"\nsüre {time.time() - bas_zaman:.0f} sn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
