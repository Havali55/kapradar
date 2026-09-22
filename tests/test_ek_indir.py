"""KAP ek indirme yanıtı: Java serileştirilmiş byte[] içinde PDF."""

from __future__ import annotations

import pytest

from kap_radar.istemci import KapErisimHatasi, java_sarmalini_ac

PDF = b"%PDF-1.4\n...govde...\n%%EOF"
# Gerçek yanıtın başı: AC ED 00 05 75 72 00 02 5B 42 ... + 4 bayt uzunluk.
BASLIK = bytes.fromhex("aced0005757200025b42acf317f8060854e0020000") + len(PDF).to_bytes(4, "big")


def test_sarmal_acilir():
    assert java_sarmalini_ac(BASLIK + PDF) == PDF


def test_duz_pdf_oldugu_gibi_doner():
    assert java_sarmalini_ac(PDF) == PDF


def test_yarim_dosya_hata_verir():
    """Uzunluk alanı tutmuyorsa kesik yanıt diske yazılmamalı."""
    with pytest.raises(KapErisimHatasi):
        java_sarmalini_ac(BASLIK + PDF[:-5])


def test_pdf_olmayan_yanit_hata_verir():
    with pytest.raises(KapErisimHatasi):
        java_sarmalini_ac(b"<!DOCTYPE html><html>WAF</html>")
