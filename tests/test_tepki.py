"""t0 ve anormal getiri hesabının testleri (spec §8).

Hepsi saf fonksiyon: ağ yok, veritabanı yok. §8'deki iki incelik burada
sınanıyor, çünkü ikisi de sessizce yanlış sonuç üretiyor:
  - bildirim seans kapandıktan sonra düştüyse t0 bir sonraki işlem günü
  - tepki ham getiri değil, endeksten arındırılmış getiri
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from kap_radar.tepki import car_hesapla, t0_bul

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
