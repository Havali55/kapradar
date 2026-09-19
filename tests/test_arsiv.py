"""Ham veri arşivinin testleri.

Arşiv backfill'in kontrol noktası: 20 dakikalık bir çekim yarıda kalırsa
ikinci koşu kaldığı yerden devam etmeli, çekilmiş bildirimi bir daha
istememeli (spec §13, risk 2 — darboğaz LLM değil çekim hızı).
"""

from __future__ import annotations

from datetime import date

import pytest

from kap_radar.arsiv import HamArsiv


def test_yazilan_detay_aynen_geri_okunur(tmp_path):
    """Türkçe karakterler diske gidip geri gelirken bozulmamalı."""
    arsiv = HamArsiv(tmp_path)
    detay = {"disclosure": {"companyTitle": "ORGE ENERJİ ELEKTRİK TAAHHÜT A.Ş."}}

    arsiv.yaz(1665567, detay)

    assert arsiv.oku(1665567) == detay


def test_cekilmemis_bildirim_arsivde_gorunmez(tmp_path):
    assert HamArsiv(tmp_path).var_mi(1665567) is False


def test_yazilan_bildirim_cekilmis_sayilir(tmp_path):
    arsiv = HamArsiv(tmp_path)

    arsiv.yaz(1665567, {"disclosure": {}})

    assert arsiv.var_mi(1665567) is True


def test_yazma_yarida_kalirsa_hedef_dosya_olusmaz(tmp_path):
    """Yarım JSON dosyası 'çekilmiş' sayılırsa o bildirim sonsuza dek eksik kalır.

    Bu yüzden yazma ya tamamlanır ya hiç olmaz: önce tam serileştirilir,
    sonra geçici dosya üzerinden yerine konur.
    """
    arsiv = HamArsiv(tmp_path)

    with pytest.raises(TypeError):
        arsiv.yaz(1665567, {"tarih": date(2026, 9, 18)})

    assert arsiv.var_mi(1665567) is False


def test_arsivdeki_indeksler_sirali_donur(tmp_path):
    """Yükleyici arşivi tarihsel sırayla işleyebilmeli."""
    arsiv = HamArsiv(tmp_path)
    for indeks in (1665567, 1664397, 1665001):
        arsiv.yaz(indeks, {"disclosure": {}})

    assert arsiv.indeksler() == [1664397, 1665001, 1665567]


def test_liste_penceresi_onbellege_alinir(tmp_path):
    """Aynı hafta iki kez sorulmamalı; pencere de kontrol noktasının parçası."""
    arsiv = HamArsiv(tmp_path)
    baslangic, bitis = date(2026, 9, 14), date(2026, 9, 20)

    assert arsiv.liste_var_mi(baslangic, bitis) is False
    arsiv.liste_yaz(baslangic, bitis, [{"disclosureIndex": 1665567}])

    assert arsiv.liste_var_mi(baslangic, bitis) is True
    assert arsiv.liste_oku(baslangic, bitis) == [{"disclosureIndex": 1665567}]


def test_farkli_pencereler_ayri_dosyalara_yazilir(tmp_path):
    """Pencere anahtarı iki tarihi birden taşımalı, yoksa haftalar birbirini ezer."""
    arsiv = HamArsiv(tmp_path)
    arsiv.liste_yaz(date(2026, 9, 14), date(2026, 9, 20), [{"disclosureIndex": 1}])

    assert arsiv.liste_var_mi(date(2026, 9, 21), date(2026, 9, 27)) is False
