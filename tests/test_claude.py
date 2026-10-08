"""Claude çıkarıcı adaptörünün testleri.

`test_gemini.py` ile aynı sözleşme: hiçbiri ağa çıkmıyor, hiçbiri para
harcamıyor. Gerçek `ClaudeCikarici` httpx.MockTransport üzerinden
sürülüyor; test edilen şey modelin zekâsı değil adaptörün kendisi.
"""

from __future__ import annotations

import json

import httpx
import pytest

from kap_radar.cikarim import PROMPT_VERSIYON, SEMA_VERSIYON, Tutar, TutarCikarimi
from kap_radar.claude import CLAUDE_KOK, YANIT_SEMASI, ClaudeCikarici, ClaudeHatasi

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


def claude_yaniti(govde: dict, **ek) -> httpx.Response:
    """Messages API zarfı: JSON dizesi bir `text` bloğunda, önünde düşünme bloğu."""
    return httpx.Response(
        200,
        json={
            "content": [
                {"type": "thinking", "thinking": "", "signature": "x"},
                {"type": "text", "text": json.dumps(govde, ensure_ascii=False)},
            ],
            "stop_reason": "end_turn",
            **ek,
        },
    )


def cikarici_kur(islevci, **kwargs) -> ClaudeCikarici:
    return ClaudeCikarici(
        api_anahtari="test-anahtar",
        model="claude-sonnet-5",
        katman=1,
        transport=httpx.MockTransport(islevci),
        uyku=lambda saniye: None,
        istek_araligi_sn=0,
        **kwargs,
    )


def kaydeden():
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return claude_yaniti(GECERLI_CIKTI)

    return istekler, islevci


def test_istek_model_prompt_ve_semayi_tasiyor():
    istekler, islevci = kaydeden()
    cikarici_kur(islevci).cikar(ORGE_METNI)

    govde = json.loads(istekler[0].content)
    assert str(istekler[0].url) == CLAUDE_KOK + "/v1/messages"
    assert govde["model"] == "claude-sonnet-5"
    assert "863.000 EUR+KDV" in govde["messages"][0]["content"]
    assert govde["output_config"]["format"] == {
        "type": "json_schema",
        "schema": YANIT_SEMASI,
    }


def test_ornekleme_parametresi_gonderilmiyor():
    """Güncel Claude modelleri `temperature`ı 400 ile reddediyor."""
    istekler, islevci = kaydeden()
    cikarici_kur(islevci).cikar(ORGE_METNI)

    assert "temperature" not in json.loads(istekler[0].content)


def test_api_anahtari_baslikta_gidiyor_url_de_degil():
    istekler, islevci = kaydeden()
    cikarici_kur(islevci).cikar(ORGE_METNI)

    assert istekler[0].headers["x-api-key"] == "test-anahtar"
    assert istekler[0].headers["anthropic-version"] == "2023-06-01"
    assert "test-anahtar" not in str(istekler[0].url)


def test_yanit_cikarim_semasina_cozuluyor_dusunme_blogu_atlaniyor():
    cikarim, _ = cikarici_kur(lambda i: claude_yaniti(GECERLI_CIKTI)).cikar(ORGE_METNI)

    assert isinstance(cikarim, TutarCikarimi)
    assert cikarim.tutarlar[0].deger == 863000
    assert cikarim.guven == "yuksek"


def test_meta_model_katman_surum_ve_token_tasiyor():
    yanit = claude_yaniti(GECERLI_CIKTI, usage={"input_tokens": 812, "output_tokens": 118})
    _, meta = cikarici_kur(lambda i: yanit).cikar(ORGE_METNI)

    assert meta.model == "claude-sonnet-5"
    assert meta.katman == 1
    assert meta.prompt_versiyon == PROMPT_VERSIYON
    assert meta.sema_versiyon == SEMA_VERSIYON
    assert meta.girdi_token == 812
    assert meta.cikti_token == 118


def test_token_bilgisi_yoksa_meta_bos_kalir():
    _, meta = cikarici_kur(lambda i: claude_yaniti(GECERLI_CIKTI)).cikar(ORGE_METNI)

    assert meta.girdi_token is None
    assert meta.cikti_token is None


@pytest.mark.parametrize("durma", ["refusal", "max_tokens"])
def test_reddedilen_ya_da_kesilen_yanit_sessizce_yutulmaz(durma):
    yanit = claude_yaniti(GECERLI_CIKTI, stop_reason=durma)

    with pytest.raises(ClaudeHatasi):
        cikarici_kur(lambda i: yanit).cikar(ORGE_METNI)


def test_metinsiz_yanit_hata_veriyor():
    bos = httpx.Response(200, json={"content": [], "stop_reason": "end_turn"})

    with pytest.raises(ClaudeHatasi):
        cikarici_kur(lambda i: bos).cikar(ORGE_METNI)


def test_semaya_uymayan_cikti_hata_veriyor():
    """Claude'a dizi uzunluğu kısıtı gönderilemiyor; iki maddelik özet
    pydantic'te düşmeli."""
    bozuk = {**GECERLI_CIKTI, "hap_ozet": ["a", "b"]}

    with pytest.raises(ClaudeHatasi):
        cikarici_kur(lambda i: claude_yaniti(bozuk)).cikar(ORGE_METNI)


def test_gecici_asiri_yuk_yeniden_deneniyor():
    """529 (aşırı yük) ve 429 geçici."""
    cagri = {"n": 0}

    def islevci(istek: httpx.Request) -> httpx.Response:
        cagri["n"] += 1
        if cagri["n"] < 3:
            return httpx.Response(529 if cagri["n"] == 1 else 429)
        return claude_yaniti(GECERLI_CIKTI)

    cikarim, _ = cikarici_kur(islevci).cikar(ORGE_METNI)

    assert cagri["n"] == 3
    assert cikarim.tutarlar[0].deger == 863000


def test_sema_pydantic_modeliyle_ayni_alanlari_istiyor():
    assert set(YANIT_SEMASI["properties"]) == set(TutarCikarimi.model_fields)
    kalem = YANIT_SEMASI["properties"]["tutarlar"]["items"]
    assert set(kalem["properties"]) == set(Tutar.model_fields)


def test_her_nesne_ek_alani_kapatiyor():
    """Claude'un yapılandırılmış çıktısı `additionalProperties: false`
    olmayan nesne şemasını kabul etmiyor."""
    assert YANIT_SEMASI["additionalProperties"] is False
    assert YANIT_SEMASI["properties"]["tutarlar"]["items"]["additionalProperties"] is False
