"""KAP detay yanıtının ayrıştırılması.

Bu modülün tamamı saf fonksiyon: ağ yok, veritabanı yok, LLM yok.
KAP'ın yapılandırılmış XBRL alanları buradan deterministik olarak çıkar;
LLM yalnızca serbest metindeki tutarlar için devreye girer (spec §6).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from selectolax.parser import HTMLParser


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


# KAP boş alanlara '-' koyuyor; bunu "bilinmiyor"dan ayırmıyoruz.
_BOS_DEGERLER = frozenset({"", "-", "—"})


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
    bulunan = _TARIH_KALIBI.findall(ham or "")
    tarihler = []
    for gun, ay, yil in bulunan:
        try:
            tarihler.append(date(int(yil), int(ay), int(gun)))
        except ValueError:
            continue
    return tarihler


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
