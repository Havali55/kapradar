"""TÜFE tablosu ve oran hesabı."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from kap_radar.tufe import aylik_tablo, oran

ISTANBUL = ZoneInfo("Europe/Istanbul")


def test_aylik_degisimler_zincirlenince_yayimlanan_yillik_orani_verir():
    """Veri bütünlüğü: elle aktarılan tablo kendi içinde tutarlı mı?

    Aylık değişimler iki ondalıkla yayımlandığı için zincir yıllık
    orandan en fazla birkaç yüzde puanı sapar; 0,05 puan aşan bir fark
    yanlış kopyalanmış bir satırdır.
    """
    tablo = aylik_tablo()
    aylar = sorted(tablo)
    for i in range(12, len(aylar)):
        carpim = Decimal(1)
        for ay in aylar[i - 11 : i + 1]:
            carpim *= 1 + tablo[ay][0] / 100
        assert abs((carpim - 1) * 100 - tablo[aylar[i]][1]) < Decimal("0.05"), aylar[i]


def test_aralik_2023_eylul_2024_orani():
    """TÜİK endeksiyle 2526,16 / 1859,38 = 1,3586."""
    assert oran(date(2023, 12, 31), date(2024, 9, 30)) == pytest.approx(
        Decimal("1.3586"), abs=Decimal("0.0005")
    )


def test_ayni_ay_orani_bir():
    assert oran(date(2024, 9, 30), date(2024, 9, 15)) == Decimal(1)


def test_tabloda_olmayan_ay_icin_oran_yok():
    assert oran(date(2023, 12, 31), date(2031, 1, 31)) is None


def test_yayimlanmamis_tufe_kullanilmaz():
    """Eylül TÜFE'si 3 Ekim'de yayımlanır; 2 Ekim'de bilinmiyordu."""
    once = datetime(2024, 10, 2, 12, tzinfo=ISTANBUL)
    sonra = datetime(2024, 10, 3, 12, tzinfo=ISTANBUL)
    assert oran(date(2023, 12, 31), date(2024, 9, 30), an=once) is None
    assert oran(date(2023, 12, 31), date(2024, 9, 30), an=sonra) is not None
