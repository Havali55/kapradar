"""KAP detay yanıtı ayrıştırıcısının testleri.

Fixture'lar gerçek KAP yanıtları (2026-09-18'de çekildi):
  detay_orge_1665567  — Yeni İş İlişkisi, çok para birimli, güncelleme
  detay_ardyz_1664397 — Yeni İş İlişkisi, tek para birimli, ilk açıklama
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from kap_radar.ayristirici import (
    aciklama_metinleri,
    bildirim_ayristir,
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


@pytest.fixture
def ardyz() -> dict:
    return detay_yukle("detay_ardyz_1664397")


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


def test_bildirim_kimlik_alanlarini_esler(orge):
    """Upsert anahtarı kararlı disclosureId; kap_index ayrı tutulur."""
    bildirim = bildirim_ayristir(orge)

    assert bildirim.kap_id == "4028328ca09bee9001a0b53d7b914cac"
    assert bildirim.kap_index == 1665567
    assert bildirim.ticker == "ORGE"
    assert bildirim.sablon_kodu == "oda-12000"


def test_bildirim_yayin_zamanini_istanbul_saatiyle_cozer(orge):
    """Detay API'si 'YYYY.MM.DD HH:MM:SS' kullanıyor — liste API'sinden farklı.

    Zaman dilimi §8'deki t0 seans kararı için kritik: bildirim seans
    kapandıktan sonra düştüyse t0 bir sonraki işlem günüdür. Saat naif
    kalırsa tüm tepki serisi bir gün kayar.
    """
    bildirim = bildirim_ayristir(orge)

    assert bildirim.yayin_zamani == datetime(
        2026, 9, 18, 18, 58, 45, tzinfo=ZoneInfo("Europe/Istanbul")
    )


def test_bildirim_guncelleme_zincirini_cikarir(orge):
    """ORGE bildirimi 2023'ten beri süren bir işin beşinci güncellemesi."""
    bildirim = bildirim_ayristir(orge)

    assert bildirim.guncelleme_mi is True
    assert bildirim.duzeltme_mi is False
    assert bildirim.onceki_aciklama_tarihleri == [
        date(2023, 5, 10),
        date(2023, 6, 14),
        date(2024, 1, 3),
        date(2025, 2, 7),
    ]


def test_bildirim_kap_alanlarini_llmsiz_doldurur(orge):
    """Karşı taraf, niteliği ve başlangıç tarihi KAP'ın kendi verisi."""
    bildirim = bildirim_ayristir(orge)

    assert bildirim.kap_alanlari["karsi_taraf"] == (
        "Özgün İnşaat Taahhüt San. ve Tic. Ltd. Şti."
    )
    assert bildirim.kap_alanlari["karsi_taraf_niteligi"] == "Müşteri (Customer)"
    assert bildirim.kap_alanlari["baslangic"] == date(2023, 5, 10)


def test_ilk_aciklamada_guncelleme_bayragi_kapali(ardyz):
    """ARDYZ bildirimi ilk açıklama — zincir boş olmalı."""
    bildirim = bildirim_ayristir(ardyz)

    assert bildirim.guncelleme_mi is False
    assert bildirim.onceki_aciklama_tarihleri == []
