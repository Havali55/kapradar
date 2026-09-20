"""Çıkarım şeması ve doğrulama kapısının testleri (spec §6).

Kapı katı: bir kalem düşerse bildirimin tamamı düşer, kısmi yayın yok
(karar 2026-09-18). Yanlış-red kabul edilen maliyet — yanlış bir sayının
bir kez yayınlanması bu ürüne güveni tek başına bitirir.

Metinler gerçek bildirimlerden alındı; sentetik cümlelerle kurulan kapı
asıl tuzakları (çok para birimli ORGE, aynı tutarı iki para biriminde
tekrarlayan ARDYZ) hiç görmezdi.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from kap_radar.cikarim import (
    CikarimMeta,
    Karar,
    Tutar,
    TutarCikarimi,
    katmanli_cikar,
    metin_kapisi,
    normalize,
    prompt_kur,
    sayilari_bul,
    tutarlilik_kapisi,
)

# ORGE 1665567 — ilave sipariş + fiyat farkı + revize toplam sözleşme
ORGE_METNI = (
    "Şirketimizin devam eden işleri arasında yer alan Pendik-Fevzi Çakmak "
    "Metro Projesi'nde 863.000 EUR+KDV tutarında ilave sipariş alınmıştır.\n"
    "Öte yandan, İşveren ile yapılan fiyat farkı anlaşması çerçevesinde "
    "44.645.758 TL+KDV tutarında fiyat farkı alınacaktır.\n"
    "Bu çerçevede, projenin 9.979.903 EUR+KDV ve 133.751.712 TL+KDV "
    "tutarındaki sözleşme büyüklüğü, yeni birim fiyatlarla 10.842.903 "
    "EUR+KDV ve 178.397.470 TL+KDV olarak revize edilmiştir."
)

# ARDYZ 1664397 — aynı tutar iki para biriminde, satır sonlarıyla bölünmüş
ARDYZ_METNI = (
    "Şirketimiz, son kullanıcısı bir kamu kurumu olan proje kapsamında, "
    "özel bir şirketten KDV dahil 1.040.400 USD (\n50.613.963 TL\n) "
    "tutarında sipariş almıştır."
)


def tutar(
    deger: str,
    para: str = "EUR",
    tip: str = "ilave_siparis",
    alinti: str = "863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
) -> Tutar:
    return Tutar(deger=Decimal(deger), para_birimi=para, tip=tip, alinti=alinti)


def cikarim(**degisiklik) -> TutarCikarimi:
    varsayilan = dict(
        tutarlar=[tutar("863000")],
        tutar_gizli=False,
        hap_ozet=["İlave sipariş", "Metro projesi", "863 bin EUR"],
        guven="yuksek",
    )
    return TutarCikarimi(**{**varsayilan, **degisiklik})


# ------------------------------------------------------------ normalizasyon


def test_noktasiz_i_indirgemesi_manset_sirketlerde_eslesir():
    """`'YAZILIM'.casefold()` → 'yazilim', `'Yazılım'.casefold()` → 'yazılım'.

    İndirgeme olmazsa eşleşme tam da Türkçe şirket adlarında sessizce
    başarısız olur (spec §6 normalizasyon notu).
    """
    assert normalize("ARDYZ YAZILIM") == normalize("Ardyz Yazılım")


def test_binlik_ayiraci_yazimlari_esitlenir():
    """Aynı sayı üç ayrı yazımla geliyor; kapı üçünü de aynı görmeli."""
    assert normalize("45.200.000") == normalize("45,200,000") == normalize("45 200 000")


def test_satir_sonlari_ve_fazla_bosluk_daraltilir():
    assert normalize("1.040.400 USD (\n50.613.963 TL\n)") == normalize(
        "1040400 USD ( 50613963 TL )"
    )


# ------------------------------------------------------- A1: alıntı gerçek mi


def test_metinde_olmayan_alinti_reddedilir():
    """Halüsinasyon kapısı: alıntı ham metinde yoksa çıkarım düşer."""
    sonuc = metin_kapisi(
        cikarim(tutarlar=[tutar("863000", alinti="1.500.000 EUR tutarında sipariş")]),
        ORGE_METNI,
    )

    assert sonuc.karar is Karar.YUKSELT
    assert sonuc.red_nedeni.startswith("A1")


def test_yazim_farki_olan_gercek_alinti_kabul_edilir():
    """Normalizasyon sonrası eşleşme: boşluk, büyük harf, ayraç farkı sorun değil."""
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar("863000", alinti="863000 EUR+KDV   TUTARINDA İLAVE SİPARİŞ")
            ]
        ),
        ORGE_METNI,
    )

    assert sonuc.karar is Karar.YAYINLA


def test_satir_sonuyla_bolunmus_alinti_kabul_edilir():
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "1040400",
                    para="USD",
                    alinti="KDV dahil 1.040.400 USD ( 50.613.963 TL ) tutarında",
                )
            ]
        ),
        ARDYZ_METNI,
    )

    assert sonuc.karar is Karar.YAYINLA


# --------------------------------------------------- A2/A3: sayı ve para birimi


def test_alintidaki_sayiyla_uyusmayan_deger_reddedilir():
    sonuc = metin_kapisi(cikarim(tutarlar=[tutar("8630000")]), ORGE_METNI)

    assert sonuc.red_nedeni.startswith("A2")


def test_alintidaki_para_birimiyle_uyusmayan_etiket_reddedilir():
    """Çok para birimli bildirimde asıl hata kaynağı burası."""
    sonuc = metin_kapisi(cikarim(tutarlar=[tutar("863000", para="TRY")]), ORGE_METNI)

    assert sonuc.red_nedeni.startswith("A3")


# ------------------------------------------------------- A4/A5/A6: tutarlılık


def test_tutar_gizli_derken_tutar_vermek_celiskidir():
    sonuc = metin_kapisi(cikarim(tutar_gizli=True), ORGE_METNI)

    assert sonuc.red_nedeni.startswith("A4")


def test_ayni_para_ve_tipte_iki_kalem_belirsizdir():
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar("863000"),
                tutar(
                    "9979903",
                    alinti="projenin 9.979.903 EUR+KDV ve 133.751.712 TL+KDV",
                ),
            ]
        ),
        ORGE_METNI,
    )

    assert sonuc.red_nedeni.startswith("A5")


def test_dusuk_guvenli_cikarim_yukseltilir():
    sonuc = metin_kapisi(cikarim(guven="dusuk"), ORGE_METNI)

    assert sonuc.karar is Karar.YUKSELT
    assert sonuc.red_nedeni.startswith("A6")


def test_tutar_aciklanmamis_bildirim_kapidan_gecer():
    """Tutarsız bildirim yayınlanabilir; yalnız skoru olmaz (spec §8)."""
    sonuc = metin_kapisi(cikarim(tutarlar=[], tutar_gizli=True), ORGE_METNI)

    assert sonuc.karar is Karar.YAYINLA


def test_gercek_cok_kalemli_orge_cikarimi_gecer():
    """Uçtan uca: ilave sipariş + fiyat farkı + revize toplam bir arada."""
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar("863000"),
                tutar(
                    "44645758",
                    para="TRY",
                    tip="fiyat_farki",
                    alinti="44.645.758 TL+KDV tutarında fiyat farkı alınacaktır",
                ),
                tutar(
                    "10842903",
                    para="EUR",
                    tip="toplam_sozlesme",
                    alinti="yeni birim fiyatlarla 10.842.903 EUR+KDV",
                ),
            ]
        ),
        ORGE_METNI,
    )

    assert sonuc.karar is Karar.YAYINLA


# ---------------------------------------------------- Aşama B: tutarlılık kapısı


def test_iki_kati_ciroyu_asan_oran_elle_kuyruga_duser():
    sonuc = tutarlilik_kapisi(ciro_orani=Decimal("2.5"), kur_bulundu=True)

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B1")


def test_kur_bulunamayan_bildirim_elle_kuyruga_duser():
    """Aşama B'de yükseltme yok: bu model hatası değil, veri şüphesi."""
    sonuc = tutarlilik_kapisi(ciro_orani=None, kur_bulundu=False)

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B2")


def test_ayni_tutarin_iki_para_biriminde_tekrari_elle_kuyruga_duser():
    """ARDYZ tuzağı: '1.040.400 USD (50.613.963 TL)' tek sipariş, iki kalem değil.

    İkisi de sayılırsa net tutar ikiye katlanır. A5 yakalamaz — para
    birimleri farklı. TL karşılıkları birbirine yakınsa mükerrer sayılır.
    """
    sonuc = tutarlilik_kapisi(
        ciro_orani=Decimal("0.1"),
        kur_bulundu=True,
        tl_kalemler=[
            ("ilave_siparis", Decimal("50613963")),
            ("ilave_siparis", Decimal("50613963")),
        ],
    )

    assert sonuc.karar is Karar.ELLE
    assert sonuc.red_nedeni.startswith("B3")


def test_temiz_bildirim_yayina_gecer():
    sonuc = tutarlilik_kapisi(ciro_orani=Decimal("0.023"), kur_bulundu=True)

    assert sonuc.karar is Karar.YAYINLA


# ------------------------------------------------------------------- şema


def test_hap_ozet_uc_madde_olmali():
    with pytest.raises(ValueError):
        cikarim(hap_ozet=["tek madde"])


def test_taninmayan_tutar_tipi_reddedilir():
    with pytest.raises(ValueError):
        tutar("100", tip="bagis")


# ------------------------------------------------------- katmanlı yönlendirme


class SahteCikarici:
    """Sabit bir çıkarım döndüren çıkarıcı (spec §7 protokolü).

    Adım 9 LLM'siz bitiyor: kapı, şema ve yönlendirme gerçek zincirle
    test ediliyor, sağlayıcı yerine bu duruyor.
    """

    def __init__(self, cevap: TutarCikarimi, model: str, katman: int) -> None:
        self._cevap = cevap
        self._meta = CikarimMeta(
            model=model, katman=katman, prompt_versiyon="v1", sema_versiyon="v1"
        )
        self.cagri = 0

    def cikar(self, ham_metin: str) -> tuple[TutarCikarimi, CikarimMeta]:
        self.cagri += 1
        return self._cevap, self._meta


def test_ilk_katman_geciyorsa_ikinci_katman_hic_cagrilmaz():
    """Hacmin ~%85'i burada bitmeli; boşuna pahalı model çalıştırılmaz."""
    ucuz = SahteCikarici(cikarim(), "flash-lite", 1)
    pahali = SahteCikarici(cikarim(), "flash", 2)

    sonuc = katmanli_cikar(ORGE_METNI, [ucuz, pahali])

    assert sonuc.kapi.karar is Karar.YAYINLA
    assert sonuc.meta.katman == 1
    assert pahali.cagri == 0


def test_ilk_katman_reddedilirse_ikinci_katmana_yukseltilir():
    kotu = SahteCikarici(cikarim(guven="dusuk"), "flash-lite", 1)
    iyi = SahteCikarici(cikarim(), "flash", 2)

    sonuc = katmanli_cikar(ORGE_METNI, [kotu, iyi])

    assert sonuc.kapi.karar is Karar.YAYINLA
    assert sonuc.meta.katman == 2


def test_son_katman_da_reddederse_elle_kuyruga_duser():
    """Kapıdan geçmeyen hiçbir çıkarım yayınlanmaz (spec §6)."""
    kotu = SahteCikarici(cikarim(guven="dusuk"), "flash-lite", 1)
    daha_kotu = SahteCikarici(cikarim(guven="dusuk"), "flash", 2)

    sonuc = katmanli_cikar(ORGE_METNI, [kotu, daha_kotu])

    assert sonuc.kapi.karar is Karar.ELLE
    assert sonuc.kapi.red_nedeni.startswith("A6")
    assert sonuc.yayina_hazir is False


# --------------------------------------------------------- çarpan sözcükleri


def test_milyon_ve_milyar_carpanlari_cozulur():
    """CVKMD 1494067: '25,02 milyon ABD Doları (Yaklaşık 1,04 milyar TRY)'.

    Çarpan sözcüğü okunmazsa A2 kapısı `deger=25020000` ile alıntıdaki
    '25,02'yi karşılaştırır ve gerçek bir çıkarımı halüsinasyon sanıp
    reddeder. Arşivde bu yazımı kullanan bildirimler var.
    """
    assert sayilari_bul("25,02 milyon ABD Doları") == [Decimal("25020000")]
    assert sayilari_bul("Yaklaşık 1,04 milyar TRY") == [Decimal("1040000000")]


def test_carpansiz_sayi_oldugu_gibi_kalir():
    assert sayilari_bul("863.000 EUR+KDV") == [Decimal("863000")]


def test_carpan_sozcuklu_alinti_kapidan_gecer():
    metin = (
        "bağlı ortaklığımıza 25,02 milyon ABD Doları (Yaklaşık 1,04 milyar TRY) "
        "tutarında sözleşme imzalamıştır."
    )
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "25020000",
                    para="USD",
                    tip="tek_seferlik",
                    alinti="25,02 milyon ABD Doları",
                )
            ]
        ),
        metin,
    )

    assert sonuc.karar is Karar.YAYINLA


# ------------------------------------------------- yazılı para birimi adları


def test_ek_almis_para_birimi_adlari_eslesir():
    """ODINE 1498996: '639.000 Amerikan Doları'dır'.

    Türkçe çekim ekleri ('Doları', 'Lirasıdır') kelime sınırını kaydırıyor.
    Sözlük ek almış hâlleri tanımazsa arşivdeki bildirimlerin büyük kısmı
    A3'ten döner — şirketler 'USD' yerine sık sık 'Amerikan Doları' yazıyor.
    """
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "639000",
                    para="USD",
                    tip="tek_seferlik",
                    alinti="639.000 Amerikan Doları",
                )
            ]
        ),
        "toplam sözleşme bedeli 639.000 Amerikan Doları'dır.",
    )

    assert sonuc.karar is Karar.YAYINLA


def test_avro_yazimi_eur_sayilir():
    """ASELS 1515178: 'toplam tutarı 1.122.139.260 Avro olan yeni sözleşmeler'."""
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "1122139260",
                    para="EUR",
                    alinti="toplam tutarı 1.122.139.260 Avro",
                )
            ]
        ),
        "arasında toplam tutarı 1.122.139.260 Avro olan yeni sözleşmeler imzalanmıştır.",
    )

    assert sonuc.karar is Karar.YAYINLA


def test_turk_lirasi_yazimi_try_sayilir():
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "26596778",
                    para="TRY",
                    tip="toplam_sozlesme",
                    alinti="26.596.778 Türk Lirası",
                )
            ]
        ),
        "kuruna göre 26.596.778 Türk Lirası).",
    )

    assert sonuc.karar is Karar.YAYINLA


def test_sayiya_bitisik_para_kodu_taninir():
    """CWENE 1502725: 'KDV hariç 2.974.771,80USD(İkiMilyon...)'.

    Kelime sınırı (`\b`) rakamdan sonra gelmiyor: '80usd' dizisinde 'usd'
    solunda rakam var. Sınır harflere göre kurulmalı, kelime karakterine
    göre değil.
    """
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "2974771.80",
                    para="USD",
                    tip="tek_seferlik",
                    alinti="KDV hariç 2.974.771,80USD",
                )
            ]
        ),
        "belirtilen, KDV hariç 2.974.771,80USD(İkiMilyonDokuzYüz...) tutarındaki sözleşmenin",
    )

    assert sonuc.karar is Karar.YAYINLA


def test_kelime_icindeki_tl_dizisi_para_birimi_sayilmaz():
    """'atlanmıştır' içinde 'tl' geçiyor; sınır harflere göre korunmalı."""
    sonuc = metin_kapisi(
        cikarim(
            tutarlar=[
                tutar(
                    "863000",
                    para="TRY",
                    alinti="863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
                )
            ]
        ),
        ORGE_METNI,
    )

    assert sonuc.red_nedeni.startswith("A3")


# ------------------------------------------------------------------ prompt


def test_prompt_semadaki_her_alani_adiyla_istiyor():
    """Şemada olup prompt'ta geçmeyen alan sessizce boş gelir.

    `tip` etiketi buna en açık örnek: prompt onu istemezse model her
    tutarı aynı kovaya atar ve toplam sözleşme bedeli skora karışır.
    """
    metin = prompt_kur("örnek bildirim metni")

    for alan in ("tutarlar", "deger", "para_birimi", "tip", "alinti",
                 "tutar_gizli", "hap_ozet", "guven"):
        assert alan in metin, alan


def test_prompt_ham_metni_gomuyor():
    assert "örnek bildirim metni" in prompt_kur("örnek bildirim metni")


def test_prompt_tip_secenekierinin_tamamini_sayiyor():
    metin = prompt_kur("x")

    for tip in ("ilave_siparis", "fiyat_farki", "toplam_sozlesme", "tek_seferlik"):
        assert tip in metin, tip


def test_prompt_carpan_sozcuklerinin_acilmasini_istiyor():
    """Pilot koşusunda model '25,02 milyon' için deger=25.02 yazdı.

    Kapı bunu A2'den reddetti — doğru davranış, çünkü 25,02 ile
    25.020.000 arasında bir milyon kat fark var. Ama asıl kusur
    prompt'ta: çarpanı açma kuralı yazılı değildi.
    """
    metin = prompt_kur("x")

    assert "milyon" in metin
    assert "25020000" in metin


def test_prompt_tip_ayrimini_ifadeye_degil_anlama_baglar():
    """v2 koşusunda 3 bildirimde skor silindi: şirket yeni bir sözleşme için
    'toplam sözleşme bedeli' yazınca model toplam_sozlesme dedi ve o kalem
    skora hiç girmedi (ODINE 1498996/1571457, OZATD 1492195).

    Ayrım Türkçe ifadeye değil 'yeni kazanılan iş mi' sorusuna bağlanmalı.
    """
    metin = prompt_kur("x")

    assert "YENİ kazanılan işi mi" in metin
    assert "639.000" in metin  # yeni sözleşmeyi 'toplam bedel' diye yazan örnek


def test_prompt_sirketin_odedigi_bedeli_ornekle_disliyor():
    """DGATE 1491549: 8.000.000 USD sözleşme DEVİR bedeli gelir sanıldı."""
    metin = prompt_kur("x")

    assert "8.000.000" in metin


def test_prompt_cevrimin_parantez_disinda_da_olabilecegini_soyluyor():
    """CWENE 1502725: TL karşılığı ayrı satırdaydı, model ikinci kalem saydı."""
    metin = prompt_kur("x")

    assert "parantez içinde olmasa" in metin
