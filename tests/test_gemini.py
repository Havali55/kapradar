"""Gemini çıkarıcı adaptörünün testleri.

Hiçbiri ağa çıkmıyor ve hiçbiri para harcamıyor: gerçek `GeminiCikarici`
httpx.MockTransport üzerinden sürülüyor. Test edilen şey modelin
zekâsı değil **adaptör sözleşmesi** — istek doğru kuruluyor mu, yanıt
şemaya doğru çözülüyor mu, geçici hata yeniden deneniyor mu.

Sağlayıcı bağımlılığı burada başlayıp burada bitiyor (spec §7): kapı,
şema, skor ve CAR hesabı Gemini'den habersiz.
"""

from __future__ import annotations

import json

import httpx
import pytest

from kap_radar.cikarim import PROMPT_VERSIYON, SEMA_VERSIYON, TutarCikarimi
from kap_radar.gemini import (
    GEMINI_KOK,
    YANIT_SEMASI,
    GeminiCikarici,
    GeminiHatasi,
)

ORGE_METNI = (
    "Pendik-Fevzi Çakmak Metro Projesi'nde 863.000 EUR+KDV tutarında "
    "ilave sipariş alınmıştır."
)

GECERLI_CIKTI = {
    "tutarlar": [
        {
            "deger": 863000,
            "para_birimi": "EUR",
            "tip": "ilave_siparis",
            "alinti": "863.000 EUR+KDV tutarında ilave sipariş alınmıştır",
        }
    ],
    "tutar_gizli": False,
    "hap_ozet": ["İlave sipariş", "Metro projesi", "863 bin EUR"],
    "guven": "yuksek",
}


def gemini_yaniti(govde: dict) -> httpx.Response:
    """Gemini'nin gerçek yanıt zarfı: metin, parts içinde bir JSON dizesi."""
    return httpx.Response(
        200,
        json={
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(govde, ensure_ascii=False)}]}}
            ]
        },
    )


def cikarici_kur(islevci, **kwargs) -> GeminiCikarici:
    return GeminiCikarici(
        api_anahtari="test-anahtar",
        model="gemini-3.1-flash-lite",
        katman=1,
        transport=httpx.MockTransport(islevci),
        uyku=lambda saniye: None,
        istek_araligi_sn=0,
        **kwargs,
    )


def test_bildirim_metni_prompt_icinde_gonderiliyor():
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return gemini_yaniti(GECERLI_CIKTI)

    cikarici_kur(islevci).cikar(ORGE_METNI)

    govde = json.loads(istekler[0].content)
    prompt = govde["contents"][0]["parts"][0]["text"]
    assert "863.000 EUR+KDV" in prompt


def test_yapilandirilmis_cikti_semasi_istekte_yer_aliyor():
    """Şema gönderilmezse model serbest metin döndürür ve JSON çözümü kırılır."""
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return gemini_yaniti(GECERLI_CIKTI)

    cikarici_kur(islevci).cikar(ORGE_METNI)

    ayar = json.loads(istekler[0].content)["generationConfig"]
    assert ayar["responseMimeType"] == "application/json"
    assert ayar["responseSchema"] == YANIT_SEMASI
    # Aynı bildirimin iki koşuda aynı çıkarımı vermesi için.
    assert ayar["temperature"] == 0


def test_api_anahtari_baslikta_gidiyor_url_de_degil():
    """URL'deki anahtar proxy ve sunucu günlüklerine düşer."""
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return gemini_yaniti(GECERLI_CIKTI)

    cikarici_kur(islevci).cikar(ORGE_METNI)

    assert istekler[0].headers["x-goog-api-key"] == "test-anahtar"
    assert "test-anahtar" not in str(istekler[0].url)


def test_model_adi_uc_noktasinda():
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return gemini_yaniti(GECERLI_CIKTI)

    cikarici_kur(islevci).cikar(ORGE_METNI)

    assert istekler[0].url.path.endswith(
        "/models/gemini-3.1-flash-lite:generateContent"
    )
    assert str(istekler[0].url).startswith(GEMINI_KOK)


def test_yanit_cikarim_semasina_cozuluyor():
    cikarim, _ = cikarici_kur(lambda i: gemini_yaniti(GECERLI_CIKTI)).cikar(ORGE_METNI)

    assert isinstance(cikarim, TutarCikarimi)
    assert cikarim.tutarlar[0].deger == 863000
    assert cikarim.tutarlar[0].para_birimi == "EUR"
    assert cikarim.guven == "yuksek"


def test_meta_model_katman_ve_surumleri_tasiyor():
    """`cikarim` tablosu versiyonlu: hangi sayıyı ne üretti sorulabilmeli."""
    _, meta = cikarici_kur(lambda i: gemini_yaniti(GECERLI_CIKTI)).cikar(ORGE_METNI)

    assert meta.model == "gemini-3.1-flash-lite"
    assert meta.katman == 1
    assert meta.prompt_versiyon == PROMPT_VERSIYON
    assert meta.sema_versiyon == SEMA_VERSIYON


def test_aday_dondurmeyen_yanit_sessizce_yutulmaz():
    """Boş yanıt 'tutar yok' değildir; sessizce kabul edilirse veri kaybı olur."""
    with pytest.raises(GeminiHatasi):
        cikarici_kur(lambda i: httpx.Response(200, json={"candidates": []})).cikar(
            ORGE_METNI
        )


def test_semaya_uymayan_cikti_hata_veriyor():
    bozuk = {**GECERLI_CIKTI, "guven": "cok_yuksek"}

    with pytest.raises(GeminiHatasi):
        cikarici_kur(lambda i: gemini_yaniti(bozuk)).cikar(ORGE_METNI)


def test_gecici_sunucu_hatasi_yeniden_deneniyor():
    """429 ve 5xx geçici; tek seferde pes etmek 613 bildirimlik koşuyu keser."""
    cagri = {"n": 0}

    def islevci(istek: httpx.Request) -> httpx.Response:
        cagri["n"] += 1
        if cagri["n"] < 3:
            return httpx.Response(429)
        return gemini_yaniti(GECERLI_CIKTI)

    cikarim, _ = cikarici_kur(islevci).cikar(ORGE_METNI)

    assert cagri["n"] == 3
    assert cikarim.tutarlar[0].deger == 863000


def test_sema_pydantic_modeliyle_ayni_alanlari_istiyor():
    """El yazımı şema ile pydantic modeli birbirinden kaymamalı.

    Şemada olmayan alanı model asla doldurmaz; modelde olmayan alanı
    şema isterse doğrulama düşer. İkisi de sessiz bozulma.
    """
    assert set(YANIT_SEMASI["properties"]) == set(TutarCikarimi.model_fields)

    kalem = YANIT_SEMASI["properties"]["tutarlar"]["items"]
    from kap_radar.cikarim import Tutar

    assert set(kalem["properties"]) == set(Tutar.model_fields)


def test_token_kullanimi_metaya_yaziliyor():
    """Harcama izne bağlı: gerçek token sayısı tahmine bırakılamaz.

    Gemini `usageMetadata` içinde veriyor; kaydedilmezse koşu sonrası
    'ne kadar tuttu' sorusunun cevabı yeniden tahmin olurdu.
    """
    def islevci(istek: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(GECERLI_CIKTI)}]}}
                ],
                "usageMetadata": {
                    "promptTokenCount": 812,
                    "candidatesTokenCount": 118,
                },
            },
        )

    _, meta = cikarici_kur(islevci).cikar(ORGE_METNI)

    assert meta.girdi_token == 812
    assert meta.cikti_token == 118


def test_token_bilgisi_yoksa_meta_bos_kalir():
    """Sayı yoksa sıfır yazılmaz: 'bilinmiyor' ile 'sıfır' aynı şey değil."""
    _, meta = cikarici_kur(lambda i: gemini_yaniti(GECERLI_CIKTI)).cikar(ORGE_METNI)

    assert meta.girdi_token is None
    assert meta.cikti_token is None


def test_hap_ozet_semada_tam_uc_madde_isteniyor():
    """Pilot koşusunda (2026-09-20) model 2 madde döndürdü ve iki bildirim
    şema doğrulamasından düştü.

    pydantic `min_length=3` diyordu ama Gemini'ye gönderilen şemada
    madde sayısı hiç yazmıyordu; model bilmediği kuralı tutturamaz.
    """
    ozet = YANIT_SEMASI["properties"]["hap_ozet"]

    assert ozet["minItems"] == 3
    assert ozet["maxItems"] == 3
