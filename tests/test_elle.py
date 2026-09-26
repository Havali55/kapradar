"""Elle kararların (`data/elle_duzeltmeler.json`) çıkarıma uygulanması.

Kapının anlam kontrolleri (B4–B6) şüpheli bildirimi elle kuyruğa atıyor;
kuyruğu boşaltan şey buradaki kararlar. Karar repoda duruyor, gerekçesiyle
birlikte: bir sayının neden değiştiği git geçmişinden okunabilmeli.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from kap_radar.elle import ElleKarar, elle_veri, kararlari_oku

FORTE_VERI = {
    "tutarlar": [
        {"deger": "927690", "para_birimi": "USD", "tip": "ilave_siparis",
         "alinti": "927.690,00 USD artış"},
        {"deger": "7112290.00", "para_birimi": "USD", "tip": "tek_seferlik",
         "alinti": "7.112.290,00 USD olarak güncellenmiştir"},
    ],
    "tutar_gizli": False,
    "hap_ozet": ["a", "b", "c"],
    "guven": "yuksek",
}


def karar(**alanlar) -> ElleKarar:
    varsayilan = dict(kap_id="k1", ticker="FORTE", karar="onayla", neden="gerekce")
    return ElleKarar(**{**varsayilan, **alanlar})


def test_skorsuz_karar_tutarlari_bosaltir_ozeti_korur():
    veri = elle_veri(karar(karar="skorsuz"), FORTE_VERI)

    assert veri["tutarlar"] == []
    assert veri["hap_ozet"] == ["a", "b", "c"]


def test_duzelt_karari_eslesen_kalemin_tipini_degistirir():
    """FORTE 2024-11-18: 7.112.290 USD artıştan sonraki yeni toplam."""
    veri = elle_veri(
        karar(karar="duzelt", yeni_tipler={"7112290": "toplam_sozlesme"}),
        FORTE_VERI,
    )

    assert [t["tip"] for t in veri["tutarlar"]] == ["ilave_siparis", "toplam_sozlesme"]


def test_duzelt_kalem_bulamazsa_hata_verir():
    """Yazım hatalı bir değer sessizce hiçbir şeyi değiştirmemeli."""
    with pytest.raises(ValueError, match="7112291"):
        elle_veri(
            karar(karar="duzelt", yeni_tipler={"7112291": "toplam_sozlesme"}),
            FORTE_VERI,
        )


def test_elle_ozet_llm_ozetinin_yerine_gecer():
    veri = elle_veri(karar(hap_ozet=("x", "y", "z")), FORTE_VERI)

    assert veri["hap_ozet"] == ["x", "y", "z"]


def test_taban_veri_degismez():
    elle_veri(karar(karar="skorsuz"), FORTE_VERI)

    assert len(FORTE_VERI["tutarlar"]) == 2


def test_onayla_cikarimi_aynen_birakir():
    assert elle_veri(karar(), FORTE_VERI) == FORTE_VERI


def yaz(tmp_path, kayitlar):
    yol = tmp_path / "elle.json"
    yol.write_text(json.dumps({"kararlar": kayitlar}), encoding="utf-8")
    return yol


def test_dosya_okunur(tmp_path):
    yol = yaz(tmp_path, [
        {"kap_id": "k1", "ticker": "FORTE", "karar": "duzelt", "neden": "n",
         "yeni_tipler": {"7112290": "toplam_sozlesme"}},
    ])

    (k,) = kararlari_oku(yol)

    assert k.karar == "duzelt"
    assert k.yeni_tipler == {"7112290": "toplam_sozlesme"}


@pytest.mark.parametrize(
    "kayit, mesaj",
    [
        ({"kap_id": "k1", "ticker": "T", "karar": "sil", "neden": "n"}, "karar"),
        ({"kap_id": "k1", "ticker": "T", "karar": "onayla", "neden": " "}, "neden"),
        ({"kap_id": "k1", "ticker": "T", "karar": "duzelt", "neden": "n"}, "yeni_tipler"),
        ({"kap_id": "k1", "ticker": "T", "karar": "duzelt", "neden": "n",
          "yeni_tipler": {"1": "gelir"}}, "tip"),
        ({"kap_id": "k1", "ticker": "T", "karar": "onayla", "neden": "n",
          "hap_ozet": ["tek"]}, "hap_ozet"),
    ],
)
def test_gecersiz_karar_reddedilir(tmp_path, kayit, mesaj):
    with pytest.raises(ValueError, match=mesaj):
        kararlari_oku(yaz(tmp_path, [kayit]))


def test_ayni_bildirime_iki_karar_reddedilir(tmp_path):
    kayit = {"kap_id": "k1", "ticker": "T", "karar": "onayla", "neden": "n"}
    with pytest.raises(ValueError, match="k1"):
        kararlari_oku(yaz(tmp_path, [kayit, kayit]))


def test_deger_ondalik_yazimdan_bagimsiz_eslesir():
    """JSON'da '7112290.00' saklı, kararda '7112290' yazıldı."""
    assert Decimal("7112290.00") == Decimal("7112290")
    veri = elle_veri(
        karar(karar="duzelt", yeni_tipler={"7112290.0": "toplam_sozlesme"}),
        FORTE_VERI,
    )
    assert veri["tutarlar"][1]["tip"] == "toplam_sozlesme"
