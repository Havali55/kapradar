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

Model kararı (2026-09-22, Adım 16 Öneri 4): yukarıdaki formül her hissenin
betasını 1 sayıyor. Bu evrende 106 hissenin 89'u beta < 1 ve 16 Eylül
gibi endeksin %5,5 düştüğü günlerde betası 0,4 olan hisse endeksin tüm
düşüşüyle cezalandırılıyordu. Yayınlanan model artık **piyasa modeli**:

    anormal_getiri(t) = hisse_getirisi(t) − (α + β · xu100_getirisi(t))

β her bildirim için kendi geçmişinden (`beta_tahmin`) ve Vasicek ile
evren ortalamasına küçültülerek (`vasicek_kucult`) tahmin ediliyor.
`car_hesapla` varsayılan α=0, β=1 ile eski formülün birebir aynısı.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")

# BIST pay piyasası kapanışı (kapanış seansı dahil). Koda gömülü tek
# zaman bilgisi; takvimin kendisi veriden geliyor.
SEANS_KAPANIS = time(18, 10)

# Tepki penceresi: t0'dan itibaren kaçıncı işlem günleri toplanacak.
VARSAYILAN_PENCERE = (0, 2)

# --- beta tahmin penceresi --------------------------------------------
# Sızıntı tamponu: tahmin penceresi t0'dan bu kadar işlem günü önce biter.
# Adım 16: işlem hacmi t0−4…t0−1 arasında zaten %10–14 yüksek. O günler
# tahmine girerse beta olayın kendisiyle kirlenir ve model gerçek tepkiyi
# "beklenen" sayıp küçültür.
BETA_TAMPON = 10
# Olay çalışmalarında standart uzunluk; gözlem yetmezse geniş pencere.
BETA_PENCERE = 120
BETA_GENIS_PENCERE = 250
BETA_ASGARI_GOZLEM = 60
# Düzeltilmemiş sermaye işlemi: tahmin penceresine girerse betayı bozar.
# Eşik `fiyat.SICRAMA_ESIGI` ile aynı.
BETA_SICRAMA_ESIGI = 0.50


@dataclass(frozen=True)
class BetaTahmini:
    beta: float
    alfa: float
    gozlem: int
    r2: float
    # Betanın standart hatası — Vasicek küçültmesinin ağırlığı buradan.
    se: float


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


def getiri_serisi(
    seri: Mapping[date, Decimal], gunler: Sequence[date]
) -> dict[date, float]:
    """Takvimdeki ardışık işlem günleri arasındaki getiriler (float).

    Regresyon içindir; yayınlanan CAR `car_hesapla`'da Decimal ile
    hesaplanıyor.
    """
    cikti: dict[date, float] = {}
    for sira in range(1, len(gunler)):
        getiri = _getiri(seri, gunler[sira], gunler[sira - 1])
        if getiri is not None:
            cikti[gunler[sira]] = float(getiri)
    return cikti


def _ols(
    hisse_getiri: Mapping[date, float],
    piyasa: Mapping[date, float],
    gunler: Iterable[date],
    haric: Collection[date],
) -> BetaTahmini | None:
    ortak = [
        g
        for g in gunler
        if g in hisse_getiri
        and g in piyasa
        and g not in haric
        and abs(hisse_getiri[g]) < BETA_SICRAMA_ESIGI
    ]
    n = len(ortak)
    if n < BETA_ASGARI_GOZLEM:
        return None

    x = [piyasa[g] for g in ortak]
    y = [hisse_getiri[g] for g in ortak]
    x_ort, y_ort = sum(x) / n, sum(y) / n
    sxx = sum((a - x_ort) ** 2 for a in x)
    if sxx == 0:
        return None
    sxy = sum((a - x_ort) * (b - y_ort) for a, b in zip(x, y))
    beta = sxy / sxx
    alfa = y_ort - beta * x_ort

    ss_kalan = sum((b - alfa - beta * a) ** 2 for a, b in zip(x, y))
    ss_toplam = sum((b - y_ort) ** 2 for b in y)
    r2 = 1.0 - ss_kalan / ss_toplam if ss_toplam > 0 else 0.0
    se = math.sqrt((ss_kalan / (n - 2)) / sxx)
    return BetaTahmini(beta=beta, alfa=alfa, gozlem=n, r2=r2, se=se)


def beta_tahmin(
    hisse_getiri: Mapping[date, float],
    piyasa: Mapping[date, float],
    gunler: Sequence[date],
    t0: date,
    haric: Collection[date] = (),
) -> BetaTahmini | None:
    """t0'daki bildirim için piyasa modeli (α, β); geçmiş yetmezse None.

    Tahmin penceresi `t0 − BETA_TAMPON`'da biter ve `BETA_PENCERE` işlem
    günü geriye gider; orada yeterli gözlem yoksa `BETA_GENIS_PENCERE`
    denenir.

    `haric`: aynı hissenin DİĞER bildirimlerinin olay pencereleri.
    Dışlanmazsa sık bildirimcilerde tahmin penceresi olay günleriyle
    dolar ve model tepkiyi "normal" saymaya başlar.
    """
    sira = {g: i for i, g in enumerate(gunler)}
    if t0 not in sira:
        return None
    bit = sira[t0] - BETA_TAMPON
    bas = max(1, bit - BETA_PENCERE)
    if bit - bas < BETA_ASGARI_GOZLEM:
        return None

    tahmin = _ols(hisse_getiri, piyasa, gunler[bas:bit], haric)
    if tahmin is None:
        tahmin = _ols(
            hisse_getiri,
            piyasa,
            gunler[max(1, bit - BETA_GENIS_PENCERE) : bit],
            haric,
        )
    return tahmin


def vasicek_kucult(
    tahminler: Sequence[BetaTahmini],
) -> tuple[float, list[float]]:
    """(çapa, küçültülmüş betalar) — sıra girdiyle aynı.

    Ham OLS betaları gürültülü (medyan R² 0,16; 578 bildirimin 11'inde
    negatif beta — bu evrende gerçek bir özellik değil). Her tahmin kendi
    belirsizliğiyle orantılı olarak çapaya çekiliyor: iyi ölçülmüş beta
    yerinde kalır, kötü ölçülmüş olan çapaya yaklaşır.

    Çapa 1,0 DEĞİL evrenin kendi ortalaması: bu evrende beta belirgin
    biçimde 1'in altında (Adım 16) ve 1'e çekmek ölçtüğümüz gerçeği geri
    silerdi.
    """
    if not tahminler:
        raise ValueError("küçültülecek tahmin yok")
    betalar = [t.beta for t in tahminler]
    n = len(betalar)
    capa = sum(betalar) / n
    varyans = sum((b - capa) ** 2 for b in betalar) / n
    kesit_var = max(varyans - sum(t.se**2 for t in tahminler) / n, 1e-6)
    kucuk = [
        (kesit_var / (kesit_var + t.se**2)) * t.beta
        + (1 - kesit_var / (kesit_var + t.se**2)) * capa
        for t in tahminler
    ]
    return capa, kucuk


def car_hesapla(
    hisse: Mapping[date, Decimal],
    endeks: Mapping[date, Decimal],
    t0: date,
    pencere: tuple[int, int] = VARSAYILAN_PENCERE,
    supheli_gunler: Collection[date] = (),
    alfa: Decimal = Decimal(0),
    beta: Decimal = Decimal(1),
) -> Decimal | None:
    """Pencere boyunca birikimli anormal getiri.

    `alfa`/`beta` piyasa modelinin katsayıları; varsayılanlar (0, 1) eski
    "endeksten düz fark" formülünü birebir verir.

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

        toplam += hisse_getirisi - (alfa + beta * endeks_getirisi)

    return toplam
