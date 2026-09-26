"""Veri denetimi betiğinin saf kontrolleri (`scripts/veri_denetimi.py`)."""

from __future__ import annotations

from kap_radar.denetim import kdv_dahil_mi, ozette_metinde_olmayan_sayi


def test_kdv_dahil_alinti_yakalanir():
    assert kdv_dahil_mi("211.702.000,00 TL (KDV Dahil)")
    assert kdv_dahil_mi("KDV dâhil 7.070.000.000-TL")


def test_kdv_haric_ve_arti_kdv_yakalanmaz():
    assert not kdv_dahil_mi("163.500.000 TL (KDV hariç)")
    assert not kdv_dahil_mi("9.750.000 USD + KDV")


def test_ozetteki_sayi_metinde_yoksa_doner():
    metin = "Sözleşme bedeli 21.309.590 USD'dir. Sevkiyat 2027 Nisan'da biter."
    assert ozette_metinde_olmayan_sayi(["Bedel 21.309.590 USD", "18 ay sürer"], metin) == "18"


def test_yuvarlanmis_ozet_sayisi_metinde_sayilir():
    """KBORU: metin 272.098.214,40 TL, özet '272,1 milyon TL'."""
    metin = "Sözleşmelerin toplam satış tutarları 272.098.214,40 TL olup"
    assert ozette_metinde_olmayan_sayi(["Toplam 272,1 milyon TL"], metin) is None


def test_tek_haneli_sayi_denetlenmez():
    assert ozette_metinde_olmayan_sayi(["3 madde"], "metin") is None
