"""Fon Portföy Dağılım Raporu ayrıştırıcısı — gerçek rapor metninden kısaltma."""

from __future__ import annotations

from kap_radar.fon import rapor_ayristir

# Tera Portföy Dördüncü Hisse (DOH), Ağustos 2026 — sayfa başlığı bir
# pozisyon bloğunun ortasına düşmüş hâliyle.
METIN = """Ağustos-2026
HİSSE SENETLERİ
Hisse Türk
ALKLC ALTINKILIÇ
GIDA VE
SÜT
2.750.000,00 423,340909 31/08/26 425,750000 1.170.812.500,00 10,21 7,96TL 80100511 9,06
TREALTK00013
ALKLC ALTINKILIÇ
GIDA VE
-1.400.000,00 423,340909 31/08/26 425,750000 -596.050.000,00 -5,20 -4,05TL 80100511 -4,61
TREALTK00013
DSTKF DESTEK
FAKTORIN
TOPLAM
(FPD
GRUP (%)TOPLAM DEĞERGÜNLÜK BR
ISIN KODU
G
500.000,00 1.958,600000 31/08/26 2.081,000000 1.040.500.000,00 9,07 7,07TL 80100511 8,05TREDSTF00012
1.850.000,00 1.615.262.500,00 14,08100,00  GRUP TOPLAMI 12,50
KİRA SERTİFİKALARI
XYZAB BAŞKA
1.000,00 1,000000 01/08/26 1,000000 999,00 1,00 1,00TL 80100511 1,00
"""


def test_pozisyonlar_ve_net_toplam():
    rapor = rapor_ayristir(METIN)

    assert rapor.donem == "Ağustos-2026"
    assert [p.ticker for p in rapor.pozisyonlar] == ["ALKLC", "ALKLC", "DSTKF"]
    assert rapor.net() == {"ALKLC": 574_762_500.0, "DSTKF": 1_040_500_000.0}


def test_sayfa_basligi_kodu_ezmez():
    """'GRUP (%)TOPLAM' satırı DSTKF bloğunun kodunu değiştirmemeli."""
    rapor = rapor_ayristir(METIN)
    assert rapor.pozisyonlar[-1].ticker == "DSTKF"
    assert rapor.pozisyonlar[-1].isin == "TREDSTF00012"


def test_grup_toplamiyla_dogrulanir():
    rapor = rapor_ayristir(METIN)
    assert rapor.rapor_hisse_toplami == 1_615_262_500.0
    assert rapor.tutarli


def test_hisse_bolumu_disindaki_kalemler_alinmaz():
    assert "XYZAB" not in rapor_ayristir(METIN).net()


def test_tek_satirlik_pozisyon_ve_sozlesme_nosuz_bicim():
    """İki biçim farkı (gerçek raporlardan): kod+ad+sayı tek satırda; ve
    borsa sözleşme numarası olmayan satır."""
    metin = """Hisse Türk
ISMEN İŞ YATIRIM 50.000,00 42,367360 14/05/26 33,220000 1.661.000,00 0,93 0,82TL 80100517 0,79TREISMD00011
AKBNK AKBANK
T.A.Ş.
-35.500,00 85,022679 31/08/26 79,400000 -2.818.700,00 -0,56 -0,48TL -0,52
TRAAKBNK91N6
14.500,00 -1.157.700,00 1,00 100,00 GRUP TOPLAMI 1,00
"""
    rapor = rapor_ayristir(metin)
    assert rapor.net() == {"ISMEN": 1_661_000.0, "AKBNK": -2_818_700.0}
    assert rapor.tutarli


def test_sayfa_sonunda_kesilen_satir():
    metin = """Hisse Türk
DSTKF DESTEK
270.868,00 1.830,738267 31/08/26 2.081,000000 563.675.501,13 9,48 13,30TL 80100517
Ağustos-2026
13,11
TREDSTF00012
270.868,00 563.675.501,13 9,48 100,00 GRUP TOPLAMI 13,11
"""
    rapor = rapor_ayristir(metin)
    assert rapor.net() == {"DSTKF": 563_675_501.13}
    assert rapor.tutarli


def test_eksik_satir_tutarsiz_sayilir():
    eksik = METIN.replace(
        "500.000,00 1.958,600000 31/08/26 2.081,000000 1.040.500.000,00 9,07 7,07TL 80100511 8,05TREDSTF00012\n",
        "",
    )
    assert not rapor_ayristir(eksik).tutarli
