"""Altın kümeye karşı doğruluk ölçümünün testleri (spec §10).

Ölçümün kendisi hatalıysa modelin iyi mi kötü mü olduğu bilinemez.
2026-09-20'deki ilk koşuda tam bu oldu: karşılaştırma değerleri metin
olarak kıyasladığı için `2999015.00` ile `2999015` farklı sayıldı ve
50 bildirimin 8'i sebepsiz "yanlış" göründü.
"""

from __future__ import annotations

from decimal import Decimal

from kap_radar.cikarim import Tutar
from kap_radar.dogruluk import Sonuc, kalem_kumesi, karsilastir


def tutar(deger: str, para: str = "USD", tip: str = "tek_seferlik") -> Tutar:
    return Tutar(deger=Decimal(deger), para_birimi=para, tip=tip, alinti="x")


def etiket(deger: str, para: str = "USD", tip: str = "tek_seferlik") -> dict:
    return {"deger": deger, "para_birimi": para, "tip": tip, "alinti": "x"}


def test_ondalik_sifirlari_farki_bozmaz():
    """'2999015.00' ile '2999015' aynı sayı; metin kıyaslaması bunu kaçırır."""
    assert kalem_kumesi([tutar("2999015")]) == kalem_kumesi([etiket("2999015.00")])


def test_ayni_kalemler_tam_dogru_sayilir():
    sonuc = karsilastir([etiket("863000", "EUR", "ilave_siparis")],
                        [tutar("863000", "EUR", "ilave_siparis")])

    assert sonuc is Sonuc.TAM


def test_tip_farki_yanlis_sayilir():
    """Değer doğru ama tip yanlışsa skor yanlış olur: toplam_sozlesme skora girmez."""
    sonuc = karsilastir([etiket("639000")], [tutar("639000", tip="toplam_sozlesme")])

    assert sonuc is Sonuc.YANLIS


def test_fazladan_kalem_yanlis_sayilir():
    """Şirketin ödediği bedeli gelir sanmak net tutarı şişirir."""
    sonuc = karsilastir([], [tutar("8000000")])

    assert sonuc is Sonuc.YANLIS


def test_dogru_kalemin_yaninda_fazlalik_kismi_sayilir():
    """CWENE: doğru USD tutarı + şirketin kendi TL çevrimi ikinci kalem olarak."""
    sonuc = karsilastir(
        [etiket("2974771.80")],
        [tutar("2974771.8"), tutar("123865928.03", para="TRY")],
    )

    assert sonuc is Sonuc.KISMI


def test_bos_beklenen_ve_bos_gelen_tam_dogru():
    """Tutarsız bildirimde boş liste doğru cevaptır."""
    assert karsilastir([], []) is Sonuc.TAM
