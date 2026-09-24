"""Finansal rapor gelir tablosunun ayrıştırılması ve TTM hasılat çözümü.

Skorun paydası burada üretiliyor (spec §8: ciro oranı). İki şart kodun
şeklini belirledi:

- **TTM.** Tek çeyrek değil son dört çeyrek. Ara dönem raporu bunu tek
  başına vermiyor; köprü `TTM = FY(önceki yıl) + YTD(cari) − YTD(geçen
  yıl aynı dönem)`. İyi haber: ara dönem raporu köprünün iki bileşenini
  birden taşıyor, çünkü geçen yılın aynı dönemi karşılaştırma sütununda.
- **Point-in-time.** Bildirim anında piyasada hangi bilanço açıksa o.
  Bugünün hasılatıyla dünün bildirimini puanlamak lookahead'dir ve
  geriye dönük testin tamamını geçersiz kılar.

Modülün tamamı saf fonksiyon: ağ yok, veritabanı yok, LLM yok.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Sequence

from selectolax.parser import HTMLParser

from kap_radar.ayristirici import tarih_listesi_coz, yayin_zamani_coz

# Gelir tablosu parçası `3100xx` rol ailesiyle işaretli. Parça sırası
# şirkete göre değiştiği için indekse değil role bakılıyor.
#
# Tek bir rol yetmiyor: IFRS gelir tablosunu iki türlü sunmaya izin
# veriyor — fonksiyon esaslı (310000, ORGE) ve çeşit esaslı (310003,
# NETAS/ARDYZ). Yalnız 310000 arandığında 935 raporun 577'si sessizce
# paydasız kalmıştı. Rol adının ortasındaki aile de sabit değil:
# TCELL holding taksonomisi kullanıyor (tbl_holding_role_310030).
GELIR_TABLOSU_ROLU = re.compile(r"tbl_[a-z]+_role_3100\d*")

# Hasılat etiketi. Bankalar ve finans kuruluşları ayrı etiket kullanıyor;
# ifrs-full_Revenue onlarda boş gelir.
HASILAT_KODLARI = (
    "ifrs-full_Revenue",
    "kap-fr_RevenueFromFinanceSectorOperations",
)

_KUNYE_PARA_BIRIMI = "Sunum Para Birimi"
_KUNYE_NITELIK = "Finansal Tablo Niteli"

__all__ = [
    "DonemHasilat",
    "Ttm",
    "aykiri_indeksler",
    "birim_coz",
    "finansal_ayristir",
    "gelir_tablosu_govdesi",
    "konsolide_mi",
    "sayi_coz",
    "sunum_para_birimi",
    "ttm_coz",
]


# --------------------------------------------------------------- ilkeller


def gelir_tablosu_govdesi(detay: dict) -> str | None:
    """Çok parçalı rapor gövdesinden gelir tablosunu seçer."""
    for parca in detay.get("disclosureBody") or []:
        if parca and GELIR_TABLOSU_ROLU.search(parca):
            return parca
    return None


def sayi_coz(ham: str | None) -> Decimal | None:
    """KAP'ın TR biçimli sayısını çözer: '2.597.519.683' → Decimal.

    Parantez negatif demek ('(1.234)'), binlik ayracı nokta, ondalık
    ayracı virgül. Boş hücre None döner — sıfır değil: 'hasılat
    açıklanmamış' ile 'hasılat sıfır' aynı şey değil.
    """
    temiz = (ham or "").strip().replace("\xa0", "").replace(" ", "")
    if not temiz or temiz in {"-", "—"}:
        return None

    negatif = temiz.startswith("(") and temiz.endswith(")")
    if negatif:
        temiz = temiz[1:-1]

    temiz = temiz.replace(".", "").replace(",", ".")
    try:
        deger = Decimal(temiz)
    except InvalidOperation:
        return None
    return -deger if negatif else deger


def _kunye_degeri(agac: HTMLParser, etiket: str) -> str | None:
    """Tablonun tepesindeki iki hücreli künye satırlarını okur."""
    for satir in agac.css("tr"):
        hucreler = satir.css("td")
        if len(hucreler) != 2:
            continue
        if hucreler[0].text(strip=True).startswith(etiket):
            return hucreler[1].text(strip=True) or None
    return None


def sunum_para_birimi(govde: str) -> str | None:
    """Raporun sunum birimi, KAP'ın yazdığı hâliyle ('TL', '1.000 TL')."""
    return _kunye_degeri(HTMLParser(govde), _KUNYE_PARA_BIRIMI)


def birim_coz(ham: str | None) -> tuple[str | None, Decimal]:
    """'1.000 TL' → ('TL', 1000). Sunum birimi hep para birimi değil.

    TOASO, DOAS ve AKENR gelir tablosunu bin TL cinsinden sunuyor. Çarpan
    uygulanmazsa o şirketlerin hasılatı bin kat küçük okunur ve her ciro
    oranı bin kat büyür — 500 milyonluk bir sipariş Tofaş'ın cirosunun
    %156'sı gibi görünür (gerçekte %0,16).
    """
    parcalar = (ham or "").strip().split()
    if not parcalar:
        return None, Decimal("1")
    if len(parcalar) == 1:
        return parcalar[0], Decimal("1")
    return parcalar[-1], sayi_coz(parcalar[0]) or Decimal("1")


def konsolide_mi(govde: str) -> bool | None:
    """'Konsolide' / 'Konsolide Olmayan'. Tanınmazsa None."""
    deger = _kunye_degeri(HTMLParser(govde), _KUNYE_NITELIK)
    if deger is None:
        return None
    if deger.startswith("Konsolide Olmayan"):
        return False
    if deger.startswith("Konsolide"):
        return True
    return None


# ------------------------------------------------------------- sütunlar


@dataclass(frozen=True)
class _Sutun:
    """Gelir tablosunun bir bağlam sütunu."""

    sira: int
    basi: date
    sonu: date

    @property
    def ay_sayisi(self) -> int:
        return (self.sonu.year - self.basi.year) * 12 + (
            self.sonu.month - self.basi.month
        ) + 1


def _sutunlar(agac: HTMLParser) -> list[_Sutun]:
    """Sütun başlıklarındaki dönem aralıklarını çıkarır.

    Türkçe etiketlere ('Cari Dönem 3 Aylık') değil tarihlere bakılıyor:
    etiket metni değişebilir, aralık değişmez. Başlık iki dili birden
    taşıdığı için aynı aralık iki kez geçer; ilk iki tarih yeter.
    """
    sutunlar: list[_Sutun] = []
    for sira, baslik in enumerate(agac.css("td.context-header, th.context-header")):
        tarihler = tarih_listesi_coz(baslik.text(separator=" ", strip=True))
        if len(tarihler) >= 2:
            sutunlar.append(_Sutun(sira=sira, basi=tarihler[0], sonu=tarihler[1]))
    return sutunlar


def _hasilat_hucreleri(agac: HTMLParser) -> list[Decimal | None] | None:
    """Hasılat satırının bağlam değerlerini sütun sırasıyla verir."""
    for kod in HASILAT_KODLARI:
        for satir in agac.css("tr"):
            ad = satir.css_first(".taxonomy-field-name")
            if ad is None or ad.text(strip=True).rstrip("|").strip() != kod:
                continue
            degerler = [
                sayi_coz(h.text(strip=True))
                for h in satir.css("td.taxonomy-context-value")
            ]
            if any(d is not None for d in degerler):
                return degerler
    return None


def _cari_ve_onceki(
    sutunlar: Sequence[_Sutun],
) -> tuple[_Sutun, _Sutun | None] | None:
    """Yılbaşından beri (YTD) sütununu ve geçen yılın aynısını seçer.

    Ara dönem raporunda dört sütun var: cari YTD, önceki yıl YTD, cari
    3 aylık, önceki yıl 3 aylık. En geç biten ve en uzun olan cari YTD'dir;
    3 aylık sütunu YTD sanmak paydayı yarıya indirir.
    """
    if not sutunlar:
        return None

    cari = max(sutunlar, key=lambda s: (s.sonu, s.ay_sayisi))
    onceki = next(
        (
            s
            for s in sutunlar
            if s is not cari
            and s.ay_sayisi == cari.ay_sayisi
            and s.sonu.year == cari.sonu.year - 1
            and s.sonu.month == cari.sonu.month
        ),
        None,
    )
    return cari, onceki


# ------------------------------------------------------------- bileşik


@dataclass(frozen=True)
class DonemHasilat:
    """Tek bir finansal rapordan çıkan dönem hasılatı."""

    ticker: str
    kap_index: int
    yayin_zamani: datetime
    donem_basi: date
    donem_sonu: date
    ay_sayisi: int
    hasilat: Decimal
    onceki_yil_hasilat: Decimal | None
    onceki_donem_sonu: date | None
    para_birimi: str | None
    konsolide: bool | None
    # Sunum biriminden gelen çarpan ('1.000 TL' → 1000). `hasilat` zaten
    # çarpılmış hâlde; bu alan hangi ölçeğin uygulandığını izlenebilir
    # tutmak için duruyor.
    birim_carpani: Decimal = Decimal("1")


def finansal_ayristir(kayit: dict) -> DonemHasilat | None:
    """Arşiv kaydından dönem hasılatını çıkarır.

    `kayit` = {"disclosure": <künye>, "gelirTablosu": <html>}. Hasılat
    satırı ya da dönem sütunu okunamıyorsa None döner; tahmin edilmez.
    """
    govde = kayit.get("gelirTablosu")
    if not govde:
        return None

    kunye = kayit["disclosure"]["disclosureBasic"]
    agac = HTMLParser(govde)

    secim = _cari_ve_onceki(_sutunlar(agac))
    degerler = _hasilat_hucreleri(agac)
    if secim is None or degerler is None:
        return None

    cari, onceki = secim
    if cari.sira >= len(degerler) or degerler[cari.sira] is None:
        return None

    onceki_deger = (
        degerler[onceki.sira]
        if onceki is not None and onceki.sira < len(degerler)
        else None
    )

    para_birimi, carpan = birim_coz(sunum_para_birimi(govde))

    return DonemHasilat(
        ticker=(kunye.get("stockCode") or "").strip(),
        kap_index=int(kunye["disclosureIndex"]),
        yayin_zamani=yayin_zamani_coz(kunye.get("publishDate", "")),
        donem_basi=cari.basi,
        donem_sonu=cari.sonu,
        ay_sayisi=cari.ay_sayisi,
        # Sunum birimi burada uygulanıyor: tabloda saklanan hasılat her
        # zaman mutlak tutar. Çarpanı okuma anına bırakmak, bir yerde
        # unutulduğunda bin kat hata demek olurdu.
        hasilat=degerler[cari.sira] * carpan,
        onceki_yil_hasilat=None if onceki_deger is None else onceki_deger * carpan,
        onceki_donem_sonu=onceki.sonu if onceki and onceki_deger is not None else None,
        para_birimi=para_birimi,
        konsolide=konsolide_mi(govde),
        birim_carpani=carpan,
    )


# ----------------------------------------------------------------- TTM


@dataclass(frozen=True)
class Ttm:
    """Bir ana kadar açıklanmış raporlardan çözülen son 12 aylık hasılat."""

    hasilat: Decimal
    para_birimi: str | None
    donem_sonu: date
    yontem: str  # "yillik" | "ytd_koprusu"
    kaynak_indeksler: tuple[int, ...]
    # Köprüde yıllık terime uygulanan TMS 29 çarpanı. None: uygulanmadı
    # (yıllık yöntem ya da katsayı çözülemedi); 1: şirket yeniden ifade
    # etmiyor. Bkz. `_yeniden_ifade_katsayisi`.
    enflasyon_carpani: Decimal | None = None


def ttm_coz(donemler: Sequence[DonemHasilat], an: datetime) -> Ttm | None:
    """`an` anında piyasanın bildiği son 12 aylık hasılatı verir.

    `an`dan sonra yayınlanmış rapor hiç dikkate alınmaz. Köprü için
    gereken yıllık rapor da o anda açıklanmış olmalı; eksikse None
    döner ve ciro oranı gösterilmez (spec §8) — yarım veriyle TTM
    uydurmak sessizce yanlış bir skor üretir.
    """
    acik = [d for d in donemler if d.yayin_zamani and d.yayin_zamani <= an]
    if not acik:
        return None

    # En güncel DÖNEM kazanır, en son YAYIN değil: eski bir dönemin
    # revizyonu yeni yayınlanmış olabilir. Aynı dönemde son yayın kazanır.
    son = max(acik, key=lambda d: (d.donem_sonu, d.yayin_zamani))

    if son.ay_sayisi == 12:
        return Ttm(
            hasilat=son.hasilat,
            para_birimi=son.para_birimi,
            donem_sonu=son.donem_sonu,
            yontem="yillik",
            kaynak_indeksler=(son.kap_index,),
        )

    if son.onceki_yil_hasilat is None:
        return None

    yillik = _kopru_yilligi(acik, son)
    if yillik is None or yillik.para_birimi != son.para_birimi:
        return None

    # TMS 29: iki YTD terimi cari dönem sonunun TL'sinde, yıllık terim bir
    # önceki Aralık'ın TL'sinde. Yıllık terim `ay_sayisi` ay ileri taşınır.
    # Katsayı çözülemezse düzeltmesiz köprü kullanılıyor ve bu işaretleniyor
    # (enflasyon_carpani=None) — payda yine de eskisi kadar doğru.
    katsayi = _yeniden_ifade_katsayisi(acik, son)
    yillik_terim = yillik.hasilat
    carpan = None
    # Sıra kronolojik ve en güncel rapor SONDA: çağıranlar kaynak
    # bağlantısı için `kaynak_indeksler[-1]` kullanıyor.
    kaynak = (yillik.kap_index, son.kap_index)
    if katsayi is not None:
        k, ilk_yayin = katsayi
        carpan = k ** (Decimal(son.ay_sayisi) / Decimal(12))
        yillik_terim = yillik.hasilat * carpan
        kaynak = (ilk_yayin, yillik.kap_index, son.kap_index)

    return Ttm(
        hasilat=(yillik_terim + son.hasilat - son.onceki_yil_hasilat).quantize(Decimal(1)),
        para_birimi=son.para_birimi,
        donem_sonu=son.donem_sonu,
        yontem="ytd_koprusu",
        kaynak_indeksler=kaynak,
        enflasyon_carpani=carpan,
    )


# Yeniden ifade katsayısının kabul aralığı. Arşivde 2024 dönemleri için
# medyan 1,44 (üst çeyrek 1,79), 2025–26 için ~1,31–1,33. Aralık dışı bir
# oran enflasyon değil: yeniden sınıflama, durdurulan faaliyet ya da birim
# hatası. Öyle bir oranla ölçeklemek paydayı yanlış yönde bozar.
YENIDEN_IFADE_ALT = Decimal("0.95")
YENIDEN_IFADE_UST = Decimal("2.2")


def _yeniden_ifade_katsayisi(
    acik: Sequence[DonemHasilat], son: DonemHasilat
) -> tuple[Decimal, int] | None:
    """Şirketin kendi 12 aylık TMS 29 katsayısı ve dayandığı rapor.

    `son`, geçen yılın aynı dönemini cari birimle veriyor
    (`onceki_yil_hasilat`); o dönemin İLK yayını aynı rakamı kendi
    döneminin birimiyle vermişti. Oran, 12 aylık satın alma gücü
    düzeltmesi. Dış veri (TÜFE) gerekmiyor ve point-in-time bozulmuyor:
    iki rapor da `an`dan önce açıklanmış olmak zorunda (`acik`).

    İlk yayın alınıyor, son revizyon değil: sonraki bir revizyon
    yeniden ifade edilmiş rakam taşıyabilir ve oranı 1'e çekerdi.
    """
    if son.onceki_donem_sonu is None or not son.onceki_yil_hasilat:
        return None
    adaylar = [
        d
        for d in acik
        if d.donem_sonu == son.onceki_donem_sonu
        and d.ay_sayisi == son.ay_sayisi
        and d.para_birimi == son.para_birimi
        and d.hasilat > 0
    ]
    if not adaylar:
        return None
    ilk = min(adaylar, key=lambda d: d.yayin_zamani)
    k = son.onceki_yil_hasilat / ilk.hasilat
    if not YENIDEN_IFADE_ALT <= k <= YENIDEN_IFADE_UST:
        return None
    return k, ilk.kap_index


# Bir dönemin yıllıklandırılmış hasılatı, şirketin medyanından bu kadar
# saparsa sunum birimi beyanı yanlış demektir. Mevsimsellik ve büyüme en
# fazla birkaç kat oynatır; yüz kat ölçek hatasıdır.
AYKIRI_ESIK = Decimal("100")

# Medyanın anlamlı olması için gereken en az dönem sayısı.
_ASGARI_DONEM = 3


def aykiri_indeksler(donemler: Sequence[DonemHasilat]) -> list[int]:
    """Sunum birimi beyanı yanlış görünen raporların indeksleri.

    ONCSM 1559324 gerçek örneği: şirket her raporunu sade TL sunarken
    2025 yıllığında sunum birimini '1.000.000 TL' yazmış, ama rakam
    diğer dönemlerin doğal devamı. Beyana körü körüne uyulsa o şirketin
    hasılatı bir milyon kat şişer, ciro oranı sıfıra iner ve skor
    sessizce yok olur.

    Karşılaştırma yıllıklandırılmış hasılat üzerinden: 3 aylık raporla
    yıllığı doğrudan kıyaslamak her seriyi aykırı gösterirdi.
    """
    yillik = [
        (d.kap_index, d.hasilat * 12 / d.ay_sayisi)
        for d in donemler
        if d.ay_sayisi and d.hasilat
    ]
    if len(yillik) < _ASGARI_DONEM:
        return []

    medyan = sorted(deger for _, deger in yillik)[len(yillik) // 2]
    if not medyan:
        return []

    return [
        indeks
        for indeks, deger in yillik
        if max(deger, medyan) / min(deger, medyan) > AYKIRI_ESIK
    ]


def _kopru_yilligi(
    acik: Sequence[DonemHasilat], son: DonemHasilat
) -> DonemHasilat | None:
    """Köprünün yıllık bacağı: cari hesap döneminden hemen önceki yıl.

    Eşleşme takvim yılıyla değil dönem başıyla kuruluyor; özel hesap
    dönemi kullanan şirkette (nadir ama var) takvim yılı yanlış rapora
    bağlar.
    """
    hedef_sonu = son.donem_basi - timedelta(days=1)
    adaylar = [
        d for d in acik if d.ay_sayisi == 12 and d.donem_sonu == hedef_sonu
    ]
    return max(adaylar, key=lambda d: d.yayin_zamani) if adaylar else None
