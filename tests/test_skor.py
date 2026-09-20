"""Etki skoru, tepki paneli ve tahta bayrağının testleri (Adım 10).

Formül `docs/arastirma/2026-09-19-skor-formulu-onerisi.md` — Hüseyin
2026-09-20'de onayladı. Spec §8'in eski toplamsal formülünün yerini
aldı; kanıt taraması o formülün üç varsayımını çürütmüştü.

Ölçek sabitleri testte açıkça yazılı: formül değişirse bu sayılar
değişmeli, sessizce kaymamalı.
"""

from __future__ import annotations

from decimal import Decimal

from kap_radar.cikarim import Tutar
from kap_radar.skor import (
    TahtaBayragi,
    buyukluk_skoru,
    f_oran,
    guvenilirlik,
    net_tutar_tl,
    tahta_bayragi,
    tepki_paneli,
)


def tl_kuru(para_birimi: str) -> Decimal | None:
    """Bildirim tarihli TCMB alış kuru yerine sabit test kuru."""
    return {
        "TRY": Decimal("1"),
        "EUR": Decimal("55.7981"),
        "USD": Decimal("48.6535"),
    }.get(para_birimi)


def tutar(deger: str, para: str, tip: str) -> Tutar:
    return Tutar(deger=Decimal(deger), para_birimi=para, tip=tip, alinti="x")


# ---------------------------------------------------------- f(r) ölçeği


def test_taban_altindaki_oran_sifir_verir():
    """%1'in altı 'olay değil' sayılıyor — ölçeğin tabanı."""
    assert f_oran(Decimal("0.005")) == Decimal("0")


def test_tavan_ustundeki_oran_bire_doyar():
    """%100'ü geçen oran daha fazla ayrım taşımıyor."""
    assert f_oran(Decimal("3")) == Decimal("1")


def test_logaritmik_olcek_onaylanan_tabloya_uyar():
    """Materyallik çarpımsal: %1→%2 ile %10→%20 aynı şeyi söyler.

    Onaylanan ölçek: %2,31→0,91 · %5→1,75 · %20→3,25 · %50→4,25 (K=1).
    (%2,31 ORGE'nin gerçek oranı; tablodaki "%2,3" onun yuvarlanmışı.)
    """
    olculen = [
        round(5 * f_oran(Decimal(oran)), 2)
        for oran in ("0.0231", "0.05", "0.20", "0.50")
    ]

    assert olculen == [Decimal("0.91"), Decimal("1.75"), Decimal("3.25"), Decimal("4.25")]


# ------------------------------------------------------ K: güvenilirlik


def test_acik_karsi_tarafli_ilk_aciklama_tam_puan_alir():
    assert guvenilirlik(karsi_taraf_acik=True, guncelleme_mi=False) == Decimal("1.00")


def test_gizli_karsi_tarafli_guncelleme_en_dusuk_carpani_alir():
    assert guvenilirlik(karsi_taraf_acik=False, guncelleme_mi=True) == Decimal("0.50")


def test_guvenilirlik_carpimsal_buyuklugu_ezmez():
    """Gizli karşı taraflı dev sözleşme hâlâ büyüktür, sadece daha az güvenilir.

    Toplamsal olsaydı güvenilirlik büyüklüğü ezerdi (ya da tersi).
    """
    dev = buyukluk_skoru(
        net_tutar_tl=Decimal("1000"),
        ttm_hasilat=Decimal("1000"),  # ciro oranı %100 → tavan
        karsi_taraf_acik=False,
        guncelleme_mi=True,
    )

    assert dev == Decimal("2.50")  # 5 × 1,00 × 0,50


# --------------------------------------------------------- net tutar TL


def test_toplam_sozlesme_net_tutara_girmez():
    """ORGE'de karıştırılsa ciro oranı ~12 kat şişerdi (spec §8)."""
    kalemler = [
        tutar("863000", "EUR", "ilave_siparis"),
        tutar("44645758", "TRY", "fiyat_farki"),
        tutar("10842903", "EUR", "toplam_sozlesme"),
    ]

    net = net_tutar_tl(kalemler, tl_kuru)

    assert net == Decimal("92799518.30")  # 863.000 × 55,7981 + 44.645.758


def test_kuru_bulunamayan_kalem_net_tutari_dusurur():
    """Eksik kuru 0 saymak toplamı sessizce küçültürdü; None döner (§6 B2).

    TCMB bülteninde olmayan para birimi şemada DIGER etiketiyle geliyor.
    """
    kalemler = [tutar("1000", "DIGER", "ilave_siparis")]

    assert net_tutar_tl(kalemler, tl_kuru) is None


def test_tutar_yoksa_net_tutar_sifir_degil_none():
    assert net_tutar_tl([], tl_kuru) is None


# ------------------------------------------------------------ skor


def test_orge_bildiriminin_skoru_ucten_uca_dogrulanir():
    """Gerçek veriyle doğrulanmış örnek: ORGE 1665567.

    net 92.799.518 TL / TTM 4.023.377.103 TL = %2,31 → f=0,181,
    karşı taraf açık + güncelleme → K=0,85 → skor 0,77/5.
    """
    skor = buyukluk_skoru(
        net_tutar_tl=Decimal("92799518.30"),
        ttm_hasilat=Decimal("4023377103"),
        karsi_taraf_acik=True,
        guncelleme_mi=True,
    )

    assert skor == Decimal("0.77")


def test_tutar_yoksa_skor_gosterilmez():
    """Eski formüldeki 2,5 tabanı kalktı: tutarsız bildirim 'orta etki' değil.

    Veri bunların olay olmadığını söylüyor; skor yerine etiket konur.
    """
    assert (
        buyukluk_skoru(
            net_tutar_tl=None,
            ttm_hasilat=Decimal("4023377103"),
            karsi_taraf_acik=True,
            guncelleme_mi=False,
        )
        is None
    )


def test_hasilat_yoksa_skor_gosterilmez():
    """Payda tahmin edilmez (spec §8)."""
    assert (
        buyukluk_skoru(
            net_tutar_tl=Decimal("92799518"),
            ttm_hasilat=None,
            karsi_taraf_acik=True,
            guncelleme_mi=False,
        )
        is None
    )


def test_skor_bes_ustune_cikmaz():
    skor = buyukluk_skoru(
        net_tutar_tl=Decimal("50000000000"),
        ttm_hasilat=Decimal("1000000"),
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert skor == Decimal("5.00")


# --------------------------------------------------------- tepki paneli


def test_panel_medyan_ve_ceyreklikleri_verir():
    """Ortalama tek başına yayınlanmaz: 20 günlük ortalamalar medyanlarla çelişiyor."""
    panel = tepki_paneli(
        [Decimal(d) for d in ("-0.05", "-0.01", "0.01", "0.02", "0.10")]
    )

    assert panel.n == 5
    assert panel.medyan == Decimal("0.01")
    assert panel.alt_ceyrek == Decimal("-0.01")
    assert panel.ust_ceyrek == Decimal("0.02")
    assert panel.pozitif_orani == Decimal("0.6")


def test_bos_kumede_panel_uretilmez():
    assert tepki_paneli([]) is None


# -------------------------------------------------------- tahta bayrağı


def test_hic_devre_kesici_gormeyen_hisse_temiz():
    assert tahta_bayragi(v90=0, v5=0) is TahtaBayragi.TEMIZ


def test_seyrek_tedbirli_hisse_hareketli():
    assert tahta_bayragi(v90=4, v5=1) is TahtaBayragi.HAREKETLI


def test_bildirim_oncesi_iki_devre_kesici_tedbirli():
    """En güçlü istatistiksel sinyal bu: 3 günlük tepki −2,48 puan.

    Skora girmiyor — bildirimin değil hissenin özelliği (formül §3).
    """
    assert tahta_bayragi(v90=3, v5=2) is TahtaBayragi.TEDBIRLI


def test_cok_sik_devre_kesici_goren_hisse_tedbirli():
    assert tahta_bayragi(v90=9, v5=0) is TahtaBayragi.TEDBIRLI
