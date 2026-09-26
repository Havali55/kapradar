"""Veri denetiminin saf kontrolleri (`scripts/veri_denetimi.py`).

Kapı yayına girecek satırı tek tek denetler; denetim betiği ise yayındaki
bütün veri setine bakar ve kapının göremediği ya da henüz karar
bekleyen durumları raporlar. Yöntem ve 2026-09-26 bulguları:
`docs/arastirma/2026-09-26-veri-denetimi.md`.
"""

from __future__ import annotations

import re
from typing import Sequence

from kap_radar.cikarim import normalize

__all__ = ["kdv_dahil_mi", "ozette_metinde_olmayan_sayi"]

_KDV_DAHIL = re.compile(r"kdv\s*(dahil|dâhil)")
_SAYI = re.compile(r"\d+(?:[.,]\d+)*")


def kdv_dahil_mi(alinti: str) -> bool:
    """Tutar KDV dahil mi? Ciro KDV hariç; oran ~%20 şişer (bilinen sapma)."""
    return bool(_KDV_DAHIL.search(normalize(alinti)))


def ozette_metinde_olmayan_sayi(ozet: Sequence[str], metin: str) -> str | None:
    """Özetteki, metinde karşılığı olmayan ilk sayı; yoksa None.

    Yalnız tam kısım aranır: özet "272,1 milyon TL" diye yuvarlayabilir,
    metin "272.098.214,40 TL" der (KBORU). Tek haneli sayılar denetlenmez.
    """
    duz = normalize(metin)
    for madde in ozet:
        for belirtec in _SAYI.findall(madde):
            tam = re.sub(r"\.", "", belirtec.split(",")[0])
            if len(tam) >= 2 and tam not in duz:
                return belirtec
    return None
