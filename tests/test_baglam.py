"""Modül B bağlamı: VBTS ayrıştırma ve point-in-time sayımlar.

Örnek metinler gerçek Borsa İstanbul duyurularından kısaltıldı.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from kap_radar.baglam import (
    VbtsAyristirmaHatasi,
    VbtsKademesi,
    VbtsTedbiri,
    aktif_vbts_kademesi,
    ayri_gun_sayisi,
    pencere_sayisi,
    seans_baslangici,
    vbts_ayristir,
)

KREDI = (
    "Within the scope of the VBMS ... AHSGY.E ... İngilizce metin. "
    "Sermaye Piyasası Kurulu kararı uyarınca devreye alınan Volatilite Bazlı "
    "Tedbir Sistemi (VBTS) kapsamında GUNDG.E, INTEM.E ve PAPIL.E payları "
    "03/09/2024 tarihli işlemlerden (seans başından) 02/10/2024 tarihli "
    "işlemlere (seans sonuna) kadar kredili işlemlere konu edilemeyecektir. "
    "Not: VBTS kapsamında getirilen tedbirler ... emir paketi ..."
)
BRUT = (
    "(VBTS) kapsamında RTALB.E ve SAMAT.E paylarında 04/09/2024 tarihli "
    "işlemlerden (seans başından) 03/10/2024 tarihli işlemlere (seans sonuna) "
    "kadar brüt takas uygulanacaktır. İlgili payda halihazırda uygulanmakta "
    "olan ve VBTS kapsamında önceki aşamalarda tanımlanan tedbirler de "
    "(kredili işlem yasağı tedbiri) brüt takas tedbirinin uygulandığı süre "
    "boyunca devam edecektir. Not: ..."
)
EMIR = (
    "(VBTS) kapsamında MEGAP.E payları 03/09/2024 tarihli işlemlerden (seans "
    "başından) 02/10/2024 tarihli işlemlere (seans sonuna) kadar emir paketi "
    "tedbiri ile işlem görecektir. Emir paketi tedbiri, \"piyasa emri ...\"."
)


def test_kredi_yasagi_uc_hisseye_ayrisir():
    tedbirler = vbts_ayristir(KREDI)

    assert [t.ticker for t in tedbirler] == ["GUNDG", "INTEM", "PAPIL"]
    assert {t.kademe for t in tedbirler} == {VbtsKademesi.KREDI_YASAGI}
    assert tedbirler[0].baslangic == date(2024, 9, 3)
    assert tedbirler[0].bitis == date(2024, 10, 2)


def test_ingilizce_bolum_ve_not_kismi_karistirilmaz():
    """İngilizce metindeki AHSGY ve 'Not:' sonrasındaki 'emir paketi' sayılmaz."""
    tedbirler = vbts_ayristir(KREDI)

    assert "AHSGY" not in {t.ticker for t in tedbirler}
    assert tedbirler[0].kademe == VbtsKademesi.KREDI_YASAGI


def test_brut_takas_onceki_kademeyi_anmasina_ragmen_brut_takastir():
    assert {t.kademe for t in vbts_ayristir(BRUT)} == {VbtsKademesi.BRUT_TAKAS}


def test_emir_paketi():
    [t] = vbts_ayristir(EMIR)
    assert (t.ticker, t.kademe) == ("MEGAP", VbtsKademesi.EMIR_PAKETI)


def test_tanimsiz_tedbir_sessizce_atlanmaz():
    metin = (
        "(VBTS) kapsamında ABCDE.E payları 03/09/2024 tarihli işlemlerden "
        "02/10/2024 tarihli işlemlere kadar yeni bir uygulamaya tabi olacaktır."
    )
    with pytest.raises(VbtsAyristirmaHatasi):
        vbts_ayristir(metin)


def test_aktif_kademe_sure_icinde_en_agiri_verir():
    tedbirler = [
        VbtsTedbiri("X", 1, date(2026, 9, 1), date(2026, 9, 30)),
        VbtsTedbiri("X", 2, date(2026, 9, 10), date(2026, 10, 9)),
    ]
    assert aktif_vbts_kademesi(tedbirler, date(2026, 8, 31)) == 0
    assert aktif_vbts_kademesi(tedbirler, date(2026, 9, 5)) == 1
    assert aktif_vbts_kademesi(tedbirler, date(2026, 9, 30)) == 2
    assert aktif_vbts_kademesi(tedbirler, date(2026, 10, 9)) == 2
    assert aktif_vbts_kademesi(tedbirler, date(2026, 10, 10)) == 0


def test_pencere_bildirim_anindan_sonrasini_saymaz():
    """Lookahead yasak: bildirimle aynı an ve sonrası bilinemezdi."""
    zamanlar = [
        datetime(2026, 1, 1),
        datetime(2026, 6, 1),
        datetime(2026, 9, 1, 10, 0),
        datetime(2026, 9, 1, 12, 0),
    ]
    an = datetime(2026, 9, 1, 10, 0)

    assert pencere_sayisi(zamanlar, an, datetime(2025, 9, 1)) == 2


def test_devre_kesici_ayni_gun_bir_kez_sayilir():
    zamanlar = [
        datetime(2026, 9, 1, 10, 5),
        datetime(2026, 9, 1, 14, 30),
        datetime(2026, 9, 2, 11, 0),
    ]
    assert ayri_gun_sayisi(zamanlar, datetime(2026, 9, 3), datetime(2026, 8, 1)) == 2


def test_seans_baslangici_islem_gunu_sayar():
    takvim = [date(2026, 9, d) for d in (14, 15, 17, 18, 21)]

    assert seans_baslangici(takvim, date(2026, 9, 21), 3) == date(2026, 9, 17)
    # Tatil günü: 16 Eylül takvimde yok, 15 dahil geriye sayılır.
    assert seans_baslangici(takvim, date(2026, 9, 16), 2) == date(2026, 9, 14)
