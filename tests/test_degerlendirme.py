"""Kayıtlı bir çıkarımın veritabanı bağlamıyla değerlendirilmesi.

Koşucu (`scripts/cikarim_kosu.py`) ve ölçüm betiği
(`scripts/dogruluk_olc.py`) aynı zinciri kuruyor: TTM'i point-in-time
çöz, kuru bildirim tarihinden al, iki aşamalı kapıyı koştur, skoru
hesapla. Zincir iki yerde ayrı ayrı yazılırsa biri düzeltilip diğeri
unutulur — 2026-09-20'de karşılaştırma mantığında tam bu oldu.

Burada sınanan şey kapının ya da skorun kendisi değil (onların testi
`test_yayin.py`), **bağlamın doğru bağlanması**: hangi tarihin kuru,
hangi ana kadarki raporlar.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from kap_radar.cikarim import Karar
from kap_radar.degerlendirme import (
    cikarimi_kur,
    degerlendir_bildirim,
    kur_cozucu,
)
from kap_radar.finansal import DonemHasilat

ORGE_METNI = (
    "Pendik-Fevzi Çakmak Metro Projesi'nde 863.000 EUR+KDV tutarında "
    "ilave sipariş alınmıştır."
)

ORGE_KAYDI = {
    "tutar_gizli": False,
    "tutarlar": [
        {
            "deger": "863000",
            "para_birimi": "EUR",
            "tip": "ilave_siparis",
            "alinti": "863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
        }
    ],
}

# Gerçek ORGE zinciri: FY2025 + 6A2026 − 6A2025 = TTM 4.023.377.103 TL.
FY2025 = DonemHasilat(
    ticker="ORGE",
    kap_index=1557898,
    yayin_zamani=datetime(2026, 3, 10, tzinfo=timezone.utc),
    donem_basi=date(2025, 1, 1),
    donem_sonu=date(2025, 12, 31),
    ay_sayisi=12,
    hasilat=Decimal("3495512127"),
    onceki_yil_hasilat=None,
    onceki_donem_sonu=None,
    para_birimi="TL",
    konsolide=True,
)
ALTI_AY_2026 = DonemHasilat(
    ticker="ORGE",
    kap_index=1649471,
    yayin_zamani=datetime(2026, 8, 19, tzinfo=timezone.utc),
    donem_basi=date(2026, 1, 1),
    donem_sonu=date(2026, 6, 30),
    ay_sayisi=6,
    hasilat=Decimal("2597519683"),
    onceki_yil_hasilat=Decimal("2069654707"),
    onceki_donem_sonu=date(2025, 6, 30),
    para_birimi="TL",
    konsolide=True,
)

BILDIRIM_ANI = datetime(2026, 9, 1, 18, 30, tzinfo=timezone.utc)


class SahteDepo:
    """`Depo`nun bu zincirde kullanılan iki metodu, ağsız.

    Sorulan kur tarihlerini kaydediyor: point-in-time hatası sessizdir,
    yanlış günün kuruyla çevrilen tutar da makul görünür.
    """

    def __init__(self, donemler=(), kurlar=None):
        self.donemler = list(donemler)
        self.kurlar = dict(kurlar or {})
        self.sorulan: list[tuple[date, str]] = []

    def donem_hasilatlari(self, ticker: str):
        return [d for d in self.donemler if d.ticker == ticker]

    def kur_coz(self, tarih: date, para_birimi: str):
        self.sorulan.append((tarih, para_birimi))
        kur = self.kurlar.get(para_birimi)
        return (tarih, kur) if kur is not None else None


def orge_depo() -> SahteDepo:
    return SahteDepo(
        donemler=[FY2025, ALTI_AY_2026],
        kurlar={"EUR": Decimal("55.7981"), "USD": Decimal("41.6382")},
    )


# ------------------------------------------------------- şemaya çevirme


def test_altin_etiketi_sema_disi_alanlar_olmadan_cevrilir():
    """Elle etiket yalnız tutarları taşır; kapı yine de koşabilmeli."""
    cikarim = cikarimi_kur(ORGE_KAYDI)

    assert cikarim.tutarlar[0].deger == Decimal("863000")
    assert cikarim.tutarlar[0].para_birimi == "EUR"
    assert len(cikarim.hap_ozet) == 3


def test_etikette_guven_yok_diye_A6_reddi_uydurulmaz():
    """Eksik `guven` 'dusuk' sayılırsa altın kümenin tamamı yükseltilir."""
    assert cikarimi_kur(ORGE_KAYDI).guven == "yuksek"


def test_kayitli_cikarimin_kendi_guveni_korunur():
    """Modelin yazdığı düşük güven ölçümde de düşük kalmalı (A6)."""
    veri = dict(ORGE_KAYDI, guven="dusuk", hap_ozet=["a", "b", "c"])

    assert cikarimi_kur(veri).guven == "dusuk"


# ------------------------------------------------------------ kur çözme


def test_kur_cozucu_TRY_icin_depoya_hic_sormaz():
    """TCMB bülteninde Türk Lirası satırı yok; sormak 'kur bulunamadı' üretir."""
    depo = orge_depo()

    assert kur_cozucu(depo, date(2026, 9, 1))("TRY") == Decimal("1")
    assert depo.sorulan == []


def test_kur_cozucu_bilinmeyen_para_birimine_None_verir():
    """DIGER çevrilemez: B2 kapısı bunu elle incelemeye düşürmeli."""
    depo = orge_depo()

    assert kur_cozucu(depo, date(2026, 9, 1))("DIGER") is None
    assert depo.sorulan == []


# ------------------------------------------------------- bağlamın bağlanması


def test_bildirim_tarihli_kur_ve_point_in_time_ttm_baglanir():
    """ORGE 1665567 gerçek zinciri: 863.000 EUR → skor 0,77 değil 0,20.

    (0,77 tüm evrenin gerçek TTM'iyle; buradaki rakamlar `test_yayin`
    ile aynı ki bağlamın kendisi izole sınansın.)
    """
    depo = orge_depo()

    sonuc = degerlendir_bildirim(
        depo,
        cikarim=ORGE_KAYDI,
        ticker="ORGE",
        an=BILDIRIM_ANI,
        ham_metin_tr=ORGE_METNI,
        guncelleme_mi=False,
        karsi_taraf_acik=True,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.net_tutar_tl == Decimal("48153760.30")
    assert sonuc.etki_skoru == Decimal("0.20")
    # Kur bildirimin kendi gününden sorulmalı, bugünden değil.
    assert depo.sorulan == [(date(2026, 9, 1), "EUR")]


def test_bildirimden_sonra_yayinlanan_rapor_paydaya_girmez():
    """Lookahead yasak: o an bilinmeyen hasılatla oran hesaplanamaz."""
    depo = orge_depo()

    sonuc = degerlendir_bildirim(
        depo,
        cikarim=ORGE_KAYDI,
        ticker="ORGE",
        an=datetime(2026, 3, 1, tzinfo=timezone.utc),  # FY2025 henüz yayında değil
        ham_metin_tr=ORGE_METNI,
        guncelleme_mi=False,
        karsi_taraf_acik=True,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.ciro_orani is None
    assert sonuc.etki_skoru is None


def test_finansali_olmayan_sirket_skorsuz_ama_yayinlanabilir():
    """Yeni halka açılan 8 şirket böyle (Adım 7: 613 bildirimin 16'sı)."""
    depo = SahteDepo(donemler=[], kurlar={"EUR": Decimal("55.7981")})

    sonuc = degerlendir_bildirim(
        depo,
        cikarim=ORGE_KAYDI,
        ticker="YENI",
        an=BILDIRIM_ANI,
        ham_metin_tr=ORGE_METNI,
        guncelleme_mi=False,
        karsi_taraf_acik=True,
    )

    assert sonuc.karar is Karar.YAYINLA
    assert sonuc.net_tutar_tl == Decimal("48153760.30")
    assert sonuc.etki_skoru is None
