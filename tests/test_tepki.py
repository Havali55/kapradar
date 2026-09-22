"""t0 ve anormal getiri hesabının testleri (spec §8).

Hepsi saf fonksiyon: ağ yok, veritabanı yok. §8'deki iki incelik burada
sınanıyor, çünkü ikisi de sessizce yanlış sonuç üretiyor:
  - bildirim seans kapandıktan sonra düştüyse t0 bir sonraki işlem günü
  - tepki ham getiri değil, endeksten arındırılmış getiri
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from kap_radar.tepki import (
    BETA_ASGARI_GOZLEM,
    BETA_PENCERE,
    BETA_TAMPON,
    BetaTahmini,
    beta_tahmin,
    car_hesapla,
    t0_bul,
    vasicek_kucult,
)

ISTANBUL = ZoneInfo("Europe/Istanbul")

# 2026-09-14 Pazartesi ... 18 Cuma, sonra hafta sonu, 21 Pazartesi.
# 16 Çarşamba kasten yok: tatil günü, takvim endeks serisinden geliyor.
ISLEM_GUNLERI = [
    date(2026, 9, 14),
    date(2026, 9, 15),
    date(2026, 9, 17),
    date(2026, 9, 18),
    date(2026, 9, 21),
    date(2026, 9, 22),
    date(2026, 9, 23),
]


def an(yil, ay, gun, saat, dakika) -> datetime:
    return datetime(yil, ay, gun, saat, dakika, tzinfo=ISTANBUL)


# ------------------------------------------------------------------- t0


def test_seans_icinde_dusen_bildirimin_t0_ayni_gun():
    """Piyasa aynı gün tepki verebiliyorsa olay günü o gündür."""
    assert t0_bul(an(2026, 9, 14, 11, 30), ISLEM_GUNLERI) == date(2026, 9, 14)


def test_seans_kapandiktan_sonra_dusen_bildirim_sonraki_gune_kayar():
    """ORGE bildirimi 18:58'de düştü; o günün kapanışı tepkiyi içeremez.

    Kaçırılırsa tüm tepki serisi bir gün kayar (spec §8).
    """
    assert t0_bul(an(2026, 9, 14, 18, 58), ISLEM_GUNLERI) == date(2026, 9, 15)


def test_tatil_gunu_atlanir():
    """İşlem takvimi endeks serisinden geliyor; 16 Eylül'de seans yok."""
    assert t0_bul(an(2026, 9, 15, 19, 0), ISLEM_GUNLERI) == date(2026, 9, 17)


def test_hafta_sonu_dusen_bildirim_pazartesiye_kayar():
    assert t0_bul(an(2026, 9, 19, 10, 0), ISLEM_GUNLERI) == date(2026, 9, 21)


def test_takvim_bitmisse_t0_yok():
    """Fiyat serisi henüz o güne ulaşmadıysa tepki hesaplanamaz — uydurulmaz."""
    assert t0_bul(an(2026, 9, 30, 10, 0), ISLEM_GUNLERI) is None


# ------------------------------------------------------------------ CAR


def seri(*kapanislar: str) -> dict[date, Decimal]:
    """İşlem günlerine sırayla kapanış atar."""
    return {
        gun: Decimal(deger)
        for gun, deger in zip(ISLEM_GUNLERI, kapanislar, strict=False)
    }


def test_endeksle_ayni_oranda_yukselen_hissede_tepki_yok():
    """Hisse %10 çıkmış ama XU100 da %10 çıkmışsa tepki yoktur.

    Ham getiri yayınlamak yanıltıcı olurdu (spec §8).
    """
    hisse = seri("100", "110", "110", "110")
    endeks = seri("1000", "1100", "1100", "1100")

    car = car_hesapla(hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 0))

    assert car == Decimal("0")


def test_endeksten_arindirilmis_getiri_yayinlanir():
    """Hisse %10, endeks %4 → anormal getiri %6."""
    hisse = seri("100", "110")
    endeks = seri("1000", "1040")

    car = car_hesapla(hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 0))

    assert car == Decimal("0.06")


def test_car_penceresi_islem_gunu_sayar_takvim_gunu_degil():
    """t0=15 Eylül, üç işlem günü: 15, 17, 18 — arada tatil var.

    Takvim günü sayılsaydı pencere 16'yı içerir, 18'i dışarıda bırakırdı.
    """
    hisse = seri("100", "110", "121", "133.1")
    endeks = seri("1000", "1000", "1000", "1000")

    car = car_hesapla(hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 2))

    assert car == Decimal("0.3")


def test_eksik_fiyat_gunu_car_hesaplatmaz():
    """Pencere içinde bir gün eksikse sonuç uydurulmaz, None döner.

    yfinance ara ara gün atlıyor (spec §8, risk 4); eksik günü yok saymak
    tepkiyi olduğundan küçük gösterirdi.
    """
    hisse = {date(2026, 9, 14): Decimal("100"), date(2026, 9, 17): Decimal("110")}
    endeks = seri("1000", "1010", "1020", "1030")

    assert car_hesapla(hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 2)) is None


def test_supheli_gun_penceredeyse_car_hesaplanmaz():
    """yfinance'in `auto_adjust`'ı BIST bedelsizlerini düzeltmiyor.

    Gerçek veride görüldü: HRKET 2026-09-09'da 87.9 → 6.15 (~14 kat).
    Düzeltilmemiş böyle bir gün pencereye girerse CAR anlamsız büyük
    çıkar ve alıntı kapısına takılmaz — çünkü fiyat "var". Yanlış sayı
    yayınlamaktansa hiç yayınlamamak.
    """
    hisse = seri("100", "110", "8", "9")
    endeks = seri("1000", "1010", "1020", "1030")

    car = car_hesapla(
        hisse,
        endeks,
        t0=date(2026, 9, 15),
        pencere=(0, 2),
        supheli_gunler={date(2026, 9, 17)},
    )

    assert car is None


def test_supheli_gun_pencere_disindaysa_car_hesaplanir():
    """Şüpheli gün seriyi tümden çöpe atmaz, yalnızca dokunduğu pencereyi."""
    hisse = seri("100", "110", "121", "8")
    endeks = seri("1000", "1000", "1000", "1000")

    car = car_hesapla(
        hisse,
        endeks,
        t0=date(2026, 9, 15),
        pencere=(0, 1),
        supheli_gunler={date(2026, 9, 18)},
    )

    assert car == Decimal("0.2")


def test_t0_oncesi_kapanis_yoksa_hesaplanmaz():
    """Getiri bir önceki işlem gününün kapanışını gerektirir."""
    hisse = {gun: Decimal("100") for gun in ISLEM_GUNLERI[1:]}
    endeks = seri("1000", "1010", "1020", "1030")

    assert car_hesapla(hisse, endeks, t0=date(2026, 9, 14), pencere=(0, 0)) is None


# --------------------------------------------------------- piyasa modeli


def test_piyasa_modeli_dusuk_betali_hisseyi_endeksin_tamaminla_cezalandirmaz():
    """16 Eylül vakası: endeks −%5, hisse −%2, beta 0,4.

    beta=1 bunu −%2 − (−%5) = +%3 "tepki" sayardı; piyasa modeli
    beklenen düşüşü 0,4 × −%5 = −%2 olarak alır, anormal getiri sıfır.
    """
    hisse = seri("100", "98")
    endeks = seri("1000", "950")

    beta1 = car_hesapla(hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 0))
    model = car_hesapla(
        hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 0), beta=Decimal("0.4")
    )

    assert beta1 == Decimal("0.03")
    assert model == Decimal("0")


def test_kiyas_serisinde_eksik_gun_pencereyi_hesaplatmaz():
    """EW kıyas serisi XU100 takviminde örnekleniyor; eksik gün None kalır.

    Anahtar silinseydi takvim kayar ve üç günlük pencere sessizce dört
    günü kapsardı.
    """
    hisse = seri("100", "101", "102", "103")
    kiyas = seri("1000", "1010", "1020", "1030")
    kiyas[date(2026, 9, 17)] = None

    assert car_hesapla(hisse, kiyas, t0=date(2026, 9, 15), pencere=(0, 2)) is None


def test_alfa_her_gun_beklenen_getiriye_eklenir():
    hisse = seri("100", "101", "102.01")
    endeks = seri("1000", "1000", "1000")

    car = car_hesapla(
        hisse, endeks, t0=date(2026, 9, 15), pencere=(0, 1), alfa=Decimal("0.01")
    )

    assert car == Decimal("0")


def _yapay_gecmis(beta: float, gun_sayisi: int = 200):
    """Bilinen betayla üretilmiş gürültüsüz getiriler."""
    gunler = [date(2025, 1, 1) + timedelta(days=i) for i in range(gun_sayisi)]
    piyasa = {g: 0.01 * math.sin(i) for i, g in enumerate(gunler)}
    hisse = {g: 0.0005 + beta * r for g, r in piyasa.items()}
    return gunler, piyasa, hisse


def test_beta_tahmini_bilinen_betayi_bulur():
    gunler, piyasa, hisse = _yapay_gecmis(0.6)

    tahmin = beta_tahmin(hisse, piyasa, gunler, t0=gunler[-1])

    assert tahmin is not None
    assert abs(tahmin.beta - 0.6) < 1e-9
    assert abs(tahmin.alfa - 0.0005) < 1e-9
    assert tahmin.gozlem == BETA_PENCERE


def test_beta_tahmin_penceresi_sizinti_tamponunda_biter():
    """t0'dan önceki BETA_TAMPON gün tahmine girmez (Adım 16 sızıntısı).

    O günlere dev bir hareket konuyor; tampon çalışıyorsa beta etkilenmez.
    """
    gunler, piyasa, hisse = _yapay_gecmis(0.6)
    t0 = gunler[-1]
    for g in gunler[-BETA_TAMPON:]:
        hisse[g] = 0.4  # eşiğin altında, filtreye takılmıyor

    tahmin = beta_tahmin(hisse, piyasa, gunler, t0=t0)

    assert tahmin is not None
    assert abs(tahmin.beta - 0.6) < 1e-9


def test_diger_olay_gunleri_tahminden_dislanir():
    gunler, piyasa, hisse = _yapay_gecmis(0.6)
    olay = set(gunler[100:103])
    for g in olay:
        hisse[g] = 0.3

    tahmin = beta_tahmin(hisse, piyasa, gunler, t0=gunler[-1], haric=olay)

    assert tahmin is not None
    assert abs(tahmin.beta - 0.6) < 1e-9
    assert tahmin.gozlem == BETA_PENCERE - 3


def test_gecmisi_yetmeyen_hissede_beta_uydurulmaz():
    """Yeni halka arz: tahmin penceresinde asgari gözlem yok."""
    gunler, piyasa, hisse = _yapay_gecmis(0.6, gun_sayisi=BETA_ASGARI_GOZLEM + 5)

    assert beta_tahmin(hisse, piyasa, gunler, t0=gunler[-1]) is None


def test_vasicek_kotu_olculmus_betayi_capaya_ceker():
    iyi = BetaTahmini(beta=1.2, alfa=0.0, gozlem=120, r2=0.5, se=0.05)
    kotu = BetaTahmini(beta=-0.4, alfa=0.0, gozlem=120, r2=0.01, se=0.8)
    orta = BetaTahmini(beta=0.7, alfa=0.0, gozlem=120, r2=0.2, se=0.1)

    capa, kucuk = vasicek_kucult([iyi, kotu, orta])

    assert abs(capa - 0.5) < 1e-12
    # İyi ölçülen yerinde kalıyor, negatif beta çapaya yaklaşıp pozitifleşiyor.
    assert abs(kucuk[0] - 1.2) < abs(kucuk[1] - (-0.4))
    assert kucuk[1] > 0
    # Her küçültülmüş beta ham değer ile çapa arasında.
    for ham, k in zip((1.2, -0.4, 0.7), kucuk):
        assert min(ham, capa) <= k <= max(ham, capa)
