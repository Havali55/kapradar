"""Claude çıkarıcı adaptörü — `Cikarici` protokolünün ikinci uygulaması.

`gemini.py`nin eşdeğeri (spec §7): şema, doğrulama kapısı, skor formülü
ve CAR hesabı Claude'dan da habersiz. Hangi sağlayıcının koşacağını
`scripts/cikarim_kosu.py` ortam değişkeninden seçiyor.

SDK yerine düz REST, Gemini adaptörüyle aynı sebeple: hız sınırı, üstel
geri çekilme ve zaman aşımı `http_temel.HizSinirliIstemci`de tek yerde
yaşıyor ve testler gerçek istemciyi MockTransport üzerinden sürebiliyor.

**Sıcaklık gönderilmiyor.** Gemini'de `temperature: 0` ile aynı bildirim
iki koşuda aynı çıkarımı veriyordu; güncel Claude modelleri örnekleme
parametrelerini 400 ile reddediyor. Tekrarlanabilirlik bu yüzden
varsayılamaz, altın kümede ölçülmesi gerekir.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, ClassVar

from pydantic import ValidationError

from kap_radar.cikarim import (
    PROMPT_VERSIYON,
    SEMA_VERSIYON,
    CikarimMeta,
    TutarCikarimi,
    prompt_kur,
)
from kap_radar.http_temel import ErisimHatasi, HizSinirliIstemci

CLAUDE_KOK = "https://api.anthropic.com"
UC_NOKTA = "/v1/messages"
API_SURUMU = "2023-06-01"

# Çıktı ~200 token; düşünme bloğu da bu sınırın içinde sayılıyor.
# Sınıra takılan yanıt yarım JSON olur, bu yüzden geniş tutuluyor.
MAKS_TOKEN = 16000

__all__ = ["CLAUDE_KOK", "YANIT_SEMASI", "ClaudeCikarici", "ClaudeHatasi"]


class ClaudeHatasi(ErisimHatasi):
    """Claude'dan kullanılabilir bir çıkarım alınamadı."""


# Claude'un yapılandırılmış çıktısı her nesnede `additionalProperties:
# false` istiyor ve dizi uzunluğu kısıtını (`minItems`/`maxItems`)
# desteklemiyor. `hap_ozet`in tam üç madde olması bu yüzden açıklamada
# ve istemin 12. kuralında yazıyor; pydantic yine de doğruluyor.
_TUTAR_SEMASI: dict[str, Any] = {
    "type": "object",
    "properties": {
        "deger": {"type": "number"},
        "para_birimi": {"type": "string", "enum": ["TRY", "USD", "EUR", "DIGER"]},
        "tip": {
            "type": "string",
            "enum": [
                "ilave_siparis",
                "fiyat_farki",
                "toplam_sozlesme",
                "tek_seferlik",
            ],
        },
        "alinti": {"type": "string"},
    },
    "required": ["deger", "para_birimi", "tip", "alinti"],
    "additionalProperties": False,
}

YANIT_SEMASI: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tutarlar": {"type": "array", "items": _TUTAR_SEMASI},
        "tutar_gizli": {"type": "boolean"},
        "hap_ozet": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tam olarak 3 madde.",
        },
        "guven": {"type": "string", "enum": ["yuksek", "orta", "dusuk"]},
    },
    "required": ["tutarlar", "tutar_gizli", "hap_ozet", "guven"],
    "additionalProperties": False,
}


class ClaudeCikarici(HizSinirliIstemci):
    """Bir bildirimin serbest metninden tutarları çıkarır."""

    HATA_SINIFI: ClassVar[type[ErisimHatasi]] = ClaudeHatasi

    def __init__(
        self,
        *,
        api_anahtari: str,
        model: str,
        katman: int,
        **kwargs,
    ) -> None:
        kwargs.setdefault("kok", CLAUDE_KOK)
        # Düşünme açıkken üretim Gemini'den de yavaş olabiliyor.
        kwargs.setdefault("zaman_asimi", 120.0)
        super().__init__(**kwargs)
        self._api_anahtari = api_anahtari
        self._model = model
        self._meta = CikarimMeta(
            model=model,
            katman=katman,
            prompt_versiyon=PROMPT_VERSIYON,
            sema_versiyon=SEMA_VERSIYON,
        )

    def cikar(self, ham_metin: str) -> tuple[TutarCikarimi, CikarimMeta]:
        """Türkçe bildirim metninden `TutarCikarimi` üretir.

        Reddedilen, yarıda kesilen ya da şemaya uymayan yanıt hata veriyor;
        sessizce "tutar yok"a indirgenmiyor (bkz. `GeminiCikarici.cikar`).
        """
        yanit = self._dene(lambda: self._cagir(ham_metin))
        return self._coz(yanit), self._kullanimla(yanit)

    def _kullanimla(self, yanit: dict) -> CikarimMeta:
        """Künyeye o çağrının gerçek token sayısını ekler."""
        kullanim = yanit.get("usage") or {}
        return replace(
            self._meta,
            girdi_token=kullanim.get("input_tokens"),
            cikti_token=kullanim.get("output_tokens"),
        )

    def _cagir(self, ham_metin: str) -> dict:
        cevap = self._oturum.post(
            UC_NOKTA,
            json={
                "model": self._model,
                "max_tokens": MAKS_TOKEN,
                "messages": [{"role": "user", "content": prompt_kur(ham_metin)}],
                "output_config": {
                    "format": {"type": "json_schema", "schema": YANIT_SEMASI},
                },
            },
            headers={
                "x-api-key": self._api_anahtari,
                "anthropic-version": API_SURUMU,
                "Accept": "application/json",
            },
        )
        # 429, 529 ve 5xx geçici; `_dene` yeniden denesin diye yükseltiliyor.
        cevap.raise_for_status()
        return cevap.json()

    def _coz(self, yanit: dict) -> TutarCikarimi:
        durma = yanit.get("stop_reason")
        if durma == "refusal":
            ayrinti = yanit.get("stop_details") or {}
            raise ClaudeHatasi(f"Claude yanıtı reddetti: {ayrinti}")
        if durma == "max_tokens":
            raise ClaudeHatasi("Claude yanıtı token sınırında kesildi")

        # Düşünme blokları da `content` içinde geliyor; yalnız metin okunur.
        metin = "".join(
            b.get("text", "") for b in yanit.get("content") or [] if b.get("type") == "text"
        )
        if not metin.strip():
            raise ClaudeHatasi("Claude boş metin döndürdü")

        try:
            return TutarCikarimi.model_validate_json(metin)
        except ValidationError as hata:
            raise ClaudeHatasi(f"Yanıt şemaya uymuyor: {hata}") from hata
        except json.JSONDecodeError as hata:
            raise ClaudeHatasi(f"Yanıt JSON değil: {metin[:200]!r}") from hata
