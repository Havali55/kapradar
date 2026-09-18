"""KAP detay yanıtının ayrıştırılması.

Bu modülün tamamı saf fonksiyon: ağ yok, veritabanı yok, LLM yok.
KAP'ın yapılandırılmış XBRL alanları buradan deterministik olarak çıkar;
LLM yalnızca serbest metindeki tutarlar için devreye girer (spec §6).

Dosya düzeni: önce ilkel çözücüler, en sonda onları birleştiren
`bildirim_ayristir`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable
from zoneinfo import ZoneInfo

from selectolax.parser import HTMLParser

# KAP tüm zamanları Türkiye saatiyle veriyor, zaman dilimi belirtmeden.
ISTANBUL = ZoneInfo("Europe/Istanbul")

# KAP boş alanlara '-' koyuyor.
_BOS_DEGERLER = frozenset({"", "-", "—"})


# --------------------------------------------------------------- serbest metin


@dataclass(frozen=True)
class AciklamaMetni:
    """Bildirimin serbest metin bölümü, dile göre ayrılmış."""

    tr: str
    en: str


# Serbest metin alanları (ExplanationTextBlock, sözleşme koşulları) summernote
# hücrelerinde durur ve iki dil AYRI <td>'lerde gelir:
#   <td class="taxonomy-context-value-summernote multi-language-content content-tr">
#   <td class="taxonomy-context-value-summernote multi-language-content content-en">
_SERBEST_METIN_SECICI = "td.taxonomy-context-value-summernote.content-{dil}"


def _dil_metni(agac: HTMLParser, dil: str) -> str:
    parcalar = [
        dugum.text(separator="\n", strip=True)
        for dugum in agac.css(_SERBEST_METIN_SECICI.format(dil=dil))
    ]
    return "\n\n".join(p for p in parcalar if p)


def aciklama_metinleri(govde_html: str) -> AciklamaMetni:
    """Serbest metni Türkçe ve İngilizce olarak ayırır.

    KAP iki dili aynı gövdeye koyuyor. LLM'e yalnızca Türkçesi verilir;
    ayrılmazsa her rakam iki kez görünür ve alıntı kapısı yanlış eşleşir.
    """
    agac = HTMLParser(govde_html)
    return AciklamaMetni(tr=_dil_metni(agac, "tr"), en=_dil_metni(agac, "en"))


# ------------------------------------------------------------ ilkel çözücüler


def evet_hayir_coz(ham: str) -> bool | None:
    """KAP bayrağını çözer: 'Evet (Yes)' / 'Hayır (No)' / boş.

    Boş ya da tanınmayan değerde None döner — False değil. Ayrım önemli:
    "güncelleme değil" ile "güncelleme olup olmadığı bilinmiyor" aynı şey
    değil ve mükerrer ayıklama buna bakıyor.
    """
    temiz = (ham or "").strip()
    if temiz in _BOS_DEGERLER:
        return None
    if temiz.startswith("Evet"):
        return True
    if temiz.startswith("Hayır"):
        return False
    return None


_TARIH_KALIBI = re.compile(r"\b(\d{2})[./](\d{2})[./](\d{4})\b")


def tarih_coz(ham: str) -> date | None:
    """Tek bir TR tarihini çözer. KAP hem '10.05.2023' hem '10/05/2023' kullanıyor."""
    eslesme = _TARIH_KALIBI.search(ham or "")
    if eslesme is None:
        return None
    gun, ay, yil = (int(p) for p in eslesme.groups())
    try:
        return date(yil, ay, gun)
    except ValueError:
        return None


def tarih_listesi_coz(ham: str) -> list[date]:
    """Güncelleme zincirindeki tarihleri çözer.

    KAP bunları virgülle ya da tire ile ayırıp tek alanda veriyor
    ('10.05.2023, 14.06.2023, ...'). Açıklama ilk kez yapılıyorsa '-' gelir.
    """
    tarihler = []
    for gun, ay, yil in _TARIH_KALIBI.findall(ham or ""):
        try:
            tarihler.append(date(int(yil), int(ay), int(gun)))
        except ValueError:
            continue
    return tarihler


# Detay API'si liste API'sinden FARKLI tarih formatı kullanıyor:
#   liste : 18.09.2026 18:58:45
#   detay : 2026.09.18 18:58:45
_DETAY_ZAMAN_KALIBI = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})[ T](\d{2}):(\d{2}):(\d{2})")


def yayin_zamani_coz(ham: str) -> datetime | None:
    """Detay API'sinin yayın zamanını İstanbul saatiyle çözer.

    Zaman dilimi §8'deki t0 seans kararı için kritik: bildirim seans
    kapandıktan sonra düştüyse t0 bir sonraki işlem günüdür. Naif
    datetime bırakılırsa tüm tepki serisi bir gün kayar.
    """
    eslesme = _DETAY_ZAMAN_KALIBI.search(ham or "")
    if eslesme is None:
        return None
    yil, ay, gun, saat, dakika, saniye = (int(p) for p in eslesme.groups())
    try:
        return datetime(yil, ay, gun, saat, dakika, saniye, tzinfo=ISTANBUL)
    except ValueError:
        return None


def _temiz(deger: str | None) -> str | None:
    """KAP'ın '-' yer tutucusunu None'a indirger."""
    kirpilmis = (deger or "").strip()
    return None if kirpilmis in _BOS_DEGERLER else kirpilmis


# ------------------------------------------------------------- XBRL alanları

# Her alan bir satır; kod adı hücresinde, değer Türkçe değer hücresinde:
#   <td class="taxonomy-field-name-cell">
#     <div class="gwt-Label taxonomy-field-name">oda_XXX|</div>
#   <td class="taxonomy-context-value ... content-tr">...değer...
# Serbest metin alanları için değer hücresi summernote varyantı.
_ALAN_ADI_SECICI = ".taxonomy-field-name"
_DEGER_SECICILERI = (
    "td.taxonomy-context-value.content-tr",
    "td.taxonomy-context-value-summernote.content-tr",
)


def xbrl_alanlari(govde_html: str) -> dict[str, str]:
    """`oda_*` alan kodlarını Türkçe değerleriyle eşler.

    Değeri boş olan ('-') alanlar da döner; anlamlandırma çağırana ait.
    Görünen etiket yerine koda bağlanır — etiket metni değişebilir,
    XBRL taksonomi kodu değişmez.
    """
    alanlar: dict[str, str] = {}

    for satir in HTMLParser(govde_html).css("tr"):
        ad_dugumu = satir.css_first(_ALAN_ADI_SECICI)
        if ad_dugumu is None:
            continue

        kod = ad_dugumu.text(strip=True).rstrip("|").strip()
        if not kod.startswith("oda_"):
            continue

        for secici in _DEGER_SECICILERI:
            deger_dugumu = satir.css_first(secici)
            if deger_dugumu is not None:
                alanlar[kod] = deger_dugumu.text(separator="\n", strip=True)
                break
        else:
            alanlar[kod] = ""

    return alanlar


# KAP gövdeyi şablonu tanımlayan sınıfla sarar:
#   <table class="financial-table tbl_oda-12000_New-Business-Relation">
_SABLON_SINIFI = re.compile(r"\btbl_(oda-\d+)_")


def sablon_kodu_bul(govde_html: str) -> str | None:
    """Gövde HTML'inden şablonun makine kodunu çıkarır ('oda-12000').

    Router bu koda bağlanır; Türkçe başlık ('Yeni İş İlişkisi') değişebilir,
    XBRL taksonomi kodu değişmez.
    """
    eslesme = _SABLON_SINIFI.search(govde_html)
    return eslesme.group(1) if eslesme else None


# ------------------------------------------------------------------ bileşik

# Şemamızın alan adları ile KAP'ın XBRL kodları arasındaki eşleme.
# Çözücü None ise ham metin olduğu gibi alınır.
_ALAN_ESLEMESI: dict[str, tuple[str, Callable[[str], object] | None]] = {
    "karsi_taraf": ("oda_NameSurnameOrCompanyTitleOfCustomerOrSupplier", None),
    "karsi_taraf_niteligi": (
        "oda_NatureOfTheOtherPartyWithWhichNewBusinessRelationWillStart",
        None,
    ),
    "baslangic": ("oda_ExpectedStartingDateOfNewBusinessRelation", tarih_coz),
    "sozlesme_kosullari": (
        "oda_IfExistSignificantProvisionsOfTheContractTextBlock",
        None,
    ),
    "sirket_etki_beyani": (
        "oda_ImpactOfNewBusinessRelationOnCompanyActivities",
        None,
    ),
}


@dataclass(frozen=True)
class Bildirim:
    """Bir KAP bildiriminin veritabanına yazılabilir hâli."""

    kap_id: str
    kap_index: int
    ticker: str | None
    sablon_kodu: str | None
    yayin_zamani: datetime | None
    guncelleme_mi: bool
    duzeltme_mi: bool
    onceki_aciklama_tarihleri: list[date]
    kap_alanlari: dict[str, object]


def bildirim_ayristir(detay: dict) -> Bildirim:
    """Detay API yanıtından veritabanına yazılabilir bir kayıt üretir.

    `detay`, `/tr/api/notification/attachment-detail/{index}` yanıtının
    tek elemanı. LLM burada devreye girmez — üretilen her alan ya KAP'ın
    künyesinden ya da yapılandırılmış XBRL alanlarından gelir.
    """
    kunye = detay["disclosure"]["disclosureBasic"]
    govde_listesi = detay.get("disclosureBody") or [""]
    govde = govde_listesi[0]
    alanlar = xbrl_alanlari(govde)

    kap_alanlari: dict[str, object] = {}
    for bizim_ad, (oda_kodu, cozucu) in _ALAN_ESLEMESI.items():
        ham = _temiz(alanlar.get(oda_kodu))
        if ham is None:
            kap_alanlari[bizim_ad] = None
        else:
            kap_alanlari[bizim_ad] = cozucu(ham) if cozucu else ham

    return Bildirim(
        kap_id=kunye["disclosureId"],
        kap_index=int(kunye["disclosureIndex"]),
        ticker=_temiz(kunye.get("stockCode")),
        sablon_kodu=sablon_kodu_bul(govde),
        yayin_zamani=yayin_zamani_coz(kunye.get("publishDate", "")),
        guncelleme_mi=bool(evet_hayir_coz(alanlar.get("oda_UpdateAnnouncementFlag", ""))),
        duzeltme_mi=bool(
            evet_hayir_coz(alanlar.get("oda_CorrectionAnnouncementFlag", ""))
        ),
        onceki_aciklama_tarihleri=tarih_listesi_coz(
            alanlar.get("oda_DateOfThePreviousNotificationAboutTheSameSubject", "")
        ),
        kap_alanlari=kap_alanlari,
    )
