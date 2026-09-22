"""Öneri 4: Modül C piyasa modeline geçsin mi? (öncesi/sonrası)

Kullanım:  python scripts/analiz_piyasa_modeli.py

**Hiçbir şey yazmaz.** Tek işi iki modeli yan yana koymak:

    beta=1 (şu anki)  : anormal(t) = r_i(t) − r_m(t)
    piyasa modeli     : anormal(t) = r_i(t) − (α + β·r_m(t))

`analiz_beta.py`'den farkı **dinamik beta**: orada her hisse için tüm
örneklemden tek bir β tahmin ediliyordu. Burada her bildirim kendi
geçmişine bakıyor ve tahmin penceresi **t0'dan 11 işlem günü önce
bitiyor**.

Neden 11: Adım 16 sızıntı bulgusu. İşlem hacmi t0−4 ile t0−1 arasında
zaten %10–14 yüksek ve hepsi anlamlı, yani bildirim öncesi günler
"normal" değil. O günleri tahmine katmak betayı olayın kendisiyle
kirletir ve model gerçek tepkiyi "beklenen" sayıp küçültür.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402

# --- tahmin penceresi -------------------------------------------------
# Sızıntı tamponu: tahmin penceresi t0'dan bu kadar işlem günü önce biter.
TAMPON = 10
# Tahmin penceresinin uzunluğu (işlem günü). 120 gün olay çalışmalarında
# standart; 250'ye genişletme yalnız gözlem yetmezse devreye giriyor.
PENCERE = 120
GENIS_PENCERE = 250
ASGARI_GOZLEM = 60

# Düzeltilmemiş sermaye işlemi filtresi. `auto_adjust` BIST bedelsizlerini
# düzeltmiyor (HRKET 87,9 → 6,15). Tahmin penceresine girerse betayı
# tümüyle bozar. Eşik CAR'daki `sicrama_gunleri` ile aynı.
SICRAMA_ESIGI = 0.50

# Piyasa stresi eşiği — 2026-09-16 Pusula/Tera krizi bu kapsamda.
STRES_ESIGI = 0.03

PENCERE_CAR = (0, 2)


def getiriler(seri: dict[date, float], gunler: list[date]) -> dict[date, float]:
    cikti: dict[date, float] = {}
    for sira in range(1, len(gunler)):
        bugun, dun = gunler[sira], gunler[sira - 1]
        if bugun in seri and dun in seri and seri[dun]:
            cikti[bugun] = seri[bugun] / seri[dun] - 1
    return cikti


def beta_tahmin(
    hisse_getiri: dict[date, float],
    piyasa: dict[date, float],
    pencere_gunleri: list[date],
    haric: set[date],
) -> tuple[float, float, int, float, float] | None:
    """(β, α, n, R², se_β) — yetersiz gözlemde None.

    `haric`: aynı hissenin DİĞER bildirimlerinin olay pencereleri.
    Dışlanmazsa sık bildirimcilerde tahmin penceresi olay günleriyle
    dolar ve model tepkiyi "normal" saymaya başlar.

    `se_β` Vasicek küçültmesi için: gürültülü tahminler ortalamaya daha
    çok çekilsin diye tahminin kendi belirsizliği taşınıyor.
    """
    ortak = [
        g
        for g in pencere_gunleri
        if g in hisse_getiri
        and g in piyasa
        and g not in haric
        and abs(hisse_getiri[g]) < SICRAMA_ESIGI
    ]
    if len(ortak) < ASGARI_GOZLEM:
        return None

    x = np.array([piyasa[g] for g in ortak])
    y = np.array([hisse_getiri[g] for g in ortak])
    X = np.column_stack([np.ones_like(x), x])
    katsayi, *_ = np.linalg.lstsq(X, y, rcond=None)
    alfa, beta = float(katsayi[0]), float(katsayi[1])

    tahmin = alfa + beta * x
    ss_kalan = float(((y - tahmin) ** 2).sum())
    ss_toplam = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_kalan / ss_toplam if ss_toplam > 0 else 0.0

    serbestlik = len(ortak) - 2
    sx = float(((x - x.mean()) ** 2).sum())
    se = float(np.sqrt((ss_kalan / serbestlik) / sx)) if serbestlik > 0 and sx > 0 else 1.0
    return beta, alfa, len(ortak), r2, se


def ozet(ad: str, dizi: np.ndarray) -> str:
    return (
        f"  {ad:<26} n={len(dizi):4}  ort={dizi.mean()*100:+6.2f}%  "
        f"medyan={np.median(dizi)*100:+6.2f}%  std={dizi.std()*100:5.2f}%"
    )


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--pencere", type=int, default=PENCERE, help="tahmin penceresi (işlem günü)"
    )
    secenek = ayristirici.parse_args(argv)

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute("select min(tarih), max(tarih) from public.endeks_gunluk")
            ilk, son = imlec.fetchone()
            imlec.execute(
                "select b.kap_id, b.ticker, t.t0, t.car_3g, "
                "       c.etki_skoru, td.bayrak "
                "from public.bildirim b "
                "join public.tepki t on t.kap_id = b.kap_id "
                "left join lateral ("
                "  select etki_skoru from public.cikarim c2 "
                "  where c2.kap_id = b.kap_id order by id desc limit 1"
                ") c on true "
                "left join public.tahta_durumu td on td.kap_id = b.kap_id "
                "where t.t0 is not null"
            )
            bildirimler = imlec.fetchall()

        endeks = {g: float(v) for g, v in depo.endeks_serisi(ilk, son).items()}
        gunler = sorted(endeks)
        piyasa = getiriler(endeks, gunler)
        tickerlar = sorted({b[1] for b in bildirimler})
        seriler = {
            t: {g: float(v) for g, v in depo.fiyat_serisi(t, ilk, son).items()}
            for t in tickerlar
        }

    print("=" * 74)
    print("VERİ")
    print("=" * 74)
    print(f"  fiyat serisi   : {ilk} → {son} ({len(gunler)} işlem günü)")
    print(f"  bildirim       : {len(bildirimler)} (t0 dolu)")
    print(f"  tahmin penceresi: {secenek.pencere} gün, t0−{TAMPON}'da bitiyor")
    print(f"  asgari gözlem  : {ASGARI_GOZLEM}")

    hisse_getirileri = {t: getiriler(seriler[t], gunler) for t in tickerlar}
    sira_no = {g: i for i, g in enumerate(gunler)}

    # Aynı hissenin tüm olay pencereleri — tahminden dışlanacak.
    olay_gunleri: dict[str, set[date]] = {t: set() for t in tickerlar}
    for _, ticker, t0, *_ in bildirimler:
        if t0 in sira_no:
            i = sira_no[t0]
            for adim in range(0, 3):
                if i + adim < len(gunler):
                    olay_gunleri[ticker].add(gunler[i + adim])

    stres = {g for g, r in piyasa.items() if abs(r) > STRES_ESIGI}

    # --- 1. geçiş: her bildirim için beta tahmini ---------------------
    kayitlar = []
    yetersiz = 0
    for kap_id, ticker, t0, kayitli_car, skor, bayrak in bildirimler:
        if t0 not in sira_no:
            continue
        i = sira_no[t0]
        bit = i - TAMPON
        bas = max(1, bit - secenek.pencere)
        if bit - bas < ASGARI_GOZLEM:
            yetersiz += 1
            continue

        tahmin = beta_tahmin(
            hisse_getirileri[ticker], piyasa, gunler[bas:bit], olay_gunleri[ticker]
        )
        if tahmin is None:
            # Dar pencere yetmedi: geniş pencereyi dene.
            tahmin = beta_tahmin(
                hisse_getirileri[ticker],
                piyasa,
                gunler[max(1, bit - GENIS_PENCERE) : bit],
                olay_gunleri[ticker],
            )
        if tahmin is None:
            yetersiz += 1
            continue
        kayitlar.append((ticker, t0, i, kayitli_car, skor, bayrak, tahmin))

    if not kayitlar:
        print("Tahmin edilebilen bildirim yok.", file=sys.stderr)
        return 1

    # --- Vasicek küçültmesi -------------------------------------------
    # Ham OLS betaları çok gürültülü (R² medyanı düşük): negatif betalar
    # gerçek bir korunma özelliği değil, örneklem gürültüsü. Vasicek her
    # tahmini kendi belirsizliğiyle orantılı olarak ortalamaya çekiyor —
    # iyi ölçülmüş beta yerinde kalır, kötü ölçülmüş olan ortalamaya
    # yaklaşır.
    #
    # Çapası 1,0 DEĞİL evrenin kendi ortalaması: bu evrende beta 1'in
    # belirgin biçimde altında (Adım 16: ort. 0,79) ve 1'e çekmek
    # ölçtüğümüz gerçeği geri silerdi.
    ham_betalar = np.array([k[6][0] for k in kayitlar])
    seler = np.array([k[6][4] for k in kayitlar])
    capa = float(ham_betalar.mean())
    kesit_var = float(ham_betalar.var()) - float((seler**2).mean())
    kesit_var = max(kesit_var, 1e-6)
    agirliklar = kesit_var / (kesit_var + seler**2)

    print(f"\n  Vasicek çapası (evren ort. β) : {capa:.3f}")
    print(f"  kesit varyansı                : {kesit_var:.4f}")
    print(f"  ortalama ağırlık (1=ham OLS)  : {agirliklar.mean():.3f}")

    # --- 2. geçiş: üç model ------------------------------------------
    eski, yeni, kucuk, betalar, kucuk_betalar = [], [], [], [], []
    r2ler, gozlemler, kademeler, tahtalar, stresli, kimlik = [], [], [], [], [], []
    dogrulama_sapmasi = 0

    for sira, (ticker, t0, i, kayitli_car, skor, bayrak, tahmin) in enumerate(
        kayitlar
    ):
        beta, alfa, n_gozlem, r2, _ = tahmin
        beta_k = float(agirliklar[sira] * beta + (1 - agirliklar[sira]) * capa)

        a = b = c = 0.0
        gecerli = True
        for adim in range(PENCERE_CAR[0], PENCERE_CAR[1] + 1):
            j = i + adim
            if not 0 < j < len(gunler):
                gecerli = False
                break
            gun = gunler[j]
            ri = hisse_getirileri[ticker].get(gun)
            rm = piyasa.get(gun)
            if ri is None or rm is None or abs(ri) >= SICRAMA_ESIGI:
                gecerli = False
                break
            a += ri - rm
            b += ri - (alfa + beta * rm)
            c += ri - (alfa + beta_k * rm)
        if not gecerli:
            continue

        # Yeniden ürettiğimiz beta=1 CAR'ı kayıtlı değerle karşılaştır:
        # tutmuyorsa karşılaştırmanın tamamı şüphelidir.
        if kayitli_car is not None and abs(float(kayitli_car) - a) > 0.0005:
            dogrulama_sapmasi += 1

        eski.append(a)
        yeni.append(b)
        kucuk.append(c)
        kimlik.append((ticker, t0))
        betalar.append(beta)
        kucuk_betalar.append(beta_k)
        r2ler.append(r2)
        gozlemler.append(n_gozlem)
        kademeler.append(
            None
            if skor is None
            else ("mega" if skor >= 3.5 else "onemli" if skor >= 2.5 else "rutin")
        )
        tahtalar.append(bayrak)
        pencere_gun = {
            gunler[i + adim] for adim in range(0, 3) if i + adim < len(gunler)
        }
        stresli.append(bool(pencere_gun & stres))

    eski_d = np.array(eski)
    yeni_d = np.array(yeni)
    kucuk_d = np.array(kucuk)
    beta_d = np.array(betalar)
    beta_k_d = np.array(kucuk_betalar)
    fark = yeni_d - eski_d
    fark_k = kucuk_d - eski_d

    print(f"  hesaplanan     : {len(eski_d)}   yetersiz geçmiş: {yetersiz}")
    if dogrulama_sapmasi:
        print(
            f"  !! beta=1 yeniden üretimi {dogrulama_sapmasi} bildirimde "
            "kayıtlı car_3g ile tutmuyor"
        )
    else:
        print("  beta=1 yeniden üretimi kayıtlı car_3g ile birebir tutuyor")

    print("\n" + "=" * 74)
    print("DİNAMİK BETA DAĞILIMI")
    print("=" * 74)
    print(
        f"  ortalama={beta_d.mean():.3f}  medyan={np.median(beta_d):.3f}  "
        f"std={beta_d.std():.3f}"
    )
    print(
        f"  %10={np.quantile(beta_d,0.1):.2f}  %90={np.quantile(beta_d,0.9):.2f}  "
        f"min={beta_d.min():.2f}  max={beta_d.max():.2f}"
    )
    print(
        f"  beta<0,7: {(beta_d<0.7).sum()}   0,7–1,3: "
        f"{((beta_d>=0.7)&(beta_d<=1.3)).sum()}   beta>1,3: {(beta_d>1.3).sum()}"
    )
    print(f"  NEGATİF beta: {(beta_d<0).sum()}  (gürültü işareti)")
    r2_d = np.array(r2ler)
    print(
        f"  R² medyan={np.median(r2_d):.3f}  "
        f"gözlem medyan={int(np.median(gozlemler))}"
    )
    print(
        f"\n  küçültülmüş β: ort={beta_k_d.mean():.3f}  "
        f"medyan={np.median(beta_k_d):.3f}  std={beta_k_d.std():.3f}  "
        f"negatif={(beta_k_d<0).sum()}"
    )

    print("\n" + "=" * 74)
    print("CAR(3 GÜN) — ÜÇ MODEL")
    print("=" * 74)
    print(ozet("A · beta=1 (şu anki)", eski_d))
    print(ozet("B · ham piyasa modeli", yeni_d))
    print(ozet("C · küçültülmüş (Vasicek)", kucuk_d))
    print(f"\n  {'':<26} {'B (ham)':>10} {'C (küçült)':>12}")
    print(
        f"  {'korelasyon (A ile)':<26} "
        f"{np.corrcoef(eski_d, yeni_d)[0,1]:>10.4f} "
        f"{np.corrcoef(eski_d, kucuk_d)[0,1]:>12.4f}"
    )
    print(
        f"  {'ortalama MUTLAK fark':<26} {np.abs(fark).mean()*100:>9.2f}p "
        f"{np.abs(fark_k).mean()*100:>11.2f}p"
    )
    print(
        f"  {'medyan mutlak fark':<26} {np.median(np.abs(fark))*100:>9.2f}p "
        f"{np.median(np.abs(fark_k))*100:>11.2f}p"
    )
    print(
        f"  {'işaret değiştiren':<26} {int(((eski_d>0)!=(yeni_d>0)).sum()):>10} "
        f"{int(((eski_d>0)!=(kucuk_d>0)).sum()):>12}"
    )
    print(
        f"  {'|fark| > 1 puan':<26} {int((np.abs(fark)>0.01).sum()):>10} "
        f"{int((np.abs(fark_k)>0.01).sum()):>12}"
    )
    print(
        f"  {'|fark| > 3 puan':<26} {int((np.abs(fark)>0.03).sum()):>10} "
        f"{int((np.abs(fark_k)>0.03).sum()):>12}"
    )

    print("\n" + "=" * 74)
    print("STRES GÜNÜ İÇEREN PENCERELER (|XU100| > %3)")
    print("=" * 74)
    stres_d = np.array(stresli)
    for etiket, maske in (("stres VAR", stres_d), ("stres YOK", ~stres_d)):
        if maske.sum() == 0:
            continue
        print(
            f"  {etiket:10} n={int(maske.sum()):4}  "
            f"beta=1 ort={eski_d[maske].mean()*100:+6.2f}%  "
            f"model ort={yeni_d[maske].mean()*100:+6.2f}%  "
            f"mutlak fark={np.abs(fark[maske]).mean()*100:5.2f} puan"
        )

    # --- kullanıcının gerçekten gördüğü şey: Modül C panelleri ---
    print("\n" + "=" * 74)
    print("MODÜL C PANELLERİ — kullanıcının gördüğü medyanlar")
    print("=" * 74)
    print(
        f"  {'GRUP':<22} {'n':>4} {'A beta=1':>9} {'B ham':>9} "
        f"{'C küçült':>9} {'C−A':>7}"
    )
    kademe_d = np.array([k if k else "-" for k in kademeler])
    tahta_d = np.array([t if t else "-" for t in tahtalar])
    for kademe in ("mega", "onemli", "rutin"):
        for tahta in ("temiz", "hareketli", "tedbirli"):
            maske = (kademe_d == kademe) & (tahta_d == tahta)
            if maske.sum() < 20:
                continue
            e = np.median(eski_d[maske])
            y = np.median(yeni_d[maske])
            k = np.median(kucuk_d[maske])
            print(
                f"  {kademe + '|' + tahta:<22} {int(maske.sum()):>4} "
                f"{e*100:>+8.2f}% {y*100:>+8.2f}% {k*100:>+8.2f}% "
                f"{(k-e)*100:>+6.2f}p"
            )
    for kademe in ("mega", "onemli", "rutin"):
        maske = kademe_d == kademe
        if maske.sum() == 0:
            continue
        e = np.median(eski_d[maske])
        y = np.median(yeni_d[maske])
        k = np.median(kucuk_d[maske])
        print(
            f"  {kademe + ' (tüm tahtalar)':<22} {int(maske.sum()):>4} "
            f"{e*100:>+8.2f}% {y*100:>+8.2f}% {k*100:>+8.2f}% "
            f"{(k-e)*100:>+6.2f}p"
        )

    print("\n" + "=" * 74)
    print("EN ÇOK DEĞİŞEN 10 BİLDİRİM")
    print("=" * 74)
    sirali = np.argsort(-np.abs(fark))[:10]
    print(
        f"  {'TICKER':<8} {'T0':<12} {'β ham':>7} {'β küç':>7} "
        f"{'A':>8} {'B ham':>8} {'C küç':>8}"
    )
    for idx in sirali:
        ticker, t0 = kimlik[idx]
        print(
            f"  {ticker:<8} {str(t0):<12} {beta_d[idx]:>7.2f} "
            f"{beta_k_d[idx]:>7.2f} {eski_d[idx]*100:>+7.2f}% "
            f"{yeni_d[idx]*100:>+7.2f}% {kucuk_d[idx]*100:>+7.2f}%"
        )

    print("\nHiçbir şey yazılmadı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
