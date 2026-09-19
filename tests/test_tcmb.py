"""TCMB kur çekicisinin testleri.

Fixture gerçek TCMB yanıtı (18.09.2026, bülten 2026/176).

Kurun kaynağı spec §8'in gereği: bildirim tarihli resmî kur kullanılır,
bugünkü kur değil. 2025'te imzalanmış bir sözleşmeyi 2026 kuruyla
çevirmek rakamı şişirir.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from kap_radar.tcmb import KurErisimHatasi, KurIstemcisi, kur_ayristir

FIXTURE = Path(__file__).parent / "fixtures"


def tcmb_xml() -> str:
    return (FIXTURE / "tcmb_20260918.xml").read_text(encoding="utf-8")


# ------------------------------------------------------------ ayrıştırıcı


def test_doviz_alis_kuru_okunur():
    """Alış/satış arasında ~%0.2 fark var; hangisi olduğu sabitlenmeli.

    Döviz alış kuru seçildi: şirketlerin hasılatı TL'ye çevirirken
    kullandığı kur bu, ciro oranının paydasıyla aynı mantık.
    """
    gun = kur_ayristir(tcmb_xml())

    assert gun.kurlar["USD"] == Decimal("48.6116")
    assert gun.kurlar["EUR"] == Decimal("55.7981")


def test_birimi_100_olan_para_birimi_bire_indirgenir():
    """JPY kuru 100 birim üzerinden yayınlanıyor.

    İndirgenmezse yen cinsli bir sözleşme 100 kat büyük görünür.
    """
    gun = kur_ayristir(tcmb_xml())

    assert gun.kurlar["JPY"] == Decimal("0.307666")


def test_kur_tarihi_istenen_gun_degil_yayin_gunu():
    """Hafta sonu istenince önceki iş gününün dosyası dönüyor.

    Tarih yanıttan okunmazsa kur yanlış güne yazılır ve §8'in
    "bildirim tarihli kur" kuralı sessizce bozulur.
    """
    gun = kur_ayristir(tcmb_xml())

    assert gun.tarih == date(2026, 9, 18)


def test_alis_kuru_bos_olan_para_birimi_atlanir():
    """Eski bültenlerde bazı para birimlerinin alış kuru boş geliyor.

    Boş değer 0'a çevrilirse çarpım sessizce sıfırlanır.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Tarih_Date Tarih="18.09.2026">
      <Currency Kod="USD"><Unit>1</Unit><ForexBuying>48.6116</ForexBuying></Currency>
      <Currency Kod="IRR"><Unit>100</Unit><ForexBuying></ForexBuying></Currency>
    </Tarih_Date>"""

    gun = kur_ayristir(xml)

    assert "USD" in gun.kurlar
    assert "IRR" not in gun.kurlar


# ---------------------------------------------------------------- istemci


def istemci_kur(islevci, **kwargs) -> KurIstemcisi:
    kwargs.setdefault("uyku", lambda saniye: None)
    return KurIstemcisi(
        transport=httpx.MockTransport(islevci), istek_araligi_sn=0, **kwargs
    )


def test_tcmb_arsiv_url_bicimini_kullanir():
    """Arşiv yolu YYYYMM/DDMMYYYY.xml — iki farklı tarih biçimi aynı URL'de."""
    yollar: list[str] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        yollar.append(istek.url.path)
        return httpx.Response(200, text=tcmb_xml())

    istemci_kur(islevci).gun(date(2026, 9, 18))

    assert yollar == ["/kurlar/202609/18092026.xml"]


def test_yayin_olmayan_gun_none_dondurur():
    """Hafta sonu ve tatilde TCMB dosya yayınlamıyor: 404 hata değil, veri yokluğu."""

    def islevci(istek: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="<html>Not Found</html>")

    assert istemci_kur(islevci).gun(date(2026, 9, 20)) is None


def test_ham_bulten_metni_arsivlenmek_uzere_dondurulur():
    """Arşive ham XML giriyor.

    Ayrıştırıcı değişirse arşivden yeniden üretilir, TCMB'ye 250 istek
    daha gitmez. Yayın olmayan günde None.
    """

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path.endswith("20092026.xml"):
            return httpx.Response(404, text="<html>Not Found</html>")
        return httpx.Response(200, text=tcmb_xml())

    istemci = istemci_kur(islevci)

    assert istemci.ham(date(2026, 9, 18)).startswith("<?xml")
    assert istemci.ham(date(2026, 9, 20)) is None


def test_sunucu_hatasinda_yeniden_dener():
    """404 veri yokluğu, 503 geçici hata — ikisi karıştırılmamalı."""
    sayac = {"n": 0}

    def islevci(istek: httpx.Request) -> httpx.Response:
        sayac["n"] += 1
        if sayac["n"] < 3:
            raise httpx.ConnectTimeout("gecici")
        return httpx.Response(200, text=tcmb_xml())

    gun = istemci_kur(islevci).gun(date(2026, 9, 18))

    assert sayac["n"] == 3
    assert gun.kurlar["USD"] == Decimal("48.6116")


def test_israrli_hatada_pes_eder():
    def islevci(istek: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("surekli")

    with pytest.raises(KurErisimHatasi):
        istemci_kur(islevci, maks_deneme=3).gun(date(2026, 9, 18))
