"""KAP detay yanıtı ayrıştırıcısının testleri.

Fixture'lar gerçek KAP yanıtları (2026-09-18'de çekildi):
  detay_orge_1665567  — Yeni İş İlişkisi, çok para birimli, güncelleme
  detay_ardyz_1664397 — Yeni İş İlişkisi, tek para birimli, ilk açıklama
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from kap_radar.ayristirici import (
    aciklama_metinleri,
    evet_hayir_coz,
    sablon_kodu_bul,
    tarih_listesi_coz,
    xbrl_alanlari,
)

FIXTURE = Path(__file__).parent / "fixtures"


def detay_yukle(ad: str) -> dict:
    ham = json.loads((FIXTURE / f"{ad}.json").read_text(encoding="utf-8"))
    return ham[0]


@pytest.fixture
def orge() -> dict:
    return detay_yukle("detay_orge_1665567")


def test_sablon_kodunu_govde_html_sinifindan_cikarir(orge):
    """Router Türkçe başlığa değil bu koda bağlanacak.

    KAP gövdeyi `tbl_oda-12000_New-Business-Relation` sınıflı tabloyla sarar.
    """
    govde = orge["disclosureBody"][0]

    assert sablon_kodu_bul(govde) == "oda-12000"


def test_aciklama_metni_turkceyi_ingilizceden_ayirir(orge):
    """Türkçe metin İngilizce çeviriyi içermemeli.

    KAP iki dili aynı bloğa koyuyor. Ayrılmazsa LLM her rakamı iki kez
    görür ve alıntı kapısı yanlış eşleşir (spec §6).
    """
    metin = aciklama_metinleri(orge["disclosureBody"][0])

    assert "863.000 EUR+KDV tutarında ilave sipariş" in metin.tr
    assert "EUR 863,000" not in metin.tr


def test_xbrl_alanlarini_kod_deger_esleme_olarak_cikarir(orge):
    """Karşı taraf LLM'e sorulmaz — KAP'ın yapılandırılmış alanından gelir."""
    alanlar = xbrl_alanlari(orge["disclosureBody"][0])

    assert (
        alanlar["oda_NameSurnameOrCompanyTitleOfCustomerOrSupplier"]
        == "Özgün İnşaat Taahhüt San. ve Tic. Ltd. Şti."
    )


@pytest.mark.parametrize(
    ("ham", "beklenen"),
    [
        ("Evet (Yes)", True),
        ("Hayır (No)", False),
        ("-", None),
        ("", None),
    ],
)
def test_evet_hayir_alanini_cozer(ham, beklenen):
    """KAP bayrakları 'Evet (Yes)' / 'Hayır (No)' biçiminde gelir."""
    assert evet_hayir_coz(ham) is beklenen


def test_onceki_aciklama_tarihlerini_listeye_cozer():
    """Güncelleme zinciri virgülle ayrılmış TR tarihleri olarak gelir."""
    ham = "10.05.2023, 14.06.2023, 03.01.2024, 07.02.2025"

    assert tarih_listesi_coz(ham) == [
        date(2023, 5, 10),
        date(2023, 6, 14),
        date(2024, 1, 3),
        date(2025, 2, 7),
    ]


def test_bos_tarih_alani_bos_liste_dondurur():
    """Açıklama ilk kez yapılıyorsa KAP '-' koyuyor."""
    assert tarih_listesi_coz("-") == []
