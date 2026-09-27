"""Söz ve gerçek istatistikleri — sitenin `lib/soz.ts`'iyle aynı fikstür."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from kap_radar.soz_gercek import (
    SozSatiri,
    buyume_donemi_sec,
    onceki_ceyrek,
    ozetle,
    spearman,
)

FIKSTUR = json.loads(
    (Path(__file__).parent / "fixtures" / "soz_gercek.json").read_text(encoding="utf-8")
)
BEKLENEN = FIKSTUR["beklenen"]


def satirlar() -> list[SozSatiri]:
    return [SozSatiri(**s) for s in FIKSTUR["satirlar"]]


def test_uc_esit_grup_yogunluga_gore_artan_son_gruba():
    ozet = ozetle(satirlar())

    assert [[s.ticker for s in g.satirlar] for g in ozet.gruplar] == (
        BEKLENEN["grup_tickerlari"]
    )


def test_grup_medyanlari():
    ozet = ozetle(satirlar())

    assert [g.medyan_buyume for g in ozet.gruplar] == pytest.approx(
        BEKLENEN["medyan_buyume"]
    )
    assert [g.medyan_yogunluk for g in ozet.gruplar] == pytest.approx(
        BEKLENEN["medyan_yogunluk"]
    )


def test_spearman_t_ve_ust_grup():
    ozet = ozetle(satirlar())

    assert ozet.n == BEKLENEN["n"]
    assert ozet.rho == pytest.approx(BEKLENEN["rho"])
    assert ozet.t == pytest.approx(BEKLENEN["t"])
    assert ozet.ust_grup_onde is BEKLENEN["ust_grup_onde"]


def test_esit_degerler_ortalama_sira_alir():
    e = FIKSTUR["spearman_esitlik"]

    assert spearman(e["x"], e["y"]) == pytest.approx(e["rho"])


def test_girdi_sirasi_sonucu_degistirmez():
    assert ozetle(list(reversed(satirlar()))) == ozetle(satirlar())


def test_ust_grup_farki_esigi_gecmezse_onde_denmez():
    """Üst grup 0,16, ortanın medyanı 0,15: bir puan fark 'belirgin' değil."""
    ornek = [
        SozSatiri(s.ticker, s.yogunluk, 0.16 if s.ticker in {"EEE", "FFF", "GGG"} else s.buyume)
        for s in satirlar()
    ]

    assert ozetle(ornek).ust_grup_onde is False


def test_uc_satirdan_azla_ozet_kurulmaz():
    assert ozetle(satirlar()[:2]) is None


def test_donem_secimi_raporlama_sezonunu_bekler():
    """9A2026'da 12 şirket raporlamış: sezon sürüyor, 6A2026 seçilir."""
    kapsam = {date.fromisoformat(k): v for k, v in FIKSTUR["kapsam"].items()}

    assert buyume_donemi_sec(kapsam) == date.fromisoformat(FIKSTUR["beklenen_donem"])


def test_donem_secimi_ceyrek_sonu_olmayani_saymaz():
    """Özel hesap yılı (Temmuz sonu) dönem adayı değil."""
    assert buyume_donemi_sec({date(2026, 7, 31): 50, date(2026, 6, 30): 40}) == date(
        2026, 6, 30
    )


def test_onceki_ceyrek_yil_sinirini_gecer():
    assert onceki_ceyrek(date(2026, 3, 31)) == date(2025, 12, 31)
    assert onceki_ceyrek(date(2026, 9, 30)) == date(2026, 6, 30)
