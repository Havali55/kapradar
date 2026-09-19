"""Anormal getiri (CAR) hesabı — spec §8'in deterministik kısmı.

Yayınlanan tepki metriği ham getiri değil: hisse %2.8 yükselmiş ama
XU100 da %2.8 yükselmişse tepki **yoktur**.

    anormal_getiri(t) = hisse_getirisi(t) − xu100_getirisi(t)

İşlem takvimi ayrı bir tatil tablosundan değil **endeks serisinden**
geliyor: XU100'ün kapanışı olan gün seans var demektir. Elle bakılan bir
tatil listesi eskir, endeks serisi kendi kendini güncel tutar.

Pencere kararı (2026-09-19): spec §8 formülü `t0+1 .. t0+3` diyor ama t0
zaten "piyasanın ilk tepki verebileceği gün" olarak tanımlanmış. İkisi
birleşince asıl tepki günü pencerenin dışında kalıyordu. Varsayılan
pencere bu yüzden **t0 dahil** (0, 2); değeri değiştirmek tek parametre.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")

# BIST pay piyasası kapanışı (kapanış seansı dahil). Koda gömülü tek
# zaman bilgisi; takvimin kendisi veriden geliyor.
SEANS_KAPANIS = time(18, 10)

# Tepki penceresi: t0'dan itibaren kaçıncı işlem günleri toplanacak.
VARSAYILAN_PENCERE = (0, 2)


def t0_bul(
    yayin_zamani: datetime,
    islem_gunleri: Iterable[date],
    seans_kapanis: time = SEANS_KAPANIS,
) -> date | None:
    """Piyasanın bildirime ilk tepki verebileceği işlem günü.

    Bildirim seans kapandıktan sonra düştüyse o günün kapanışı tepkiyi
    içeremez; t0 bir sonraki işlem günüdür. Kaçırılırsa tüm tepki serisi
    bir gün kayar (spec §8).
    """
    yerel = yayin_zamani.astimezone(ISTANBUL)
    gun = yerel.date()
    gunler = sorted(islem_gunleri)

    if yerel.time() < seans_kapanis:
        adaylar = [g for g in gunler if g >= gun]
    else:
        adaylar = [g for g in gunler if g > gun]

    return adaylar[0] if adaylar else None


def _getiri(seri: Mapping[date, Decimal], gun: date, onceki: date) -> Decimal | None:
    """İki işlem günü arasındaki getiri; kapanışlardan biri yoksa None."""
    bugun, dun = seri.get(gun), seri.get(onceki)
    if bugun is None or dun is None or dun == 0:
        return None
    return bugun / dun - 1


def car_hesapla(
    hisse: Mapping[date, Decimal],
    endeks: Mapping[date, Decimal],
    t0: date,
    pencere: tuple[int, int] = VARSAYILAN_PENCERE,
    supheli_gunler: Collection[date] = (),
) -> Decimal | None:
    """Pencere boyunca birikimli anormal getiri.

    Pencere **işlem günü** sayar, takvim günü değil: arada tatil varsa
    takvim günü saymak pencereyi yanlış yere oturtur.

    Eksik tek bir kapanış bile sonucu None yapar. yfinance ara ara gün
    atlıyor (spec §13, risk 4) ve eksik günü yok saymak tepkiyi olduğundan
    küçük gösterirdi — yanlış sayı yayınlamaktansa hiç yayınlamamak.

    `supheli_gunler` aynı ilkenin ikinci yarısı: `auto_adjust` BIST
    bedelsizlerini düzeltmiyor (gerçek veride HRKET 87.9 → 6.15). Böyle
    bir gün pencereye girerse fiyat "var" olduğu için eksik sayılmaz ama
    getiri anlamsızdır; pencere tümden reddedilir.
    """
    gunler = sorted(endeks)
    if t0 not in endeks:
        return None

    t0_sira = gunler.index(t0)
    ilk, son = pencere
    toplam = Decimal(0)

    for adim in range(ilk, son + 1):
        sira = t0_sira + adim
        if sira <= 0 or sira >= len(gunler):
            return None
        gun, onceki = gunler[sira], gunler[sira - 1]
        if gun in supheli_gunler:
            return None

        hisse_getirisi = _getiri(hisse, gun, onceki)
        endeks_getirisi = _getiri(endeks, gun, onceki)
        if hisse_getirisi is None or endeks_getirisi is None:
            return None

        toplam += hisse_getirisi - endeks_getirisi

    return toplam
