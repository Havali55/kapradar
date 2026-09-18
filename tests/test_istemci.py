"""KAP HTTP istemcisinin testleri.

Hiçbiri ağa çıkmaz: httpx.MockTransport ile sahte yanıt, enjekte edilen
uyku fonksiyonuyla sahte zaman kullanılır.

Buradaki kurallar Adım 0'da ampirik olarak öğrenildi (spec §9): oturum
ısıtması, Referer ve dürüst User-Agent olmadan WAF bağlantıyı düşürüyor.
"""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from kap_radar.istemci import KapErisimHatasi, KapIstemcisi

LISTE_YOLU = "/tr/api/disclosure/members/byCriteria"
ISITMA_YOLU = "/tr/bildirim-sorgu"


class SahteSaat:
    """Yalnızca uyku ile ilerleyen saat.

    Gerçek geçen süre hep sıfır sayıldığı için, iki istek arasında bekleme
    varsa bunu kesinlikle hız sınırlayıcı koymuştur.
    """

    def __init__(self) -> None:
        self.simdi = 0.0
        self.uykular: list[float] = []

    def __call__(self) -> float:
        return self.simdi

    def uyu(self, saniye: float) -> None:
        self.uykular.append(saniye)
        self.simdi += saniye


def istemci_kur(islevci, **kwargs) -> KapIstemcisi:
    """Ağa çıkmayan, beklemeyen bir istemci kurar."""
    kwargs.setdefault("uyku", lambda saniye: None)
    return KapIstemcisi(transport=httpx.MockTransport(islevci), **kwargs)


def test_ilk_api_isteginden_once_oturum_isitir():
    """Isıtma olmadan WAF bağlantıyı düşürüyor (Adım 0 bulgusu)."""
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        if istek.url.path == ISITMA_YOLU:
            return httpx.Response(200, text="<html></html>")
        return httpx.Response(200, json=[])

    istemci_kur(islevci).liste(date(2026, 9, 17), date(2026, 9, 18))

    assert istekler[0].method == "GET"
    assert istekler[0].url.path == ISITMA_YOLU
    assert istekler[1].url.path == LISTE_YOLU


def test_api_istegine_referer_ve_user_agent_ekler():
    """Üçü birden olmazsa WAF düşürüyor; ikisi başlık, biri ısıtma."""
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        return httpx.Response(200, json=[])

    istemci_kur(islevci, user_agent="kap-radar/test (+posta@ornek.com)").liste(
        date(2026, 9, 17), date(2026, 9, 18)
    )

    liste_istegi = next(i for i in istekler if i.url.path == LISTE_YOLU)
    assert liste_istegi.headers["referer"].endswith(ISITMA_YOLU)
    assert liste_istegi.headers["user-agent"] == "kap-radar/test (+posta@ornek.com)"


def test_oturum_yalnizca_bir_kez_isitilir():
    """Her istekte ısıtmak gereksiz trafik üretir ve hız bütçesini yer."""
    yollar: list[str] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        yollar.append(istek.url.path)
        return httpx.Response(200, json=[])

    istemci = istemci_kur(islevci)
    istemci.liste(date(2026, 9, 17), date(2026, 9, 17))
    istemci.liste(date(2026, 9, 18), date(2026, 9, 18))

    assert yollar.count(ISITMA_YOLU) == 1


def test_ardisik_istekler_arasinda_hiz_siniri_bekler():
    """Adım 0'da ardışık tarama WAF'a takıldı; hız sınırı koda gömülü olmalı."""
    saat = SahteSaat()
    istemci = KapIstemcisi(
        transport=httpx.MockTransport(lambda istek: httpx.Response(200, json=[])),
        uyku=saat.uyu,
        saat=saat,
        istek_araligi_sn=0.5,
    )

    istemci.liste(date(2026, 9, 17), date(2026, 9, 17))
    istemci.liste(date(2026, 9, 18), date(2026, 9, 18))

    # 3 istek (ısıtma + 2 liste) -> aradaki 2 boşlukta bekleme olmalı
    beklemeler = [u for u in saat.uykular if u > 0]
    assert len(beklemeler) == 2
    assert all(u == pytest.approx(0.5) for u in beklemeler)


def test_ilk_istek_beklemeden_gider():
    """Boşta duran poller'ın ilk isteği gecikmemeli."""
    saat = SahteSaat()
    istemci = KapIstemcisi(
        transport=httpx.MockTransport(lambda istek: httpx.Response(200, json=[])),
        uyku=saat.uyu,
        saat=saat,
        istek_araligi_sn=0.5,
    )

    istemci.liste(date(2026, 9, 17), date(2026, 9, 17))

    # 2 istek gitti (ısıtma + liste). İlki beklediyse 2 bekleme olurdu.
    assert saat.uykular == [pytest.approx(0.5)]


def dusen_sonra_basaran(dusus_sayisi: int, sonuc: list[dict]):
    """İlk `dusus_sayisi` liste isteğinde bağlantıyı düşüren sahte sunucu."""
    sayac = {"n": 0}

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path != LISTE_YOLU:
            return httpx.Response(200, text="<html></html>")
        sayac["n"] += 1
        if sayac["n"] <= dusus_sayisi:
            raise httpx.ConnectTimeout("WAF baglantiyi dusurdu")
        return httpx.Response(200, json=sonuc)

    return islevci, sayac


def test_gecici_hatada_yeniden_dener_ve_sonucu_dondurur():
    """WAF bağlantıyı düşürdüğünde iş kaybolmamalı, sadece gecikmeli."""
    islevci, sayac = dusen_sonra_basaran(2, [{"disclosureIndex": 1665567}])
    saat = SahteSaat()
    istemci = KapIstemcisi(
        transport=httpx.MockTransport(islevci),
        uyku=saat.uyu,
        saat=saat,
        istek_araligi_sn=0,
    )

    sonuc = istemci.liste(date(2026, 9, 17), date(2026, 9, 18))

    assert sayac["n"] == 3
    assert sonuc == [{"disclosureIndex": 1665567}]


def test_geri_cekilme_ustel_olarak_buyur():
    """Sabit aralıkla yeniden denemek bloklanmış bir WAF'ı açmaz."""
    islevci, _ = dusen_sonra_basaran(3, [])
    saat = SahteSaat()
    istemci = KapIstemcisi(
        transport=httpx.MockTransport(islevci),
        uyku=saat.uyu,
        saat=saat,
        istek_araligi_sn=0,
        geri_cekilme_tabani_sn=1.0,
    )

    istemci.liste(date(2026, 9, 17), date(2026, 9, 18))

    beklemeler = [u for u in saat.uykular if u > 0]
    assert beklemeler == [1.0, 2.0, 4.0]


def test_maks_denemeden_sonra_pes_eder():
    """Sonsuza kadar denemek KAP'ı da bizi de yorar; açık hata verilmeli."""
    islevci, sayac = dusen_sonra_basaran(99, [])
    saat = SahteSaat()
    istemci = KapIstemcisi(
        transport=httpx.MockTransport(islevci),
        uyku=saat.uyu,
        saat=saat,
        istek_araligi_sn=0,
        maks_deneme=4,
    )

    with pytest.raises(KapErisimHatasi):
        istemci.liste(date(2026, 9, 17), date(2026, 9, 18))

    assert sayac["n"] == 4


def test_detay_ucunu_dogru_referer_ile_cagirir():
    """Detay isteğinin Referer'ı o bildirimin kendi sayfası olmalı."""
    istekler: list[httpx.Request] = []

    def islevci(istek: httpx.Request) -> httpx.Response:
        istekler.append(istek)
        if istek.url.path == ISITMA_YOLU:
            return httpx.Response(200, text="<html></html>")
        return httpx.Response(200, json=[{"disclosure": {}}])

    sonuc = istemci_kur(islevci).detay(1665567)

    detay_istegi = istekler[-1]
    assert detay_istegi.url.path == "/tr/api/notification/attachment-detail/1665567"
    assert detay_istegi.headers["referer"].endswith("/tr/Bildirim/1665567")
    assert sonuc == {"disclosure": {}}


def test_bos_detay_yaniti_hata_verir():
    """Boş dizi dönen detay sessizce None'a dönüşmemeli."""

    def islevci(istek: httpx.Request) -> httpx.Response:
        if istek.url.path == ISITMA_YOLU:
            return httpx.Response(200, text="<html></html>")
        return httpx.Response(200, json=[])

    with pytest.raises(KapErisimHatasi):
        istemci_kur(islevci).detay(1665567)
