"""Gemini çıkarıcı adaptörü — `Cikarici` protokolünün tek uygulaması.

Sağlayıcı bağımlılığı bu dosyada başlayıp bu dosyada bitiyor (spec §7):
şema, doğrulama kapısı, skor formülü ve CAR hesabı Gemini'den habersiz.
Başka bir sağlayıcıya geçmek bunun bir eşdeğerini yazmak demek.

SDK yerine düz REST kullanılıyor. Sebep: projedeki diğer her çekici
`http_temel.HizSinirliIstemci` üzerinden gidiyor — hız sınırı, üstel
geri çekilme ve zaman aşımı tek yerde yaşıyor. SDK ayrı bir yeniden
deneme mantığı getirirdi ve testler gerçek istemciyi süremezdi.

**Yapılandırılmış çıktı zorunlu.** `responseSchema` gönderilmezse model
serbest metin döndürüyor ve JSON çözümü kırılıyor; şema ile birlikte
çıktı doğrudan `TutarCikarimi`ye çözülebiliyor.
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

GEMINI_KOK = "https://generativelanguage.googleapis.com"
UC_NOKTA = "/v1beta/models/{model}:generateContent"

__all__ = ["GEMINI_KOK", "YANIT_SEMASI", "GeminiCikarici", "GeminiHatasi"]


class GeminiHatasi(ErisimHatasi):
    """Gemini'den kullanılabilir bir çıkarım alınamadı."""


# Gemini'nin `responseSchema`sı OpenAPI alt kümesi; pydantic'in ürettiği
# JSON Schema `$defs`/`anyOf` taşıdığı için olduğu gibi kabul edilmiyor.
# Bu yüzden elle yazılı — `TutarCikarimi` ile aynı alanlara sahip olduğu
# testle bağlanıyor, yoksa ikisi sessizce birbirinden kayar.
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
}

YANIT_SEMASI: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tutarlar": {"type": "array", "items": _TUTAR_SEMASI},
        "tutar_gizli": {"type": "boolean"},
        # Madde sayısı şemada yazmazsa model tutturamaz: 2026-09-20
        # pilotunda iki bildirim 3 yerine 2 madde döndürdüğü için
        # pydantic doğrulamasından düştü.
        "hap_ozet": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "guven": {"type": "string", "enum": ["yuksek", "orta", "dusuk"]},
    },
    "required": ["tutarlar", "tutar_gizli", "hap_ozet", "guven"],
}


class GeminiCikarici(HizSinirliIstemci):
    """Bir bildirimin serbest metninden tutarları çıkarır."""

    HATA_SINIFI: ClassVar[type[ErisimHatasi]] = GeminiHatasi

    def __init__(
        self,
        *,
        api_anahtari: str,
        model: str,
        katman: int,
        **kwargs,
    ) -> None:
        kwargs.setdefault("kok", GEMINI_KOK)
        # Model üretimi KAP'tan yavaş; 30 sn zaman aşımı uzun bildirimlerde
        # yetmiyor ve yeniden denemeyi boşuna tetikliyor.
        kwargs.setdefault("zaman_asimi", 90.0)
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

        Şemaya uymayan ya da boş yanıt hata veriyor, sessizce "tutar yok"a
        indirgenmiyor: boş liste ile başarısız çağrı aynı şey değil ve
        karıştırılırsa gerçek tutarlar sessizce kaybolur.
        """
        yanit = self._dene(lambda: self._cagir(ham_metin))
        return self._coz(yanit), self._kullanimla(yanit)

    def _kullanimla(self, yanit: dict) -> CikarimMeta:
        """Künyeye o çağrının gerçek token sayısını ekler."""
        kullanim = yanit.get("usageMetadata") or {}
        return replace(
            self._meta,
            girdi_token=kullanim.get("promptTokenCount"),
            cikti_token=kullanim.get("candidatesTokenCount"),
        )

    def _cagir(self, ham_metin: str) -> dict:
        cevap = self._oturum.post(
            UC_NOKTA.format(model=self._model),
            json={
                "contents": [{"parts": [{"text": prompt_kur(ham_metin)}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": YANIT_SEMASI,
                    # Aynı bildirim iki koşuda aynı çıkarımı vermeli;
                    # yoksa altın küme ölçümü tekrarlanamaz olur.
                    "temperature": 0,
                },
            },
            headers={
                # Anahtar sorgu dizesinde değil başlıkta: URL proxy ve
                # sunucu günlüklerine düşer.
                "x-goog-api-key": self._api_anahtari,
                "Accept": "application/json",
            },
        )
        # 429 ve 5xx gövdesi geçerli JSON olduğu için `_dene` bunu kendi
        # başına fark etmez; açıkça yükseltiliyor ki yeniden denensin.
        cevap.raise_for_status()
        return cevap.json()

    def _coz(self, yanit: dict) -> TutarCikarimi:
        adaylar = yanit.get("candidates") or []
        if not adaylar:
            neden = yanit.get("promptFeedback") or "aday dönmedi"
            raise GeminiHatasi(f"Gemini kullanılabilir yanıt vermedi: {neden}")

        parcalar = adaylar[0].get("content", {}).get("parts") or []
        metin = "".join(p.get("text", "") for p in parcalar)
        if not metin.strip():
            raise GeminiHatasi("Gemini boş metin döndürdü")

        try:
            return TutarCikarimi.model_validate_json(metin)
        except ValidationError as hata:
            raise GeminiHatasi(f"Yanıt şemaya uymuyor: {hata}") from hata
        except json.JSONDecodeError as hata:
            raise GeminiHatasi(f"Yanıt JSON değil: {metin[:200]!r}") from hata
