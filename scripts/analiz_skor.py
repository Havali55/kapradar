"""Skor bileşenlerinin kanıt tabanı: çok değişkenli analiz.

Kullanım:  python scripts/ozellik_kur.py && python scripts/analiz_skor.py

Soru şu: bir bildirimin piyasada yarattığı tepkiyi **önceden** neyin
öngördüğü. Tek değişkenli ortalamalar yanıltıcı, çünkü sinyaller
birbirine karışıyor (karşı tarafı açıklayan şirketler aynı zamanda daha
büyük ve daha likit olabilir). Bu yüzden hepsi aynı anda konuluyor.

Üç metodolojik önlem, üçü de BIST'in karakterinden doğuyor:

1. **Kümelenmiş standart hata.** 612 bildirim 111 şirkete ait; aynı
   şirketin bildirimleri bağımsız gözlem değil. Ticker düzeyinde
   kümelenmezse t değerleri olduğundan büyük çıkar.
2. **Kırpma (winsorize).** Tavan serisi yapan birkaç tahta ortalamayı
   tek başına taşıyabiliyor. Sonuçlar %1/%99'da kırpılmış hâliyle de
   raporlanıyor; ikisi ayrışıyorsa bulgu birkaç gözlemin eseridir.
3. **Dönem bölmesi.** İlk 6 ay ile son 6 ay ayrı ayrı. Bir katsayı iki
   yarıda da aynı yöne bakmıyorsa kalibrasyona girmemeli.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "data" / "ozellikler.csv"


def veri_oku() -> list[dict]:
    with VERI.open(encoding="utf-8") as dosya:
        return list(csv.DictReader(dosya))


def sayi(satir: dict, alan: str, varsayilan: float = 0.0) -> float:
    ham = satir.get(alan, "")
    return float(ham) if ham not in ("", None) else varsayilan


def winsorize(y: np.ndarray, oran: float = 0.01) -> np.ndarray:
    alt, ust = np.quantile(y, [oran, 1 - oran])
    return np.clip(y, alt, ust)


def ols(X: np.ndarray, y: np.ndarray, kume: np.ndarray | None = None):
    """Katsayılar + (kümelenmiş ya da heteroskedastisiteye dayanıklı) hata."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta

    if kume is None:
        orta = (X * (e**2)[:, None]).T @ X
        duzeltme = n / (n - k)
    else:
        orta = np.zeros((k, k))
        gruplar = np.unique(kume)
        for g in gruplar:
            maske = kume == g
            Xg, eg = X[maske], e[maske]
            skor = Xg.T @ eg
            orta += np.outer(skor, skor)
        G = len(gruplar)
        duzeltme = (G / (G - 1)) * ((n - 1) / (n - k))

    V = duzeltme * (XtX_inv @ orta @ XtX_inv)
    hata = np.sqrt(np.maximum(np.diag(V), 0))
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    return beta, hata, r2


def tablo(adlar, beta, hata, r2, n, baslik):
    print(f"\n{baslik}   (n={n}, R²={r2:.3f})")
    print(f"  {'değişken':26} {'katsayı':>10} {'std.hata':>10} {'t':>7}")
    for ad, b, h in zip(adlar, beta, hata):
        t = b / h if h else 0.0
        yildiz = "***" if abs(t) > 2.58 else "**" if abs(t) > 1.96 else "*" if abs(t) > 1.64 else ""
        print(f"  {ad:26} {b*100:+10.2f} {h*100:10.2f} {t:+7.2f} {yildiz}")


def tasarim(kayitlar: list[dict], hedef: str):
    """Tasarım matrisi. Ölçekler yüzde puan cinsinden okunabilir olsun diye
    sürekli değişkenler log ya da 0/1'e indirgeniyor."""
    adlar = [
        "sabit",
        "log10 günlük ciro (mn)",
        "karşı taraf açık",
        "güncelleme bildirimi",
        "tutar açıklanmış",
        "log1p tutar/ciro katı",
        "öncesi 5g sürüklenme",
        "VBTS son 5 günde",
        "log1p VBTS 90g",
        "içeriden işlem 5g",
        "sözleşme koşulu açık",
    ]
    satirlar, y, kume = [], [], []
    for k in kayitlar:
        hedef_deger = k.get(hedef, "")
        if hedef_deger in ("", None):
            continue
        ciro = sayi(k, "gunluk_ciro")
        satirlar.append(
            [
                1.0,
                math.log10(max(ciro, 1) / 1e6),
                sayi(k, "karsi_taraf_acik"),
                sayi(k, "guncelleme"),
                sayi(k, "tutar_var"),
                math.log1p(max(sayi(k, "tutar_ciro_kat"), 0)),
                sayi(k, "oncesi_5g"),
                1.0 if sayi(k, "vbts_yakin") > 0 else 0.0,
                math.log1p(sayi(k, "vbts_90g")),
                1.0 if sayi(k, "iceriden_yakin") > 0 else 0.0,
                sayi(k, "kosul_acik"),
            ]
        )
        y.append(float(hedef_deger))
        kume.append(k["ticker"])
    return adlar, np.array(satirlar), np.array(y), np.array(kume)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kayitlar = veri_oku()

    print("=" * 78)
    print("ÇOK DEĞİŞKENLİ ANALİZ — bağımlı değişken: 3 günlük anormal getiri")
    print("=" * 78)

    adlar, X, y, kume = tasarim(kayitlar, "car_3g")
    beta, hata, r2 = ols(X, y, kume)
    tablo(adlar, beta, hata, r2, len(y), "A · ticker düzeyinde kümelenmiş")

    beta_w, hata_w, r2_w = ols(X, winsorize(y), kume)
    tablo(adlar, beta_w, hata_w, r2_w, len(y), "B · %1 kırpılmış (aykırı değer testi)")

    # Tedbire düşmüş tahtaları tamamen dışarıda bırak
    temiz = [k for k in kayitlar if sayi(k, "vbts_yakin") == 0]
    adlar_t, Xt, yt, kt = tasarim(temiz, "car_3g")
    beta_t, hata_t, r2_t = ols(Xt, yt, kt)
    tablo(adlar_t, beta_t, hata_t, r2_t, len(yt), "C · son 5 günde VBTS görenler hariç")

    # Dönem bölmesi
    sirali = sorted(kayitlar, key=lambda k: k["tarih"])
    orta = len(sirali) // 2
    for etiket, altkume in (("D · ilk yarı", sirali[:orta]), ("E · ikinci yarı", sirali[orta:])):
        a, Xi, yi, ki = tasarim(altkume, "car_3g")
        b, h, r = ols(Xi, yi, ki)
        tablo(a, b, h, r, len(yi), f"{etiket} ({altkume[0]['tarih']} → {altkume[-1]['tarih']})")

    print("\n" + "=" * 78)
    print("AYNI MODEL, 1 GÜNLÜK TEPKİ")
    print("=" * 78)
    a1, X1, y1, k1 = tasarim(kayitlar, "car_1g")
    b1, h1, r1 = ols(X1, y1, k1)
    tablo(a1, b1, h1, r1, len(y1), "F · 1 gün")

    print("\n" + "=" * 78)
    print("TEDBİR YOĞUNLUĞUNA GÖRE HAM TEPKİ")
    print("=" * 78)
    vbts_degerleri = sorted(sayi(k, "vbts_90g") for k in kayitlar)
    esik1 = vbts_degerleri[len(vbts_degerleri) // 3]
    esik2 = vbts_degerleri[2 * len(vbts_degerleri) // 3]
    kovalar = {
        f"az tedbir (≤{esik1:.0f})": lambda k: sayi(k, "vbts_90g") <= esik1,
        f"orta ({esik1:.0f}–{esik2:.0f})": lambda k: esik1 < sayi(k, "vbts_90g") <= esik2,
        f"yoğun tedbir (>{esik2:.0f})": lambda k: sayi(k, "vbts_90g") > esik2,
    }
    for ad, kosul in kovalar.items():
        for alan in ("car_1g", "car_3g", "car_20g"):
            degerler = [sayi(k, alan, float("nan")) for k in kayitlar if kosul(k)]
            degerler = [d for d in degerler if not math.isnan(d)]
            if not degerler:
                continue
            dizi = np.array(degerler)
            sh = dizi.std(ddof=1) / math.sqrt(len(dizi))
            print(
                f"  {ad:22} {alan:7} n={len(dizi):4} "
                f"ort={dizi.mean()*100:+6.2f}%  sh=±{sh*100:4.2f}  "
                f"t={dizi.mean()/sh:+5.2f}  medyan={np.median(dizi)*100:+6.2f}%"
            )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
