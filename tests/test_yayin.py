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


# ---------------------------------------------- B4–B6: sayı neyin sayısı?
# Aşama A sayının metinde geçtiğini denetler, neyin sayısı olduğunu değil.
# 2026-09-26 veri denetiminde 962 skorlu bildirimin 10'unda tutar şirketin
# geliri değildi; hepsi "önemli" ya da "mega" kademesindeydi.

ASTOR_METNI = (
    "Şirketimiz ile Fransa'da yerleşik Trench Group GmbH arasında, güç "
    "transformatörü üretiminde kullanılmak üzere, yüksek gerilim bushing "
    "ürünlerinin teminine ilişkin olarak toplam 53.250.000 EUR tutarında "
    "sözleşme imzalanmıştır."
)
ARDYZ_EDS_METNI = (
    "Şirketimiz, Tokat Erbaa Belediyesi tarafından muhammen bedeli "
    "430.320.000 TL olan EDS İşinin Kiraya Verilmesi ihalesinde, gelir "
    "paylaşımı modeli kapsamında en avantajlı teklifi vererek 10 yıl süreli "
    "ihale sözleşmesini imzalamıştır."
)
TOASO_METNI = (
    "İlgili üretim sözleşmesi uyarınca toplam 256 milyon Euro tutara kadar "
    "yatırım ile 2026'nın üçüncü çeyreğinde hayata geçirilmesi öngörülen proje."
)
ANELE_METNI = (
    "Türkiye'nin yüksek segment turizm yatırımları arasında öne çıkan Maça "
    "Kızı Oteli'nin renovasyonu için 51.916.865 USD tutarında anlaşma "
    "imzalanmıştır."
)
ORGE_REVIZE_METNI = (
    "Devam eden 3.907.628 USD ve 102.633.429 TL (sözleşme döviz kuru ile "
    "213.243.933 TL) tutarındaki sözleşme büyüklüğü, İşveren ile yapılan "
    "anlaşma çerçevesinde, 146.756.067 TL artışla yeni birim fiyatlarla "
    "360.000.000 TL olarak revize edilmiştir."
)


def degerlendir_tek(metin, *kalemler, nitelik=None, insan=False):
    return degerlendir(
        cikarim(*kalemler),
        ham_metin_tr=metin,
        ttm_hasilat=Decimal("30000000000"),
        kur_coz=kur,
        karsi_taraf_acik=True,
        guncelleme_mi=False,
        karsi_taraf_niteligi=nitelik,
        insan_denetimli=insan,
    )


ASTOR_KALEMI = Tutar(
    deger=Decimal("53250000"),
    para_birimi="EUR",
    tip="tek_seferlik",
    alinti="toplam 53.250.000 EUR tutarında",
)


def test_karsi_taraf_tedarikciyse_elle_kuyruga_duser():
    """ASTOR 2026-01-30: şirket bushing SATIN ALIYOR; %9 'önemli iş' sanıldı."""
    sonuc = degerlendir_tek(ASTOR_METNI, ASTOR_KALEMI, nitelik="Tedarikçi (Supplier)")

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B4")


def test_tedarikci_ama_tutarsiz_bildirim_yayinlanir():
    """Tutar yoksa büyüklük iddiası da yok; yön sorusu önemsiz."""
    sonuc = degerlendir_tek(ASTOR_METNI, nitelik="Tedarikçi (Supplier)")

    assert sonuc.karar is Karar.YAYINLA


def test_muhammen_bedel_elle_kuyruga_duser():
    """ARDYZ 2026-09-25: 430 mn TL idarenin tahmini, şirketin geliri değil."""
    sonuc = degerlendir_tek(
        ARDYZ_EDS_METNI,
        Tutar(
            deger=Decimal("430320000"),
            para_birimi="TRY",
            tip="tek_seferlik",
            alinti="muhammen bedeli 430.320.000 TL",
        ),
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B5")


def test_yatirim_tutari_elle_kuyruga_duser():
    """TOASO 2025-09-08: 256 mn EUR şirketin kendi yatırımı."""
    sonuc = degerlendir_tek(
        TOASO_METNI,
        Tutar(
            deger=Decimal("256000000"),
            para_birimi="EUR",
            tip="tek_seferlik",
            alinti="256 milyon Euro tutara kadar yatırım",
        ),
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B5")


def test_yatirim_sozcugu_baska_anlamda_gecerse_yayinlanir():
    """ANELE: 'turizm yatırımları arasında' otelin niteliği, tutar değil."""
    sonuc = degerlendir_tek(
        ANELE_METNI,
        Tutar(
            deger=Decimal("51916865"),
            para_birimi="USD",
            tip="tek_seferlik",
            alinti="51.916.865 USD tutarında anlaşma",
        ),
    )

    assert sonuc.karar is Karar.YAYINLA


def test_artis_ve_yeni_toplam_birlikte_sayilirsa_elle_kuyruga_duser():
    """ORGE 2025-03-18: 360 mn = 213,2 mn (eski) + 146,8 mn (artış)."""
    sonuc = degerlendir_tek(
        ORGE_REVIZE_METNI,
        Tutar(
            deger=Decimal("146756067"),
            para_birimi="TRY",
            tip="ilave_siparis",
            alinti="146.756.067 TL artışla",
        ),
        Tutar(
            deger=Decimal("360000000"),
            para_birimi="TRY",
            tip="tek_seferlik",
            alinti="360.000.000 TL olarak revize edilmiştir",
        ),
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B6")


def test_insan_denetimli_satir_anlam_kapisini_atlar():
    """Elle onaylanmış çıkarım B4–B6'ya yeniden takılmamalı; aritmetik
    kapıları (A, B1–B3) yine koşar."""
    sonuc = degerlendir_tek(
        ASTOR_METNI, ASTOR_KALEMI, nitelik="Tedarikçi (Supplier)", insan=True
    )

    assert sonuc.karar is Karar.YAYINLA
