"""Çıkarımdan yayın kararına giden tam zincirin testleri.

Adım 9'un kapısı iki aşamalı ama koşucu 2026-09-20'de yalnız A aşamasını
çalıştırıyordu: §8 hesaplarına ihtiyaç duyan B aşaması hiç devreye
girmiyordu. Sonuç, CWENE 1502725'te görüldü — model şirketin kendi TL
çevrimini ikinci kalem sayınca skor 0,08 yerine 0,61 çıktı ve kapı
bunu yakalayamadı, çünkü yakalayacak olan kontrol (B3) koşmuyordu.
"""

from __future__ import annotations

from decimal import Decimal

from kap_radar.cikarim import Karar, Tutar, TutarCikarimi
from kap_radar.yayin import degerlendir

ORGE_METNI = (
    "Pendik-Fevzi Çakmak Metro Projesi'nde 863.000 EUR+KDV tutarında "
    "ilave sipariş alınmıştır."
)

CWENE_METNI = (
    "Söz konusu açıklamada belirtilen, KDV hariç 2.974.771,80USD tutarındaki "
    "sözleşmenin doğru TL karşılığı sözleşme imza tarihi itibarıyla TCMB "
    "USD/TL döviz alış kuru üzerinden KDV hariç toplam 123.865.928,03 TL'dir."
)


def kur(para_birimi: str) -> Decimal | None:
    return {"TRY": Decimal("1"), "EUR": Decimal("55.7981"), "USD": Decimal("41.6382")}.get(
        para_birimi
    )


def cikarim(*kalemler: Tutar) -> TutarCikarimi:
    return TutarCikarimi(
        tutarlar=list(kalemler),
        tutar_gizli=False,
        hap_ozet=["a", "b", "c"],
        guven="yuksek",
    )


def test_temiz_bildirim_skoruyla_birlikte_yayina_gecer():
    sonuc = degerlendir(
        cikarim(
            Tutar(
                deger=Decimal("863000"),
                para_birimi="EUR",
                tip="ilave_siparis",
                alinti="863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
            )
        ),
        ham_metin_tr=ORGE_METNI,
        ttm_hasilat=Decimal("4023377103"),
        kur_coz=kur,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.net_tutar_tl == Decimal("48153760.30")
    # 48,15 mn / 4,02 mr = %1,20 -> f=0,261 -> 5 x 0,261 x 1,00
    # (taban %1'ken f=0,039 ve skor 0,20'ydi; oran aynı, ölçek değişti)
    assert sonuc.etki_skoru == Decimal("1.31")


def test_ayni_tutarin_iki_para_birimindeki_tekrari_yayini_durdurur():
    """CWENE 1502725: 2.974.771,80 USD ve onun TL karşılığı iki kalem sayılmış.

    A5 bunu göremez (para birimleri farklı); B3 görür. Skor 0,08 yerine
    0,61 çıkacakken bildirim elle kuyruğa düşüyor.
    """
    sonuc = degerlendir(
        cikarim(
            Tutar(
                deger=Decimal("2974771.80"),
                para_birimi="USD",
                tip="tek_seferlik",
                alinti="KDV hariç 2.974.771,80USD",
            ),
            Tutar(
                deger=Decimal("123865928.03"),
                para_birimi="TRY",
                tip="tek_seferlik",
                alinti="KDV hariç toplam 123.865.928,03 TL",
            ),
        ),
        ham_metin_tr=CWENE_METNI,
        ttm_hasilat=Decimal("11125249299"),
        kur_coz=kur,
        karsi_taraf_acik=False,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B3")


def test_metin_kapisindan_donen_cikarim_hesaplara_hic_girmez():
    """Aşama A reddi yükseltme ister; §8 hesabı koşturmanın anlamı yok."""
    sonuc = degerlendir(
        cikarim(
            Tutar(
                deger=Decimal("1500000"),
                para_birimi="EUR",
                tip="ilave_siparis",
                alinti="1.500.000 EUR tutarında sipariş",
            )
        ),
        ham_metin_tr=ORGE_METNI,
        ttm_hasilat=Decimal("4023377103"),
        kur_coz=kur,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.YUKSELT
    assert sonuc.red_nedeni.startswith("A1")
    assert sonuc.etki_skoru is None


def test_tutarsiz_bildirim_skorsuz_yayinlanir():
    """Tutar yoksa skor gösterilmez ama bildirim yayınlanabilir (spec §8)."""
    sonuc = degerlendir(
        cikarim(),
        ham_metin_tr=ORGE_METNI,
        ttm_hasilat=Decimal("4023377103"),
        kur_coz=kur,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.etki_skoru is None
    assert sonuc.net_tutar_tl is None


def test_hasilati_bilinmeyen_sirkette_oran_ve_skor_yok():
    """Payda tahmin edilmez; bildirim yine yayınlanır."""
    sonuc = degerlendir(
        cikarim(
            Tutar(
                deger=Decimal("863000"),
                para_birimi="EUR",
                tip="ilave_siparis",
                alinti="863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
            )
        ),
        ham_metin_tr=ORGE_METNI,
        ttm_hasilat=None,
        kur_coz=kur,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.ciro_orani is None
    assert sonuc.etki_skoru is None


def test_kuru_cozulemeyen_kalem_elle_kuyruga_duser():
    """B2: bildirim tarihli kur bulunamadıysa hesap güvenilmez.

    TCMB bülteninde olmayan para birimi şemada DIGER; alıntısında da
    bilinen üç koddan biri geçmemeli, yoksa A3 zaten reddeder.
    """
    sonuc = degerlendir(
        cikarim(
            Tutar(
                deger=Decimal("115000000"),
                para_birimi="DIGER",
                tip="ilave_siparis",
                alinti="Toplam ihale bütçesi 115 milyon GBP",
            )
        ),
        ham_metin_tr="Toplam ihale bütçesi 115 milyon GBP olup sözleşme imzalanmıştır.",
        ttm_hasilat=Decimal("4023377103"),
        kur_coz=lambda p: None,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B2")
