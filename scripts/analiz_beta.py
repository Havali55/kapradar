"""Beta=1 varsayımı bize ne kaybettiriyor? (CAR metodolojisi denetimi)

Kullanım:  python scripts/analiz_beta.py

Şu an `tepki.car_hesapla` piyasa-düzeltilmiş getiri kullanıyor:
    anormal(t) = r_hisse(t) − r_xu100(t)
Bu, her hissenin betasının 1 olduğunu varsayar. BIST'te bu varsayım
sığ ve yüksek betalı tahtalarda kırılır: endeks %5 düşerken betası 1,6
olan hisse %8 düşer ve biz bunu "bildirime tepki" sanarız.

Varsayımın kırıldığı gün elimizde duruyor: **16 Eylül 2026**, Pusula ve
Tera Portföy fonlarının temerrüdüyle BIST 100 gün içinde %6'ya yakın
düştü, BIST Tüm'deki 584 hissenin 566'sı ekside kapandı. Örneklemimizin
son günleri bu krizin içinde.

Bu betik iki modeli yan yana koyuyor:
    piyasa-düzeltilmiş : r_i − r_m                (beta = 1 varsayımı)
    piyasa modeli      : r_i − (α + β·r_m)        (beta tahmin edilir)
"""

from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.depo import Depo  # noqa: E402
from kap_radar.tepki import t0_bul  # noqa: E402

# Piyasa çapında stres günü eşiği: endeksin günlük mutlak getirisi.
STRES_ESIGI = 0.03


def env_oku(yol: Path) -> dict[str, str]:
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def getiriler(seri: dict[date, float], gunler: list[date]) -> dict[date, float]:
    """Ardışık işlem günleri arasındaki getiri."""
    cikti = {}
    for sira in range(1, len(gunler)):
        bugun, dun = gunler[sira], gunler[sira - 1]
        if bugun in seri and dun in seri and seri[dun]:
            cikti[bugun] = seri[bugun] / seri[dun] - 1
    return cikti


def beta_tahmin(
    hisse: dict[date, float], piyasa: dict[date, float], haric: set[date]
) -> tuple[float, float, int]:
    """OLS ile α ve β. Olay pencereleri tahminden dışlanır.

    Dışlanmazsa bildirimin kendi tepkisi betayı şişirir ve model o
    tepkiyi "normal" sayıp anormal getiriyi küçültür.
    """
    ortak = [g for g in hisse if g in piyasa and g not in haric]
    if len(ortak) < 60:
        return 1.0, 0.0, len(ortak)
    x = np.array([piyasa[g] for g in ortak])
    y = np.array([hisse[g] for g in ortak])
    X = np.column_stack([np.ones_like(x), x])
    katsayi, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(katsayi[1]), float(katsayi[0]), len(ortak)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dsn = env_oku(KOK / ".env")["DATABASE_URL"]

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute("select min(tarih), max(tarih) from public.endeks_gunluk")
            ilk, son = imlec.fetchone()
            imlec.execute(
                "select b.kap_id, b.ticker, b.yayin_zamani, t.t0 "
                "from public.bildirim b join public.tepki t on t.kap_id = b.kap_id "
                "where b.ticker is not null and t.t0 is not null"
            )
            bildirimler = imlec.fetchall()

        endeks_seri = {g: float(v) for g, v in depo.endeks_serisi(ilk, son).items()}
        gunler = sorted(endeks_seri)
        piyasa = getiriler(endeks_seri, gunler)

        tickerlar = sorted({t for _, t, _, _ in bildirimler})
        seriler = {
            t: {g: float(v) for g, v in depo.fiyat_serisi(t, ilk, son).items()}
            for t in tickerlar
        }

    # --- piyasa stresi ---------------------------------------------------
    stres = {g for g, r in piyasa.items() if abs(r) > STRES_ESIGI}
    print("=" * 78)
    print("PİYASA STRESİ (|XU100 günlük getiri| > %3)")
    print("=" * 78)
    for gun in sorted(stres):
        print(f"  {gun}  XU100 {piyasa[gun]*100:+6.2f}%")
    print(f"  toplam {len(stres)} gün / {len(piyasa)} işlem günü")

    # --- beta dağılımı ---------------------------------------------------
    olay_gunleri: dict[str, set[date]] = {t: set() for t in tickerlar}
    for _, ticker, _, t0 in bildirimler:
        if t0 in endeks_seri:
            sira = gunler.index(t0)
            for adim in range(-1, 6):
                if 0 <= sira + adim < len(gunler):
                    olay_gunleri[ticker].add(gunler[sira + adim])

    betalar = {}
    for ticker in tickerlar:
        hisse_getiri = getiriler(seriler[ticker], gunler)
        betalar[ticker] = beta_tahmin(hisse_getiri, piyasa, olay_gunleri[ticker])

    beta_dizi = np.array([b for b, _, _ in betalar.values()])
    print("\n" + "=" * 78)
    print("BETA DAĞILIMI (olay pencereleri dışlanarak tahmin edildi)")
    print("=" * 78)
    print(
        f"  n={len(beta_dizi)}  ortalama={beta_dizi.mean():.2f}  "
        f"medyan={np.median(beta_dizi):.2f}  "
        f"%10={np.quantile(beta_dizi,0.1):.2f}  %90={np.quantile(beta_dizi,0.9):.2f}"
    )
    print(f"  beta > 1.3 olan hisse : {(beta_dizi > 1.3).sum()}")
    print(f"  beta < 0.7 olan hisse : {(beta_dizi < 0.7).sum()}")
    uc = sorted(betalar.items(), key=lambda x: x[1][0])
    print("  en düşük:", ", ".join(f"{t} {b:.2f}" for t, (b, _, _) in uc[:4]))
    print("  en yüksek:", ", ".join(f"{t} {b:.2f}" for t, (b, _, _) in uc[-4:]))

    # --- iki model yan yana ----------------------------------------------
    def car(ticker: str, t0: date, pencere: tuple[int, int], model: str):
        hisse_getiri = getiriler(seriler[ticker], gunler)
        beta, alfa, _ = betalar[ticker]
        if t0 not in endeks_seri:
            return None
        sira = gunler.index(t0)
        toplam = 0.0
        for adim in range(pencere[0], pencere[1] + 1):
            if not 0 < sira + adim < len(gunler):
                return None
            gun = gunler[sira + adim]
            if gun not in hisse_getiri or gun not in piyasa:
                return None
            if model == "duzeltilmis":
                toplam += hisse_getiri[gun] - piyasa[gun]
            else:
                toplam += hisse_getiri[gun] - (alfa + beta * piyasa[gun])
        return toplam

    eski, yeni, stresli = [], [], []
    for _, ticker, _, t0 in bildirimler:
        a = car(ticker, t0, (0, 2), "duzeltilmis")
        b = car(ticker, t0, (0, 2), "model")
        if a is None or b is None:
            continue
        eski.append(a)
        yeni.append(b)
        sira = gunler.index(t0)
        pencere_gunleri = {
            gunler[sira + adim]
            for adim in range(0, 3)
            if 0 <= sira + adim < len(gunler)
        }
        stresli.append(bool(pencere_gunleri & stres))

    eski_d, yeni_d = np.array(eski), np.array(yeni)
    fark = yeni_d - eski_d
    stresli_d = np.array(stresli)

    print("\n" + "=" * 78)
    print("İKİ MODEL YAN YANA (3 günlük pencere)")
    print("=" * 78)
    print(f"  n={len(eski_d)}")
    print(f"  piyasa-düzeltilmiş (beta=1) ortalama : {eski_d.mean()*100:+6.2f}%")
    print(f"  piyasa modeli (beta tahmini) ortalama: {yeni_d.mean()*100:+6.2f}%")
    print(f"  korelasyon                            : {np.corrcoef(eski_d, yeni_d)[0,1]:.3f}")
    print(f"  ortalama mutlak fark                  : {np.abs(fark).mean()*100:5.2f} puan")
    print(f"  işaret değiştiren bildirim            : {int(((eski_d>0)!=(yeni_d>0)).sum())}")
    print(f"  1 puandan fazla değişen               : {int((np.abs(fark)>0.01).sum())}")

    print("\n  Stres günü içeren pencereler:")
    for etiket, maske in (("stres VAR", stresli_d), ("stres YOK", ~stresli_d)):
        if maske.sum() == 0:
            continue
        print(
            f"    {etiket:10} n={int(maske.sum()):4}  "
            f"beta=1: {eski_d[maske].mean()*100:+6.2f}%  "
            f"model: {yeni_d[maske].mean()*100:+6.2f}%  "
            f"fark: {fark[maske].mean()*100:+5.2f} puan"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
