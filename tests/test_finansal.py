"""Finansal rapor ayrıştırıcısının ve TTM çözümünün testleri.

Fixture'lar gerçek KAP finansal raporları (ORGE, 2026-09-19'da çekildi):
  finansal_orge_1557898 — FY2025, yıllık, iki sütunlu
  finansal_orge_1649471 — 6A2026, ara dönem, dört sütunlu

Ara dönem raporu asıl tuzağı taşıyor: aynı tabloda hem yılbaşından beri
(YTD) hem yalnız üç aylık sütunlar var. Üç aylığı YTD sanmak hasılatı
yarıya indirir, ciro oranını iki katına çıkarır.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from kap_radar.finansal import (
    DonemHasilat,
    aykiri_indeksler,
    birim_coz,
    finansal_ayristir,
    gelir_tablosu_govdesi,
    konsolide_mi,
    sunum_para_birimi,
    ttm_coz,
)

FIXTURE = Path(__file__).parent / "fixtures"
ISTANBUL = ZoneInfo("Europe/Istanbul")


def kayit_yukle(ad: str) -> dict:
    return json.loads((FIXTURE / f"{ad}.json").read_text(encoding="utf-8"))


@pytest.fixture
def fy2025() -> dict:
    return kayit_yukle("finansal_orge_1557898")


@pytest.fixture
def yarim2026() -> dict:
    return kayit_yukle("finansal_orge_1649471")


# ------------------------------------------------------------ gövde seçimi


def test_gelir_tablosunu_rol_sinifindan_secer():
    """Rapor beş parça; gelir tablosu `tbl_general_role_310000` olan.

    Sıraya güvenmek kırılgan: parça sayısı ve sırası şirkete göre değişiyor.
    """
    detay = {
        "disclosureBody": [
            "<table class='tbl_general_role_210015'>bilanço</table>",
            "<table class='tbl_general_role_310000'>gelir tablosu</table>",
            "<table class='tbl_general_role_520003'>nakit akış</table>",
        ]
    }
    assert "gelir tablosu" in gelir_tablosu_govdesi(detay)


def test_gelir_tablosu_yoksa_none_doner():
    detay = {"disclosureBody": ["<table class='tbl_general_role_210015'>x</table>"]}
    assert gelir_tablosu_govdesi(detay) is None


# ------------------------------------------------------------------ künye


def test_sunum_para_birimini_okur(yarim2026):
    """Raporun para birimi TL değilse hasılat 48 kat yanlış okunur."""
    assert sunum_para_birimi(yarim2026["gelirTablosu"]) == "TL"


def test_konsolide_bayragini_okur(yarim2026):
    assert konsolide_mi(yarim2026["gelirTablosu"]) is True


# ------------------------------------------------------------- ayrıştırma


def test_yillik_rapordan_hasilati_ve_donemi_cikarir(fy2025):
    hasilat = finansal_ayristir(fy2025)

    assert hasilat.ticker == "ORGE"
    assert hasilat.kap_index == 1557898
    assert hasilat.donem_basi == date(2025, 1, 1)
    assert hasilat.donem_sonu == date(2025, 12, 31)
    assert hasilat.ay_sayisi == 12
    assert hasilat.hasilat == Decimal("3495512127")
    assert hasilat.onceki_yil_hasilat == Decimal("4488280980")
    assert hasilat.yayin_zamani == datetime(2026, 2, 17, 20, 21, 19, tzinfo=ISTANBUL)


def test_ara_donemde_ytd_sutunu_secilir_uc_aylik_sutun_degil(yarim2026):
    """Dört sütunlu tabloda doğru olan 6 aylık YTD, 3 aylık değil.

    3 aylık sütun 1.253.630.860; YTD 2.597.519.683. Karıştırılırsa
    payda yarıya iner ve her ciro oranı iki katına çıkar.
    """
    hasilat = finansal_ayristir(yarim2026)

    assert hasilat.ay_sayisi == 6
    assert hasilat.hasilat == Decimal("2597519683")
    assert hasilat.onceki_yil_hasilat == Decimal("2069654707")


# ------------------------------------------------------------ TTM çözümü


def donem(
    *,
    sonu: date,
    ay: int,
    hasilat: str,
    onceki: str | None = None,
    yayin: datetime,
    indeks: int = 1,
    para: str = "TL",
) -> DonemHasilat:
    """Test için kısa yoldan dönem kaydı."""
    yil_once = date(sonu.year - 1, sonu.month, sonu.day)
    return DonemHasilat(
        ticker="TEST",
        kap_index=indeks,
        yayin_zamani=yayin,
        donem_basi=date(sonu.year, 1, 1) if ay == 12 else date(sonu.year, 1, 1),
        donem_sonu=sonu,
        ay_sayisi=ay,
        hasilat=Decimal(hasilat),
        onceki_yil_hasilat=Decimal(onceki) if onceki else None,
        onceki_donem_sonu=yil_once if onceki else None,
        para_birimi=para,
        konsolide=True,
    )


FY2025 = donem(
    sonu=date(2025, 12, 31),
    ay=12,
    hasilat="3495512127",
    onceki="4488280980",
    yayin=datetime(2026, 2, 17, 20, 21, 19, tzinfo=ISTANBUL),
    indeks=1557898,
)
YARIM2026 = donem(
    sonu=date(2026, 6, 30),
    ay=6,
    hasilat="2597519683",
    onceki="2069654707",
    yayin=datetime(2026, 8, 13, 18, 34, 45, tzinfo=ISTANBUL),
    indeks=1649471,
)


def test_yillik_rapor_tek_basina_ttm_verir():
    """En güncel rapor yıllıksa TTM zaten o rapordur."""
    sonuc = ttm_coz([FY2025], datetime(2026, 5, 1, tzinfo=ISTANBUL))

    assert sonuc.hasilat == Decimal("3495512127")
    assert sonuc.yontem == "yillik"
    assert sonuc.kaynak_indeksler == (1557898,)


def test_ara_donem_ttmsi_yillik_rapor_koprusuyle_hesaplanir():
    """TTM = FY(önceki yıl) + YTD(cari) − YTD(geçen yıl aynı dönem).

    ORGE 1665567 bildiriminin gerçek paydası bu: 4.023.377.103 TL.
    """
    sonuc = ttm_coz(
        [FY2025, YARIM2026], datetime(2026, 9, 18, 18, 58, tzinfo=ISTANBUL)
    )

    assert sonuc.hasilat == Decimal("4023377103")
    assert sonuc.yontem == "ytd_koprusu"
    assert sonuc.kaynak_indeksler == (1557898, 1649471)
    assert sonuc.donem_sonu == date(2026, 6, 30)


def test_bildirimden_sonra_yayinlanan_rapor_ttmye_girmez():
    """Point-in-time şartı: lookahead yasak.

    13 Ağustos'ta yayınlanan 6A2026'yı 1 Temmuz'daki bir bildirimde
    kullanmak, o gün piyasanın bilmediği bir rakamla skor üretmek olur.
    """
    sonuc = ttm_coz(
        [FY2025, YARIM2026], datetime(2026, 7, 1, 12, 0, tzinfo=ISTANBUL)
    )

    assert sonuc.hasilat == Decimal("3495512127")
    assert sonuc.yontem == "yillik"


def test_kopru_icin_yillik_rapor_yoksa_ttm_uretilmez():
    """Yarım veriyle TTM uydurulmaz; oran gösterilmez (spec §8)."""
    assert ttm_coz([YARIM2026], datetime(2026, 9, 18, tzinfo=ISTANBUL)) is None


def test_gecen_yil_ayni_donem_sutunu_yoksa_ttm_uretilmez():
    ytd_siz = donem(
        sonu=date(2026, 6, 30),
        ay=6,
        hasilat="2597519683",
        yayin=datetime(2026, 8, 13, tzinfo=ISTANBUL),
        indeks=999,
    )
    assert ttm_coz([FY2025, ytd_siz], datetime(2026, 9, 1, tzinfo=ISTANBUL)) is None


def test_para_birimleri_farkliysa_ttm_uretilmez():
    """USD yıllık ile TL ara dönemi toplamak sessizce 40 kat hata üretir."""
    usd_yillik = donem(
        sonu=date(2025, 12, 31),
        ay=12,
        hasilat="100000000",
        yayin=datetime(2026, 2, 17, tzinfo=ISTANBUL),
        indeks=2,
        para="USD",
    )
    assert ttm_coz([usd_yillik, YARIM2026], datetime(2026, 9, 1, tzinfo=ISTANBUL)) is None


def test_ayni_donemin_revizyonunda_son_yayin_kazanir():
    """Düzeltilmiş rapor öncekini geçersiz kılar."""
    revize = donem(
        sonu=date(2025, 12, 31),
        ay=12,
        hasilat="3500000000",
        yayin=datetime(2026, 3, 10, tzinfo=ISTANBUL),
        indeks=1600000,
    )
    sonuc = ttm_coz([FY2025, revize], datetime(2026, 5, 1, tzinfo=ISTANBUL))

    assert sonuc.hasilat == Decimal("3500000000")
    assert sonuc.kaynak_indeksler == (1600000,)


def test_hic_rapor_yoksa_none_doner():
    assert ttm_coz([], datetime(2026, 9, 1, tzinfo=ISTANBUL)) is None


# ------------------------------------------------------- sunum birimi


def test_bin_tl_sunum_birimi_carpana_ayrisir():
    """TOASO ve DOAS gelir tablosunu '1.000 TL' cinsinden sunuyor.

    Çarpan uygulanmazsa hasılat 1.000 kat küçük okunur ve her ciro oranı
    1.000 kat büyür: 500 milyonluk bir sipariş Tofaş'ın cirosunun
    %156'sı gibi görünür (gerçekte %0,16).
    """
    assert birim_coz("1.000 TL") == ("TL", Decimal("1000"))
    assert birim_coz("1.000.000 TL") == ("TL", Decimal("1000000"))


def test_sade_para_birimi_carpansiz_kalir():
    assert birim_coz("TL") == ("TL", Decimal("1"))
    assert birim_coz("USD") == ("USD", Decimal("1"))


def test_taninmayan_birim_carpan_uydurmaz():
    assert birim_coz("") == (None, Decimal("1"))


def test_hasilat_sunum_birimiyle_carpilmis_doner(fy2025):
    """ORGE sade TL sunuyor; çarpan 1 ve hasılat olduğu gibi."""
    hasilat = finansal_ayristir(fy2025)

    assert hasilat.birim_carpani == Decimal("1")
    assert hasilat.para_birimi == "TL"
    assert hasilat.hasilat == Decimal("3495512127")


# --------------------------------------------------- birim beyanı hatası


def olcekli(sonu: date, ay: int, hasilat: str, indeks: int) -> DonemHasilat:
    return donem(
        sonu=sonu, ay=ay, hasilat=hasilat, onceki="1", yayin=datetime(2026, 1, 1, tzinfo=ISTANBUL), indeks=indeks
    )


def test_bin_kat_sapan_donem_aykiri_sayilir():
    """ONCSM 1559324 gerçek örneği: şirket sade TL raporlarken tek bir
    raporda sunum birimini '1.000.000 TL' yazmış. Rakamın büyüklüğü
    diğer dönemlerin devamı; beyan hatalı.

    Beyana körü körüne uyulursa o şirketin hasılatı bir milyon kat
    şişer ve ciro oranı sıfıra iner — yani skor sessizce yok olur.
    """
    donemler = [
        olcekli(date(2025, 3, 31), 3, "167741811", 1),
        olcekli(date(2025, 6, 30), 6, "341870476", 2),
        olcekli(date(2025, 9, 30), 9, "523362988", 3),
        olcekli(date(2025, 12, 31), 12, "709077088000000", 4),  # birimi yanlış uygulanmış
    ]

    assert aykiri_indeksler(donemler) == [4]


def test_tutarli_seride_aykiri_yok():
    """TOASO gerçekten '1.000 TL' kullanıyor; hepsi aynı ölçekte."""
    donemler = [
        olcekli(date(2025, 3, 31), 3, "24204042000", 1),
        olcekli(date(2025, 6, 30), 6, "95098254000", 2),
        olcekli(date(2025, 9, 30), 9, "189458771000", 3),
        olcekli(date(2025, 12, 31), 12, "319413508000", 4),
    ]

    assert aykiri_indeksler(donemler) == []


def test_tek_donemli_sirkette_aykiri_aranmaz():
    """Karşılaştıracak başka dönem yoksa sapma iddiası kurulamaz."""
    assert aykiri_indeksler([olcekli(date(2025, 12, 31), 12, "100", 1)]) == []


def test_cesit_esasli_gelir_tablosu_da_taninir():
    """NETAS ve ARDYZ 'tbl_general_role_310003' kullanıyor.

    IFRS gelir tablosunu iki türlü sunmaya izin veriyor: fonksiyon esaslı
    (310000) ve çeşit esaslı (310003). Yalnız ilki aranırsa arşivdeki
    935 raporun 577'si sessizce paydasız kalır — 2026-09-20'deki ilk
    çekimde tam olarak bu oldu.
    """
    detay = {
        "disclosureBody": [
            "<table class='tbl_general_role_210015'>bilanço</table>",
            "<table class='tbl_general_role_310003'>gelir tablosu</table>",
        ]
    }
    assert "gelir tablosu" in gelir_tablosu_govdesi(detay)


def test_bilanco_gelir_tablosu_sanilmaz():
    """Rol öneki 3100 ile başlamayan parça seçilmemeli."""
    detay = {
        "disclosureBody": [
            "<table class='tbl_general_role_210015'>bilanço</table>",
            "<table class='tbl_general_role_610000'>dipnotlar</table>",
        ]
    }
    assert gelir_tablosu_govdesi(detay) is None


def test_holding_taksonomisindeki_gelir_tablosu_da_taninir():
    """TCELL 'tbl_holding_role_310030' kullanıyor.

    Rol adının ortasındaki aile adı şirket tipine göre değişiyor
    (general / holding / banka). Sabitlenirse Turkcell gibi holding
    raporlayan şirketler paydasız kalır.
    """
    detay = {
        "disclosureBody": [
            "<table class='tbl_holding_role_210015'>bilanço</table>",
            "<table class='tbl_holding_role_310030'>gelir tablosu</table>",
        ]
    }
    assert "gelir tablosu" in gelir_tablosu_govdesi(detay)


# ------------------------------------------------------------- TMS 29

# Geçen yılın aynı dönemi, İLK yayınlandığı hâliyle (Haziran 2025 TL'si).
# YARIM2026 aynı dönemi 2.069.654.707 olarak yeniden ifade ediyor; oran
# k = 2.069.654.707 / 1.556.131.358 = 1,33 (yıllık ~%33 enflasyon).
YARIM2025_ILK = donem(
    sonu=date(2025, 6, 30),
    ay=6,
    hasilat="1556131358",
    onceki="1200000000",
    yayin=datetime(2025, 8, 12, 18, 0, tzinfo=ISTANBUL),
    indeks=1470000,
)


def test_kopru_yillik_terimi_yeniden_ifade_katsayisiyla_tasir():
    """TMS 29: YTD'ler cari dönem sonu TL'sinde, FY önceki Aralık TL'sinde.

    Yıllık terim 6 ay ileri taşınıyor: × k^(6/12). Düzeltmesiz köprü
    payda'yı küçültür, ciro oranını şişirirdi.
    """
    sonuc = ttm_coz(
        [YARIM2025_ILK, FY2025, YARIM2026],
        datetime(2026, 9, 18, 18, 58, tzinfo=ISTANBUL),
    )

    k = Decimal("2069654707") / Decimal("1556131358")
    carpan = k ** (Decimal(6) / Decimal(12))
    beklenen = (
        Decimal("3495512127") * carpan + Decimal("2597519683") - Decimal("2069654707")
    ).quantize(Decimal(1))
    assert sonuc.hasilat == beklenen
    assert sonuc.enflasyon_carpani == carpan
    assert sonuc.kaynak_indeksler == (1470000, 1557898, 1649471)
    # Düzeltme payda'yı büyütür: ~4,02 milyar → ~4,56 milyar.
    assert sonuc.hasilat > Decimal("4023377103")


def test_orijinal_rapor_yoksa_kopru_duzeltmesiz_ve_isaretli():
    """Karşılaştırılacak ilk yayın yoksa k bilinmiyor; uydurulmuyor."""
    sonuc = ttm_coz(
        [FY2025, YARIM2026], datetime(2026, 9, 18, 18, 58, tzinfo=ISTANBUL)
    )

    assert sonuc.hasilat == Decimal("4023377103")
    assert sonuc.enflasyon_carpani is None


def test_yeniden_ifade_etmeyen_sirkette_kopru_degismez():
    """Banka gibi TMS 29 dışındaki raporlayıcı: k = 1, çarpan 1."""
    ilk = donem(
        sonu=date(2025, 6, 30), ay=6, hasilat="2069654707",
        yayin=datetime(2025, 8, 12, tzinfo=ISTANBUL), indeks=1470000,
    )
    sonuc = ttm_coz(
        [ilk, FY2025, YARIM2026], datetime(2026, 9, 18, tzinfo=ISTANBUL)
    )

    assert sonuc.hasilat == Decimal("4023377103")
    assert sonuc.enflasyon_carpani == Decimal(1)


def test_makul_araligin_disindaki_katsayi_uygulanmaz():
    """k = 3: enflasyon değil, yeniden sınıflama ya da birim hatası."""
    ilk = donem(
        sonu=date(2025, 6, 30), ay=6, hasilat="689884902",
        yayin=datetime(2025, 8, 12, tzinfo=ISTANBUL), indeks=1470000,
    )
    sonuc = ttm_coz(
        [ilk, FY2025, YARIM2026], datetime(2026, 9, 18, tzinfo=ISTANBUL)
    )

    assert sonuc.hasilat == Decimal("4023377103")
    assert sonuc.enflasyon_carpani is None


def test_yillik_yontemde_enflasyon_carpani_yok():
    sonuc = ttm_coz([FY2025], datetime(2026, 5, 1, tzinfo=ISTANBUL))

    assert sonuc.enflasyon_carpani is None
