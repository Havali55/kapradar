"""Fiyat serisi dönüşümü ve tutarlılık kontrolleri (spec §8, §13 risk 4).

yfinance resmî bir kaynak değil ve ara ara kırılıyor. Seri kendi
veritabanımıza girmeden önce elenmezse bozuk bir kapanış tüm CAR
hesabını sessizce zehirler.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd

from kap_radar.fiyat import cerceveden_seri, seri_dogrula, sicrama_gunleri


def cerceve(satirlar: dict[str, tuple[float, int]]) -> pd.DataFrame:
    """yfinance'in döndürdüğü biçimde küçük bir çerçeve."""
    indeks = pd.DatetimeIndex([pd.Timestamp(g) for g in satirlar])
    return pd.DataFrame(
        {
            "Close": [d[0] for d in satirlar.values()],
            "Volume": [d[1] for d in satirlar.values()],
        },
        index=indeks,
    )


def test_cerceve_ondalik_seriye_cevrilir():
    """Fiyat float olarak taşınırsa getiri hesabına ikilik gürültü sızar."""
    seri = cerceveden_seri(
        "ORGE", cerceve({"2026-09-17": (120.30, 1_000), "2026-09-18": (121.90, 2_000)})
    )

    assert seri.kapanislar == {
        date(2026, 9, 17): Decimal("120.3"),
        date(2026, 9, 18): Decimal("121.9"),
    }
    assert seri.hacimler[date(2026, 9, 18)] == 2000


def test_float32_gurultusu_temizlenir():
    """yfinance kapanışları float32 taşıyor: 22.2 → 22.200000762939453.

    Ham hâliyle saklamak olmayan bir hassasiyeti iddia eder; BIST fiyat
    adımları dört ondalığın çok üstünde değil.
    """
    seri = cerceveden_seri(
        "ORGE", cerceve({"2026-09-18": (22.200000762939453, 10)})
    )

    assert seri.kapanislar[date(2026, 9, 18)] == Decimal("22.2")


def test_bos_kapanis_seriye_girmez():
    """yfinance eksik günü NaN ile döndürüyor; NaN Decimal'e çevrilirse patlar."""
    ham = cerceve({"2026-09-17": (120.30, 1_000), "2026-09-18": (float("nan"), 0)})

    seri = cerceveden_seri("ORGE", ham)

    assert date(2026, 9, 18) not in seri.kapanislar


def test_temiz_seri_uyari_uretmez():
    seri = cerceveden_seri(
        "ORGE",
        cerceve(
            {
                "2026-09-16": (100.0, 10),
                "2026-09-17": (102.0, 10),
                "2026-09-18": (101.0, 10),
            }
        ),
    )

    assert seri_dogrula(seri) == []


def test_negatif_fiyat_isaretlenir():
    seri = cerceveden_seri(
        "ORGE", cerceve({"2026-09-17": (100.0, 10), "2026-09-18": (-5.0, 10)})
    )

    uyarilar = seri_dogrula(seri)

    assert len(uyarilar) == 1
    assert "2026-09-18" in uyarilar[0]


def test_tek_gunde_yuzde_50_siçrama_isaretlenir():
    """Bedelsiz artırım/bölünme serisi kırar; auto_adjust bunu düzeltmiş olmalı.

    Düzeltilmemiş bir sıçrama kaldıysa o hissenin CAR'ı anlamsızdır.
    """
    seri = cerceveden_seri(
        "ORGE", cerceve({"2026-09-17": (100.0, 10), "2026-09-18": (151.0, 10)})
    )

    uyarilar = seri_dogrula(seri)

    assert len(uyarilar) == 1
    assert "sıçrama" in uyarilar[0]


def test_sicrama_gunleri_bozuk_gunu_tarih_olarak_verir():
    """CAR hesabı bu günlere dokunan pencereleri reddediyor.

    Uyarı metni insan için; tepki hesabına tarih kümesi gerekiyor.
    Gerçek örnek: HRKET 2026-09-09'da 87.9 → 6.15 (düzeltilmemiş bedelsiz).
    """
    seri = cerceveden_seri(
        "HRKET",
        cerceve(
            {
                "2026-09-08": (87.9, 10),
                "2026-09-09": (6.1464, 10),
                "2026-09-10": (6.2, 10),
            }
        ),
    )

    assert sicrama_gunleri(seri.kapanislar) == [date(2026, 9, 9)]


def test_normal_dalgalanma_isaretlenmez():
    """Eşik %50; BIST'te %10'luk gün sıradan."""
    seri = cerceveden_seri(
        "ORGE", cerceve({"2026-09-17": (100.0, 10), "2026-09-18": (110.0, 10)})
    )

    assert seri_dogrula(seri) == []
