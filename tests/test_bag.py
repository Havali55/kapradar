"""Güncelleme ve düzeltme bildirimlerini önceki bildirime bağlama.

2026-09-26 veri denetimi: kamu ihalelerinde şirketler önce "ihale
üzerimizde kaldı", sonra aynı tutarla "sözleşme imzalandı" diyor; ikisi
de skorlanıyordu. PLTUR'un İBB işi (%54) sitede iki ayrı "mega iş"ti.
Düzeltme bildirimi geldiğinde de asıl bildirim yayında kalıyordu
(ONCSM, VBTYZ, KAYSE, BVSAN).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from kap_radar.bag import Bag, BagGirdisi, baglari_kur


def girdi(
    kap_id,
    an,
    *,
    ticker="PLTUR",
    guncelleme=False,
    duzeltme=False,
    onceki=(),
    kalemler=(),
    sayilar=(),
):
    return BagGirdisi(
        kap_id=kap_id,
        ticker=ticker,
        an=an,
        guncelleme_mi=guncelleme,
        duzeltme_mi=duzeltme,
        onceki_tarihler=tuple(onceki),
        kalemler=frozenset((Decimal(d), p) for d, p in kalemler),
        metin_sayilari=frozenset(Decimal(s) for s in sayilar),
    )


IHALE = girdi(
    "ihale", datetime(2025, 12, 8, 18, 0),
    kalemler=[("3375868924.80", "TRY")], sayilar=["3375868924.80"],
)


def test_ayni_tutarli_guncelleme_ayni_is_olarak_baglanir():
    """PLTUR: 08.12.2025 ihale, 29.12.2025 aynı tutarla sözleşme."""
    sozlesme = girdi(
        "sozlesme", datetime(2025, 12, 29, 9, 0), guncelleme=True,
        onceki=[date(2025, 12, 8)],
        kalemler=[("3375868924.80", "TRY")], sayilar=["3375868924.80"],
    )

    assert baglari_kur([IHALE, sozlesme]) == [
        Bag("sozlesme", "ihale", "ayni_is", "kap_tarih")
    ]


def test_farkli_tutarli_guncelleme_yalniz_baglanir():
    """İlave sipariş güncellemesi yeni bir iş: sayılmaya devam eder."""
    ilave = girdi(
        "ilave", datetime(2026, 1, 5, 9, 0), guncelleme=True,
        onceki=[date(2025, 12, 8)], kalemler=[("100000000", "TRY")],
    )

    assert baglari_kur([IHALE, ilave]) == [Bag("ilave", "ihale", "guncelleme", "kap_tarih")]


def test_duzeltme_asil_bildirime_baglanir():
    asil = girdi("asil", datetime(2026, 4, 16, 10, 7), ticker="KAYSE",
                 kalemler=[("5096500000", "TRY")], sayilar=["5096500000"])
    duz = girdi("duz", datetime(2026, 4, 16, 15, 0), ticker="KAYSE", duzeltme=True,
                onceki=[date(2026, 4, 16)],
                kalemler=[("5096500000", "TRY")], sayilar=["5096500000"])

    assert baglari_kur([asil, duz]) == [Bag("duz", "asil", "duzeltme", "kap_tarih")]


def test_ayni_gun_iki_aday_varsa_ortak_tutari_olan_secilir():
    """ALTNY 27.10.2025: 22:10'daki bildirim düzeltilen, 22:11'deki ayrı iş."""
    duzeltilen = girdi("a", datetime(2025, 10, 27, 22, 10), ticker="ALTNY",
                       sayilar=["994950"])
    ayri_is = girdi("b", datetime(2025, 10, 27, 22, 11), ticker="ALTNY",
                    kalemler=[("5950000", "USD")], sayilar=["5950000"])
    duz = girdi("d", datetime(2025, 10, 28, 11, 55), ticker="ALTNY", duzeltme=True,
                onceki=[date(2025, 10, 27)],
                kalemler=[("994950", "USD")], sayilar=["994950"])

    (bag,) = baglari_kur([duzeltilen, ayri_is, duz])

    assert bag.onceki_kap_id == "a"


def test_bildirilen_tarihte_bildirim_yoksa_bag_kurulmaz():
    """MIATK 11.10.2024: düzeltme bayrağı 10.10'u gösteriyor, o gün
    Yeni İş İlişkisi yok. 23.09'daki ilgisiz işe bağlanmamalı."""
    eski = girdi("eski", datetime(2024, 9, 23, 6, 39), ticker="MIATK",
                 kalemler=[("137187769.05", "TRY")], sayilar=["137187769.05"])
    duz = girdi("duz", datetime(2024, 10, 11, 8, 13), ticker="MIATK", duzeltme=True,
                onceki=[date(2024, 10, 10)], kalemler=[("32385184.80", "TRY")])

    assert baglari_kur([eski, duz]) == []


def test_tarih_alani_bossa_ortak_tutarla_baglanir():
    guncel = girdi("g", datetime(2026, 1, 20, 9, 0), guncelleme=True,
                   kalemler=[("3375868924.80", "TRY")], sayilar=["3375868924.80"])

    assert baglari_kur([IHALE, guncel]) == [Bag("g", "ihale", "ayni_is", "tutar")]


def test_bayraksiz_bildirim_ayni_tutarla_bile_baglanmaz():
    """KAYSE 12–13.02.2025: iki ayrı 7,07 mr TL anlaşma ('toplam 14,14 mr')."""
    ikinci = girdi("ikinci", datetime(2026, 1, 20, 9, 0),
                   kalemler=[("3375868924.80", "TRY")], sayilar=["3375868924.80"])

    assert baglari_kur([IHALE, ikinci]) == []


def test_baska_hisseye_baglanmaz():
    guncel = girdi("g", datetime(2025, 12, 29, 9, 0), ticker="ORGE", guncelleme=True,
                   onceki=[date(2025, 12, 8)], kalemler=[("3375868924.80", "TRY")])

    assert baglari_kur([IHALE, guncel]) == []


def test_sonraki_bildirime_baglanmaz():
    """Tarih eşleşse bile önceki bildirim, bildirimden ÖNCE yayınlanmış olmalı."""
    sonra = girdi("sonra", datetime(2025, 12, 8, 20, 0), kalemler=[("5", "TRY")])
    guncel = girdi("g", datetime(2025, 12, 8, 19, 0), guncelleme=True,
                   onceki=[date(2025, 12, 8)])

    assert baglari_kur([sonra, guncel]) == []


def test_tarih_ilk_duyuruyu_gosterse_de_ortak_tutarli_ara_bildirime_baglanir():
    """ONRYT: 11.11.2025 süreç bilgisi (9,6 mn USD), 01.12.2025 sözleşme
    (aynı tutar); ikisinin de 'önceki tarihi' 2024-09-20'deki ilk duyuru."""
    ilk = girdi("ilk", datetime(2024, 9, 20, 10, 0), ticker="ONRYT")
    surec = girdi("surec", datetime(2025, 11, 11, 12, 35), ticker="ONRYT",
                  guncelleme=True, onceki=[date(2024, 9, 20)],
                  kalemler=[("9600000", "USD")], sayilar=["9600000"])
    sozlesme = girdi("soz", datetime(2025, 12, 1, 13, 58), ticker="ONRYT",
                     guncelleme=True, onceki=[date(2024, 9, 20)],
                     kalemler=[("9600000", "USD")], sayilar=["9600000"])

    baglar = baglari_kur([ilk, surec, sozlesme])

    assert Bag("soz", "surec", "ayni_is", "tutar") in baglar
