"""Fon Portföy Dağılım Raporu (PDF) → yurt içi hisse pozisyonları.

Rapor her portföy şirketinde aynı SPK şablonunda (III-FON PORTFÖY DEĞERİ
TABLOSU). Bir pozisyon metinde şöyle görünüyor (pypdf çıktısı):

    DSTKF DESTEK
    FAKTORIN
    G
    500.000,00 1.958,600000 31/08/26 2.081,000000 1.040.500.000,00 9,07 7,07TL 80100517 8,05
    TREDSTF00012

Sayı satırı: nominal · birim alış · alış tarihi · günlük birim değer ·
toplam değer (TL) · grup % · FPD % · döviz · borsa sözleşme no · FTD %
ve (ya aynı satırda ya bir sonrakinde) ISIN. Kod, sayı satırından önceki
en yakın "KOD AD" satırının ilk kelimesi. Aynı hisse birden fazla satırda
(farklı alış tarihleri) ve NEGATİF nominalle de (ödünç/satış) görünebiliyor;
toplam net alınıyor.

Doğrulama: raporun kendi "Hisse Türk" grup toplamı ile ayrıştırılan
toplam karşılaştırılıyor; tutmuyorsa rapor elle incelemeye düşer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SAYI = r"-?[\d.]+,\d+"
# Borsa sözleşme no bazı şirketlerin raporunda yok ("...TL -0,74"). Satır
# başı da serbest: kısa unvanlar kod + ad + sayılarla tek satıra sığıyor
# ("ISMEN İŞ YATIRIM 50.000,00 ..."); o zaman kod önekten alınıyor.
_SATIR = re.compile(
    rf"(?:^|(?<=\s))(?P<nominal>{_SAYI}) (?P<alis>{_SAYI}) (?P<tarih>\d\d/\d\d/\d\d) "
    rf"(?P<fiyat>{_SAYI}) (?P<deger>{_SAYI}) (?P<grup>{_SAYI}) (?P<fpd>{_SAYI})"
    rf"TL(?: \d+)?(?: (?P<ftd>{_SAYI}))?\s*(?P<isin>TR[A-Z0-9]{{10}})?\s*$"
)
# Sayfa sonunda satır sözleşme no'da kesilebiliyor; FTD % ve ISIN sonraki
# sayfaya taşıyor. Bu yüzden ikisi de isteğe bağlı — ihtiyaç duyulan TL
# değeri satırın başında.
_KOD = re.compile(r"^([A-Z][A-Z0-9]{2,5}) \S")
# Sayfa başlığındaki kolon adları kod kalıbına uyuyor ("GRUP (%)TOPLAM").
# Bir pozisyon bloğu sayfa sonunda bölünürse sayılar yanlış koda yazılırdı.
_BASLIK_KELIMELERI = frozenset(
    {"GRUP", "TOPLAM", "BORSA", "SATIN", "VADE", "VADEYE", "ISIN", "REPO",
     "KURUM", "TUTARI", "ORANI", "NET", "BIRIM"}
)
_GRUP_TOPLAMI = re.compile(rf"^(?P<nominal>{_SAYI}) (?P<deger>{_SAYI}) .*GRUP TOPLAMI")
_AY = re.compile(
    r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)-(\d{4})"
)


def sayi(metin: str) -> float:
    return float(metin.replace(".", "").replace(",", "."))


@dataclass(frozen=True)
class Pozisyon:
    ticker: str
    nominal: float
    deger_tl: float
    isin: str | None


@dataclass(frozen=True)
class FonRaporu:
    donem: str | None
    pozisyonlar: list[Pozisyon]
    rapor_hisse_toplami: float | None

    @property
    def ayristirilan_toplam(self) -> float:
        return sum(p.deger_tl for p in self.pozisyonlar)

    @property
    def tutarli(self) -> bool:
        """Ayrıştırılan toplam raporun kendi grup toplamını ±%0,5 tutuyor mu."""
        if self.rapor_hisse_toplami is None:
            return not self.pozisyonlar
        hedef = self.rapor_hisse_toplami
        return abs(self.ayristirilan_toplam - hedef) <= max(abs(hedef) * 0.005, 1.0)

    def net(self) -> dict[str, float]:
        """Hisse başına net TL pozisyon (negatif satırlar düşülmüş)."""
        toplam: dict[str, float] = {}
        for p in self.pozisyonlar:
            toplam[p.ticker] = toplam.get(p.ticker, 0.0) + p.deger_tl
        return toplam


def _hisse_turk_bolumu(metin: str) -> str:
    """'Hisse Türk' alt grubundan ilk GRUP TOPLAMI satırına kadar.

    Sayfa başlıkları (kolon adları) bölümün ortasına girebiliyor; onlar
    sayı satırı kalıbına uymadığı için zararsız.
    """
    bas = metin.find("Hisse Türk")
    if bas == -1:
        return ""
    govde = metin[bas:]
    son = re.search(r"GRUP TOPLAMI.*$", govde, re.M)
    # Grup toplamı satırının kendisi de dahil kalsın (doğrulama için).
    return govde[: son.end()] if son else govde


def rapor_ayristir(metin: str) -> FonRaporu:
    ay = _AY.search(metin)
    bolum = _hisse_turk_bolumu(metin)
    satirlar = [s.strip() for s in bolum.splitlines()]

    pozisyonlar: list[Pozisyon] = []
    son_kod: str | None = None
    # Kod yalnız bir pozisyon bittikten sonraki İLK uygun satırdan alınır:
    # unvanın devam satırları ("GIDA VE", "SÜT SANAYİ") da kod kalıbına uyar.
    kod_bekleniyor = True
    rapor_toplam: float | None = None
    for i, satir in enumerate(satirlar):
        if (m := _GRUP_TOPLAMI.match(satir)) is not None:
            rapor_toplam = sayi(m["deger"])
            break
        if (m := _SATIR.search(satir)) is not None:
            # Önek bir kodsa ve yeni pozisyon bekleniyorsa kod odur; değilse
            # (unvanın devamı: "ENERJİ A. 975,00 ...") önceki kod geçerli.
            onek = satir[: m.start()].strip()
            k = re.match(r"^([A-Z][A-Z0-9]{2,5})(?:\s|$)", onek)
            if kod_bekleniyor and k is not None and k[1] not in _BASLIK_KELIMELERI:
                son_kod = k[1]
            if son_kod is None:
                continue
            isin = m["isin"]
            if isin is None and i + 1 < len(satirlar):
                sonraki = re.match(r"^(TR[A-Z0-9]{10})$", satirlar[i + 1])
                isin = sonraki[1] if sonraki else None
            pozisyonlar.append(
                Pozisyon(son_kod, sayi(m["nominal"]), sayi(m["deger"]), isin)
            )
            kod_bekleniyor = True
            continue
        if (
            kod_bekleniyor
            and (k := _KOD.match(satir)) is not None
            and k[1] not in _BASLIK_KELIMELERI
        ):
            son_kod = k[1]
            kod_bekleniyor = False

    donem = f"{ay[1]}-{ay[2]}" if ay else None
    return FonRaporu(donem, pozisyonlar, rapor_toplam)
