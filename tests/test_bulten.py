from datetime import date

import pytest

from kap_radar.bulten import marj, metni_coz, satirlari_oku

BASLIK = (
    "TARIH;ISLEM  KODU;BULTEN ADI;ENSTRUMAN GRUBU;ONCEKI KAPANIS FIYATI;KAPANIS FIYATI;"
    "TOPLAM ISLEM HACMI;TOPLAM ISLEM ADEDI\n"
    "DATE;CODE;NAME;GROUP;PREV;CLOSE;VALUE;VOLUME\n"
)


def _metin(*satirlar: str) -> str:
    return BASLIK + "".join(s + "\n" for s in satirlar)


def test_pay_satiri_okunur_ve_getiri_hesaplanir():
    s = satirlari_oku(_metin("2020-01-02;AEFES.E;ANADOLU EFES;EQT;23.08;23.06;12232224.72;528017"))
    assert len(s) == 1
    assert s[0].tarih == date(2020, 1, 2)
    assert s[0].ticker == "AEFES"
    assert s[0].adet == 528017 and s[0].hacim_tl == pytest.approx(12232224.72)
    assert s[0].getiri == pytest.approx(23.06 / 23.08 - 1)


def test_pay_olmayan_satirlar_atlanir():
    s = satirlari_oku(_metin(
        "2020-01-02;AEFES.E;X;EQT;1;1;1;1",
        "2020-01-02;AEFES.R;RUCHAN;EQT;1;1;1;1",   # rüçhan
        "2020-01-02;XYZ.F;FON;ETF;1;1;1;1",        # başka grup
        "2020-01-02;BOS.E;BOS;EQT;;1;1;1",          # eksik sayı
    ))
    assert [x.ticker for x in s] == ["AEFES"]


def test_ayni_pay_iki_satirda_ise_adedi_buyuk_olan_kalir():
    s = satirlari_oku(_metin(
        "2020-01-02;ABC.E;X;EQT;10;11;100;10",
        "2020-01-02;ABC.E;X;EQT;10;12;5000;400",
    ))
    assert len(s) == 1 and s[0].kapanis == 12


def test_onceki_kapanis_sifirsa_getiri_yok():
    s = satirlari_oku(_metin("2020-01-02;YENI.E;HALKA ARZ;EQT;0;5;10;2"))
    assert s[0].getiri is None


def test_islem_gormeyen_gunde_getiri_yok():
    # Bülten işlem olmayan günde kapanışı 0 yazıyor; −%100 değil.
    s = satirlari_oku(_metin("2020-01-02;DURAN.E;X;EQT;12.5;0;0;0"))
    assert s[0].getiri is None


def test_marj_2020_marttan_once_yirmi():
    assert marj(date(2020, 3, 12)) == pytest.approx(0.205)
    assert marj(date(2020, 3, 13)) == pytest.approx(0.105)


def test_noktali_tarih_bicimi_okunur():
    s = satirlari_oku(_metin("21.05.2020;ABC.E;X;EQT;17.39;17.47;107653362.5;6160055"))
    assert s[0].tarih == date(2020, 5, 21)


def test_bom_ve_cp1254_cozulur():
    bom = ("﻿" + _metin("2020-01-02;ABC.E;ŞİRKET;EQT;1;1;1;1")).encode("utf-8")
    assert satirlari_oku(metni_coz(bom))[0].ticker == "ABC"
    eski = _metin("2020-01-02;ABC.E;ŞİRKET;EQT;1;1;1;1").encode("cp1254")
    assert satirlari_oku(metni_coz(eski))[0].ticker == "ABC"
