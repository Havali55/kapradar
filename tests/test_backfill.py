"""12 aylık backfill işinin testleri.

Hiçbiri ağa çıkmaz: gerçek `KapIstemcisi` httpx.MockTransport üzerinden
sürülür, arşiv tmp_path'e yazar. Böylece test edilen şey istemcinin
kendisi dahil gerçek zincir oluyor.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx

from kap_radar.arsiv import HamArsiv
from kap_radar.backfill import (
    LISTE_SINIRI,
    backfill,
    finansal_adaylari,
    finansal_backfill,
    haftalik_pencereler,
)
from kap_radar.istemci import KapIstemcisi

FIXTURE = Path(__file__).parent / "fixtures"
LISTE_YOLU = "/tr/api/disclosure/members/byCriteria"
DETAY_ONEKI = "/tr/api/notification/attachment-detail/"


def liste_fixture() -> list[dict]:
    return json.loads(
        (FIXTURE / "liste_2026-09-17_18.json").read_text(encoding="utf-8")
    )


def sahte_kap(liste: list[dict], detay_islevci=None):
    """Isıtma, liste ve detay uçlarını karşılayan sahte KAP.

    `istekler` listesi dışarıya verilir; hangi ucun kaç kez çağrıldığı
    testin asıl konusu.
    """
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        if istek.url.path == LISTE_YOLU:
            return httpx.Response(200, json=liste)
        if istek.url.path.startswith(DETAY_ONEKI):
            indeks = int(istek.url.path.rsplit("/", 1)[1])
            if detay_islevci is not None:
                return detay_islevci(indeks)
            return httpx.Response(
                200,
                json=[{"disclosure": {"disclosureBasic": {"disclosureIndex": indeks}}}],
            )
        return httpx.Response(200, text="<html></html>")

    return islevci, istekler


def istemci_kur(islevci) -> KapIstemcisi:
    return KapIstemcisi(
        transport=httpx.MockTransport(islevci),
        uyku=lambda saniye: None,
        istek_araligi_sn=0,
    )


def detay_istekleri(istekler: list[httpx.Request]) -> list[int]:
    return [
        int(i.url.path.rsplit("/", 1)[1])
        for i in istekler
        if i.url.path.startswith(DETAY_ONEKI)
    ]


# ------------------------------------------------------------- pencereler


def test_haftalik_pencereler_araligi_bosluksuz_kaplar():
    """Pencereler arasında bir gün boşluk kalsa o günün bildirimleri kaybolur."""
    assert haftalik_pencereler(date(2026, 1, 1), date(2026, 1, 20)) == [
        (date(2026, 1, 1), date(2026, 1, 7)),
        (date(2026, 1, 8), date(2026, 1, 14)),
        (date(2026, 1, 15), date(2026, 1, 20)),
    ]


def test_tek_gunluk_aralik_tek_pencere_verir():
    assert haftalik_pencereler(date(2026, 1, 1), date(2026, 1, 1)) == [
        (date(2026, 1, 1), date(2026, 1, 1))
    ]


def test_pencere_uzunlugu_ayarlanabilir(tmp_path):
    """Günde ~475 bildirim var; haftalık pencere 2.000 sınırını aşıyor.

    Sınıra dayanan her pencere bölünüp yeniden soruluyor, yani boşa giden
    istek demek. Koşucu pencereyi baştan dar tutabilmeli.
    """
    sorulan: list[tuple[str, str]] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path != LISTE_YOLU:
            return httpx.Response(200, text="<html></html>")
        govde = json.loads(istek.content)
        sorulan.append((govde["fromDate"], govde["toDate"]))
        return httpx.Response(200, json=[])

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=HamArsiv(tmp_path),
        baslangic=date(2026, 1, 1),
        bitis=date(2026, 1, 6),
        pencere_gun=3,
    )

    assert sorulan == [
        ("2026-01-01", "2026-01-03"),
        ("2026-01-04", "2026-01-06"),
    ]


# ---------------------------------------------------------------- çekim


def test_yalnizca_hedef_sablonun_detayi_cekilir(tmp_path):
    """949 bildirimlik bir haftada yalnızca 6 'Yeni İş İlişkisi' var.

    Diğer şablonların detayını çekmek 150 kat gereksiz istek demek;
    liste kaydındaki `subject` ön eleme için yeterli, şablon kodu
    doğrulaması detay geldikten sonra yapılır.
    """
    islevci, istekler = sahte_kap(liste_fixture())
    arsiv = HamArsiv(tmp_path)

    ozet = backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    assert ozet.aday == 6
    assert ozet.cekildi == 6
    assert len(detay_istekleri(istekler)) == 6


def test_cekilen_detay_arsive_kendi_indeksiyle_yazilir(tmp_path):
    islevci, _ = sahte_kap(liste_fixture())
    arsiv = HamArsiv(tmp_path)

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    assert arsiv.var_mi(1665567)
    kayit = arsiv.oku(1665567)
    assert kayit["disclosure"]["disclosureBasic"]["disclosureIndex"] == 1665567


def test_ikinci_kosu_arsivdekini_yeniden_istemez(tmp_path):
    """Çekim yarıda kalırsa ikinci koşu kaldığı yerden devam etmeli.

    KAP'ın WAF'ı asıl darboğaz (spec §13); aynı bildirimi iki kez istemek
    hem gereksiz hem riskli.
    """
    arsiv = HamArsiv(tmp_path)
    ilk_islevci, _ = sahte_kap(liste_fixture())
    backfill(
        istemci=istemci_kur(ilk_islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    ikinci_islevci, ikinci_istekler = sahte_kap(liste_fixture())
    ozet = backfill(
        istemci=istemci_kur(ikinci_islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    assert ozet.atlandi == 6
    assert ozet.cekildi == 0
    assert detay_istekleri(ikinci_istekler) == []


def test_onbellekteki_pencere_icin_liste_istegi_yapilmaz(tmp_path):
    """Pencere de kontrol noktasının parçası: çekilmiş hafta yeniden sorulmaz."""
    arsiv = HamArsiv(tmp_path)
    arsiv.liste_yaz(date(2026, 9, 17), date(2026, 9, 18), [])
    islevci, istekler = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    assert [i for i in istekler if i.url.path == LISTE_YOLU] == []


def test_tek_bildirimin_hatasi_kosuyu_durdurmaz(tmp_path):
    """20 dakikalık çekim tek bir bozuk bildirim yüzünden çöpe gitmemeli."""
    kotu_indeks = 1665567

    def detay_islevci(indeks: int) -> httpx.Response:
        if indeks == kotu_indeks:
            raise httpx.ConnectTimeout("WAF baglantiyi dusurdu")
        return httpx.Response(
            200,
            json=[{"disclosure": {"disclosureBasic": {"disclosureIndex": indeks}}}],
        )

    islevci, _ = sahte_kap(liste_fixture(), detay_islevci)
    arsiv = HamArsiv(tmp_path)

    ozet = backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
    )

    assert ozet.hatalar == [kotu_indeks]
    assert ozet.cekildi == 5
    assert arsiv.var_mi(kotu_indeks) is False


# ------------------------------------------------------------ 2.000 sınırı


def test_sinira_dayanan_pencere_ikiye_bolunur(tmp_path):
    """KAP liste yanıtını 2.000 kayıtta kesiyor — dolu dönen pencereye güvenilmez.

    17-18 Eylül penceresinde 949 bildirim vardı; haftalık pencere ~3.300
    eder, yani sınırın çok üstünde. Bölünmezse o haftanın bildirimleri
    sessizce kaybolur.
    """
    dolu = [{"disclosureIndex": i, "subject": "Diger"} for i in range(LISTE_SINIRI)]
    sorulan: list[tuple[str, str]] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path != LISTE_YOLU:
            return httpx.Response(200, text="<html></html>")
        istek_govdesi = json.loads(istek.content)
        sorulan.append((istek_govdesi["fromDate"], istek_govdesi["toDate"]))
        gun_sayisi = (
            date.fromisoformat(istek_govdesi["toDate"])
            - date.fromisoformat(istek_govdesi["fromDate"])
        ).days + 1
        return httpx.Response(200, json=dolu if gun_sayisi > 4 else [])

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=HamArsiv(tmp_path),
        baslangic=date(2026, 1, 1),
        bitis=date(2026, 1, 7),
    )

    assert sorulan == [
        ("2026-01-01", "2026-01-07"),
        ("2026-01-01", "2026-01-04"),
        ("2026-01-05", "2026-01-07"),
    ]


def test_bolunemeyen_dolu_pencere_ozette_bildirilir(tmp_path):
    """Tek gün bile sınıra dayanıyorsa veri eksik olabilir — sessiz kalınmaz."""
    dolu = [{"disclosureIndex": i, "subject": "Diger"} for i in range(LISTE_SINIRI)]

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path != LISTE_YOLU:
            return httpx.Response(200, text="<html></html>")
        return httpx.Response(200, json=dolu)

    ozet = backfill(
        istemci=istemci_kur(islevci),
        arsiv=HamArsiv(tmp_path),
        baslangic=date(2026, 1, 1),
        bitis=date(2026, 1, 1),
    )

    assert ozet.tasan_pencereler == [(date(2026, 1, 1), date(2026, 1, 1))]


# -------------------------------------------------------- finansal raporlar


def fr_kaydi(indeks: int, kodlar: str, konu: str = "Finansal Rapor") -> dict:
    return {
        "disclosureIndex": indeks,
        "subject": konu,
        "stockCodes": kodlar,
        "disclosureClass": "FR",
    }


def test_finansal_adaylari_yalniz_hedef_sirketleri_secer():
    """111 şirketimiz var, BIST'te 550'den fazla; gerisi indirilmemeli."""
    kayitlar = [fr_kaydi(1, "ORGE"), fr_kaydi(2, "THYAO")]

    assert finansal_adaylari(kayitlar, {"ORGE"}) == [1]


def test_finansal_adaylari_sorumluluk_beyanini_almaz():
    """Aynı FR sınıfında rapor dışı bildirimler de var; gelir tablosu taşımazlar."""
    kayitlar = [fr_kaydi(1, "ORGE", konu="Sorumluluk Beyanı (Konsolide)")]

    assert finansal_adaylari(kayitlar, {"ORGE"}) == []


def test_finansal_adaylari_cok_kodlu_kayitta_her_kodu_dener():
    """KAP çift paylı şirketleri 'MRBAS, MRS' diye tek alanda veriyor."""
    kayitlar = [fr_kaydi(1, "MRBAS, MRS")]

    assert finansal_adaylari(kayitlar, {"MRS"}) == [1]


def _fr_detayi(indeks: int) -> httpx.Response:
    return httpx.Response(
        200,
        json=[
            {
                "disclosure": {"disclosureBasic": {"disclosureIndex": indeks}},
                "disclosureBody": [
                    "<table class='tbl_general_role_210015'>bilanço</table>",
                    "<table class='tbl_general_role_310000'>gelir tablosu</table>",
                    "<table class='tbl_general_role_610000'>dipnotlar</table>",
                ],
            }
        ],
    )


def test_finansal_backfill_yalniz_gelir_tablosunu_arsivler(tmp_path):
    """Raporun beş parçasının dördü hiç açılmıyor; hepsini saklamak ~2 GB eder."""
    arsiv = HamArsiv(tmp_path)
    islevci, _ = sahte_kap([fr_kaydi(1649471, "ORGE")], detay_islevci=_fr_detayi)

    finansal_backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 8, 13),
        bitis=date(2026, 8, 13),
        tickerlar={"ORGE"},
    )

    kayit = arsiv.finansal_oku(1649471)
    assert "gelir tablosu" in kayit["gelirTablosu"]
    assert "dipnotlar" not in kayit["gelirTablosu"]


def test_finansal_backfill_arsivdekini_yeniden_cekmez(tmp_path):
    """İkinci koşu ücretsiz olmalı: 900 raporluk çekim yarıda kalabilir."""
    arsiv = HamArsiv(tmp_path)
    islevci, istekler = sahte_kap([fr_kaydi(1649471, "ORGE")], detay_islevci=_fr_detayi)
    args = dict(
        arsiv=arsiv,
        baslangic=date(2026, 8, 13),
        bitis=date(2026, 8, 13),
        tickerlar={"ORGE"},
    )

    finansal_backfill(istemci=istemci_kur(islevci), **args)
    finansal_backfill(istemci=istemci_kur(islevci), **args)

    assert detay_istekleri(istekler) == [1649471]


def test_finansal_backfill_gelir_tablosuz_raporu_ozette_bildirir(tmp_path):
    """Sessizce atlanırsa o şirketin paydası sebepsiz boş kalır."""

    def gelir_tablosuz(indeks: int) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "disclosure": {"disclosureBasic": {"disclosureIndex": indeks}},
                    "disclosureBody": ["<table class='tbl_general_role_210015'>x</table>"],
                }
            ],
        )

    islevci, _ = sahte_kap([fr_kaydi(1, "ORGE")], detay_islevci=gelir_tablosuz)

    ozet = finansal_backfill(
        istemci=istemci_kur(islevci),
        arsiv=HamArsiv(tmp_path),
        baslangic=date(2026, 8, 13),
        bitis=date(2026, 8, 13),
        tickerlar={"ORGE"},
    )

    assert ozet.gelir_tablosuz == [1]


def test_liste_penceresi_dusse_bile_kosu_devam_eder(tmp_path):
    """WAF tek bir pencerede ısırdı diye 20 dakikalık çekim çöpe gitmemeli.

    Detay hataları zaten tolere ediliyordu; liste hatası koşuyu
    ortasından kesiyordu ve o noktaya kadar indirilen her şey özetsiz
    kalıyordu. Eksik pencere özete yazılır, ikinci koşu onu tekrar dener.
    """
    dusen = {"2026-01-04"}

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path != LISTE_YOLU:
            return httpx.Response(200, text="<html></html>")
        govde = json.loads(istek.content)
        if govde["fromDate"] in dusen:
            return httpx.Response(503)
        return httpx.Response(200, json=[])

    ozet = backfill(
        istemci=istemci_kur(islevci),
        arsiv=HamArsiv(tmp_path),
        baslangic=date(2026, 1, 1),
        bitis=date(2026, 1, 9),
        pencere_gun=3,
    )

    assert ozet.hatali_pencereler == [(date(2026, 1, 4), date(2026, 1, 6))]
    assert ozet.pencere == 3  # kalan pencereler işlendi


# ------------------------------------------------------------ açık pencere


def test_bugunu_iceren_pencere_arsive_yazilmaz(tmp_path):
    """Gün bitmeden yazılan liste yarımdır; arşivlenirse o günün sonraki
    bildirimleri bir daha hiç sorulmaz (canlı koşunun kalıcı deliği)."""
    arsiv = HamArsiv(tmp_path)
    islevci, _ = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        bugun=date(2026, 9, 18),
    )

    assert not arsiv.liste_var_mi(date(2026, 9, 17), date(2026, 9, 18))


def test_dunu_iceren_pencere_de_acik_sayilir(tmp_path):
    """KAP akşam geç saatte de bildirim düşürüyor; sabah koşusu dünü
    yeniden sormalı."""
    arsiv = HamArsiv(tmp_path)
    arsiv.liste_yaz(date(2026, 9, 17), date(2026, 9, 18), [])
    islevci, istekler = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        bugun=date(2026, 9, 19),
    )

    assert [i for i in istekler if i.url.path == LISTE_YOLU] != []


def test_kapanmis_pencere_arsivlenir(tmp_path):
    arsiv = HamArsiv(tmp_path)
    islevci, _ = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        bugun=date(2026, 9, 20),
    )

    assert arsiv.liste_var_mi(date(2026, 9, 17), date(2026, 9, 18))


def test_finansal_backfill_acik_pencereyi_arsivlemez(tmp_path):
    arsiv = HamArsiv(tmp_path)
    islevci, _ = sahte_kap(liste_fixture())

    finansal_backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        tickerlar=set(),
        bugun=date(2026, 9, 18),
    )

    assert not arsiv.liste_var_mi(date(2026, 9, 17), date(2026, 9, 18))


def test_acik_pencere_gecici_klasore_yazilir(tmp_path):
    """Bağlam hesabı en taze bildirimi görebilsin diye (ARDYZ 43/44)."""
    arsiv = HamArsiv(tmp_path)
    islevci, _ = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        bugun=date(2026, 9, 18),
    )

    assert arsiv.acik_listeler() == [(date(2026, 9, 17), date(2026, 9, 18))]
    assert arsiv.liste_kayitlari() != {}


def test_kapanan_pencerenin_gecici_dosyasi_silinir(tmp_path):
    arsiv = HamArsiv(tmp_path)
    arsiv.acik_liste_yaz(date(2026, 9, 17), date(2026, 9, 18), [])
    islevci, _ = sahte_kap(liste_fixture())

    backfill(
        istemci=istemci_kur(islevci),
        arsiv=arsiv,
        baslangic=date(2026, 9, 17),
        bitis=date(2026, 9, 18),
        bugun=date(2026, 9, 20),
    )

    assert arsiv.acik_listeler() == []
    assert arsiv.liste_var_mi(date(2026, 9, 17), date(2026, 9, 18))
