"""X paylaşımı: tweet metni, OAuth imzası, istemci.

İmza vektörleri oauthlib 3.x ile üretildi (2026-09-25) — kendi
uygulamamızı kendi çıktısıyla sınamamak için. İlki X belgesinin
"Creating a signature" örneği.
"""

import json
from decimal import Decimal

import httpx
import pytest

from kap_radar.x_paylasim import (
    MAKS_UZUNLUK,
    XAnahtarlari,
    XHatasi,
    XIstemci,
    oauth_basligi,
    tweet_metni,
    x_uzunlugu,
)

KAP_ID = "4028328d9f52dddd01a043a00a8b03ff"


def metin(
    oran: str,
    karsi_taraf: str | None = "Turkcell İletişim Hizmetleri A.Ş.",
    acik: bool | None = True,
    tutar: str | None = None,
) -> str:
    return tweet_metni(
        kap_id=KAP_ID,
        ticker="ORGE",
        ciro_orani=Decimal(oran),
        net_tutar_tl=None if tutar is None else Decimal(tutar),
        karsi_taraf=karsi_taraf,
        karsi_taraf_acik=acik,
    )


# --- tweet metni ------------------------------------------------------------


def test_onaylanan_bicim():
    assert metin("0.0615", tutar="75903345.00") == (
        "$ORGE · 75,9 milyon TL'lik yeni iş = cirosunun %6,2'si · Önemli iş · "
        "Kiminle: Turkcell İletişim Hizmetleri A.Ş. · Yatırım tavsiyesi değildir"
    )


def test_tutar_yoksa_yalniz_oran():
    assert metin("0.0615").startswith("$ORGE · Cirosunun %6,2'si · Önemli iş ·")
    assert metin("0.0615", tutar="0").startswith("$ORGE · Cirosunun %6,2'si ·")


@pytest.mark.parametrize(
    "tutar, beklenen",
    [
        ("55766721950.00", "55,8 milyar TL'lik"),
        ("1101522675.00", "1,1 milyar TL'lik"),
        ("1234567890123", "1.234,6 milyar TL'lik"),
        ("180000000.00", "180,0 milyon TL'lik"),
        ("41682654.15", "41,7 milyon TL'lik"),
        ("850000", "850.000 TL'lik"),
    ],
)
def test_tutar_sitedeki_uzun_tl_bicimiyle(tutar, beklenen):
    assert f"$ORGE · {beklenen} yeni iş = cirosunun " in metin("0.02", tutar=tutar)


def test_link_yok():
    # Linkli gönderi 13 kat pahalı (0,20 $ / 0,015 $); bot linksiz.
    assert "http" not in metin("0.0615")


@pytest.mark.parametrize(
    "oran, beklenen",
    [
        ("0.0231", "%2,3'ü"),
        ("0.376", "%37,6'sı"),
        ("0.40", "%40,0'ı"),
        ("0.0005", "%0,1'i"),
        ("0.019", "%1,9'u"),
        ("12.345", "%1.234,5'i"),
    ],
)
def test_yuzde_eki_son_rakama_uyar(oran, beklenen):
    assert f"Cirosunun {beklenen} ·" in metin(oran)


@pytest.mark.parametrize(
    "oran, kademe",
    [("0.0499", "Rutin iş"), ("0.05", "Önemli iş"), ("0.1499", "Önemli iş"), ("0.15", "Mega iş")],
)
def test_kademe_esikleri_sitedekiyle_ayni(oran, kademe):
    assert f"· {kademe} ·" in metin(oran)


def test_adi_verilmemis_karsi_taraf():
    assert "Kiminle: adı verilmemiş" in metin("0.02", "Uluslararası Müşteri", acik=False)
    assert "Kiminle: adı verilmemiş" in metin("0.02", None, acik=False)


def test_siniflandirilmamis_satir_kanonik_siniflandiriciya_gider():
    # "alan dolu = isim" eski kuralı burada "Uluslararası Müşteri" yazardı.
    assert "Kiminle: adı verilmemiş" in metin("0.02", "Uluslararası Müşteri", acik=None)
    assert "Kiminle: Aselsan" in metin("0.02", "Aselsan Elektronik Sanayi ve Ticaret A.Ş.", acik=None)


def test_harfsiz_deger_isim_sayilmaz():
    assert "Kiminle: adı verilmemiş" in metin("0.02", ".", acik=True)


def test_uzun_ad_kisaltilir_ve_tweet_sinirda_kalir():
    ad = "Çok Uzun Adlı Uluslararası Mühendislik ve Taahhüt Anonim Şirketi Türkiye Şubesi Konsorsiyumu İş Ortaklığı"
    t = metin("12.345", ad, acik=True, tutar="1234567890123")
    assert "…" in t and ad not in t
    assert x_uzunlugu(t) <= MAKS_UZUNLUK


def test_ciro_orani_yoksa_metin_kurulmaz():
    with pytest.raises(ValueError):
        metin("0")


# --- X uzunluğu -------------------------------------------------------------


def test_url_23_sayilir():
    assert x_uzunlugu("a https://kap.calibresolve.com/kap/" + "x" * 40) == 2 + 23


def test_turkce_harf_bir_uc_nokta_iki_sayilir():
    assert x_uzunlugu("şğıİöçü") == 7
    assert x_uzunlugu("…") == 2


# --- OAuth 1.0a -------------------------------------------------------------

# X belgesinde herkese açık yayımlanan ÖRNEK değerler ("Creating a
# signature"); hiçbir hesaba ait değil, yalnız imza algoritmasını sınar.
BELGE_ANAHTARLARI = XAnahtarlari(
    api_key="xvz1evFS4wEEPTGEFPHBog",
    api_secret="kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
    access_token="370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
    access_token_secret="LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE",
)


def imza(baslik: str) -> str:
    return baslik.split('oauth_signature="')[1].split('"')[0]


def test_belgedeki_ornek_imza():
    baslik = oauth_basligi(
        "POST",
        "https://api.twitter.com/1.1/statuses/update.json",
        BELGE_ANAHTARLARI,
        nonce="kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg",
        zaman=1318622958,
        parametreler={
            "include_entities": "true",
            "status": "Hello Ladies + Gentlemen, a signed OAuth request!",
        },
    )
    assert imza(baslik) == "hCtSmYh%2BiHYCEqBWrE7C7hYmtUk%3D"
    assert baslik.startswith("OAuth ")
    assert 'oauth_token="370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb"' in baslik


def test_parametresiz_v2_istegi():
    anahtarlar = XAnahtarlari("ck", "cs", "tk", "ts")
    baslik = oauth_basligi(
        "GET", "https://api.x.com/2/users/me", anahtarlar, nonce="abc123", zaman=1700000000
    )
    assert imza(baslik) == "0KoQVkefh3ooziDMN1E82NbaACk%3D"


def test_gizli_anahtarlar_repr_de_gorunmez():
    r = repr(XAnahtarlari("ck", "gizli-cs", "tk", "gizli-ts"))
    assert "gizli" not in r


# --- istemci ----------------------------------------------------------------


def istemci(isleyici) -> XIstemci:
    return XIstemci(
        XAnahtarlari("ck", "cs", "tk", "ts"),
        transport=httpx.MockTransport(isleyici),
        nonce=lambda: "abc123",
        saat=lambda: 1700000000.0,
    )


def test_gonder_json_govde_ve_imzali_baslik():
    gorulen = {}

    def isleyici(istek: httpx.Request) -> httpx.Response:
        gorulen["yol"] = istek.url.path
        gorulen["govde"] = json.loads(istek.content)
        gorulen["baslik"] = istek.headers["Authorization"]
        return httpx.Response(201, json={"data": {"id": "1840000000000000000", "text": "x"}})

    assert istemci(isleyici).gonder("merhaba") == "1840000000000000000"
    assert gorulen["yol"] == "/2/tweets"
    assert gorulen["govde"] == {"text": "merhaba"}
    assert gorulen["baslik"].startswith("OAuth ") and "oauth_signature=" in gorulen["baslik"]


def test_hata_cevabi_yeniden_denenmez():
    sayac = {"n": 0}

    def isleyici(istek: httpx.Request) -> httpx.Response:
        sayac["n"] += 1
        return httpx.Response(403, json={"detail": "You are not permitted to perform this action."})

    with pytest.raises(XHatasi) as hata:
        istemci(isleyici).gonder("merhaba")
    assert hata.value.durum_kodu == 403
    assert sayac["n"] == 1


def test_ben_kullanici_adini_dondurur():
    def isleyici(istek: httpx.Request) -> httpx.Response:
        assert istek.method == "GET" and istek.url.path == "/2/users/me"
        return httpx.Response(200, json={"data": {"id": "1", "username": "kapradar"}})

    assert istemci(isleyici).ben() == "kapradar"


def test_kimlik_erisim_duzeyini_basliktan_okur():
    """X erişim düzeyini `x-access-level` başlığında veriyor. "read" ise
    gönderim 403 döner: token izin değişikliğinden önce üretilmiş."""

    def isleyici(istek: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": {"id": "1", "username": "kapradar"}},
            headers={"x-access-level": "read-write"},
        )

    assert istemci(isleyici).kimlik() == ("kapradar", "read-write")


def test_kimlik_baslik_yoksa_duzey_bilinmiyor():
    def isleyici(istek: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"id": "1", "username": "kapradar"}})

    assert istemci(isleyici).kimlik() == ("kapradar", None)
