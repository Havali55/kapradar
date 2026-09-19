"""BIST fiyat serisi çekimi ve elemesi (spec §8, §9 Adım 6).

Yalnızca günlük kapanış gerekiyor — tick/anlık veri değil. Veri kendi
veritabanımızda saklandığı için yfinance bağımlılığı tek seferlik çekime
iniyor; kaynak sonra değiştirilebilir (spec §13, risk 4).

`auto_adjust=True` şart: bedelsiz sermaye artırımı ve pay bölünmesi ham
fiyat serisini kırar, düzeltilmemiş seride CAR anlamsız çıkar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd

# BIST'te %10'luk gün sıradan; %50 tek günlük hareket düzeltilmemiş bir
# sermaye işlemine işaret eder.
SICRAMA_ESIGI = Decimal("0.5")

# Kapanışların saklandığı ondalık basamak sayısı (float32 gürültüsü eşiği).
ONDALIK_BASAMAK = 4

YF_SON_EKI = ".IS"
XU100_SEMBOLU = "XU100.IS"


@dataclass(frozen=True)
class FiyatSerisi:
    """Bir sembolün düzeltilmiş kapanış serisi."""

    sembol: str
    kapanislar: dict[date, Decimal] = field(default_factory=dict)
    hacimler: dict[date, int] = field(default_factory=dict)


def _ondalik(deger) -> Decimal | None:
    """float'ı metin üzerinden, yuvarlayarak Decimal'e çevirir.

    İki ayrı sorun var. Doğrudan `Decimal(float)` ikilik gürültüyü
    taşır; ayrıca yfinance kapanışları float32 tutuyor, yani 22.2 bize
    22.200000762939453 olarak geliyor. BIST fiyat adımları dört ondalığın
    üstünde değil — fazlası olmayan bir hassasiyeti iddia etmek olurdu.
    """
    if deger is None:
        return None
    sayi = float(deger)
    if math.isnan(sayi):
        return None
    return Decimal(str(round(sayi, ONDALIK_BASAMAK))).normalize()


def cerceveden_seri(sembol: str, cerceve: pd.DataFrame) -> FiyatSerisi:
    """yfinance çerçevesini ondalık seriye çevirir.

    Eksik günler (NaN) seriye hiç girmez: veri yokluğu ile sıfır fiyat
    aynı şey değil.
    """
    kapanislar: dict[date, Decimal] = {}
    hacimler: dict[date, int] = {}

    for damga, satir in cerceve.iterrows():
        gun = damga.date()
        kapanis = _ondalik(satir.get("Close"))
        if kapanis is None:
            continue
        kapanislar[gun] = kapanis
        hacim = satir.get("Volume")
        if hacim is not None and not math.isnan(float(hacim)):
            hacimler[gun] = int(hacim)

    return FiyatSerisi(sembol=sembol, kapanislar=kapanislar, hacimler=hacimler)


def sicrama_gunleri(
    kapanislar: dict[date, Decimal], esik: Decimal = SICRAMA_ESIGI
) -> list[date]:
    """Bir önceki kapanışa göre eşiği aşan günler.

    `auto_adjust` BIST bedelsizlerini düzeltmiyor (gerçek veride HRKET
    87.9 → 6.15). Böyle bir gün fiyat olarak "var" olduğu için eksik
    sayılmaz; CAR hesabı bu tarihlere dokunan pencereleri reddediyor.
    """
    gunler = sorted(kapanislar)
    bozuk: list[date] = []

    for sira, gun in enumerate(gunler[1:], start=1):
        kapanis, onceki = kapanislar[gun], kapanislar[gunler[sira - 1]]
        if onceki > 0 and kapanis > 0 and abs(kapanis / onceki - 1) > esik:
            bozuk.append(gun)

    return bozuk


def seri_dogrula(seri: FiyatSerisi, esik: Decimal = SICRAMA_ESIGI) -> list[str]:
    """Seriyi veritabanına girmeden önce eler.

    Bozuk tek bir kapanış hem o günün hem ertesi günün getirisini
    zehirler; sessizce geçirmek yerine uyarı üretilir. Karar insana
    kalıyor: %50'lik düşüş düzeltilmemiş bir sermaye işlemi de olabilir,
    gerçek bir çöküş de.
    """
    uyarilar = [
        f"{seri.sembol} {gun}: fiyat pozitif değil ({kapanis})"
        for gun, kapanis in sorted(seri.kapanislar.items())
        if kapanis <= 0
    ]

    gunler = sorted(seri.kapanislar)
    for gun in sicrama_gunleri(seri.kapanislar, esik):
        onceki = seri.kapanislar[gunler[gunler.index(gun) - 1]]
        uyarilar.append(
            f"{seri.sembol} {gun}: tek günde %50 üstü sıçrama "
            f"({onceki} → {seri.kapanislar[gun]})"
        )

    return uyarilar


def yf_sembolu(ticker: str) -> str:
    """BIST tickerını yfinance sembolüne çevirir: ORGE → ORGE.IS."""
    return f"{ticker}{YF_SON_EKI}"


def seri_cek(sembol: str, baslangic: date, bitis: date) -> FiyatSerisi:
    """yfinance'ten düzeltilmiş günlük kapanışları çeker.

    Ağa çıkan tek fonksiyon; testler `cerceveden_seri`'yi doğruluyor.
    """
    import yfinance

    cerceve = yfinance.download(
        sembol,
        start=baslangic.isoformat(),
        # yfinance'te `end` dışlayıcı: son gün de gelsin diye bir ileri.
        end=(bitis + timedelta(days=1)).isoformat(),
        auto_adjust=True,
        progress=False,
        multi_level_index=False,
    )
    return cerceveden_seri(sembol, cerceve)
