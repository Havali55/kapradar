"""Çıkarım şeması ve doğrulama kapısı (spec §6).

LLM'in bu projedeki tek işi serbest metinden **tutar** çıkarmak. Karşı
taraf, tarihler ve bayraklar KAP'ın XBRL alanlarından deterministik
geliyor (`ayristirici.py`), aritmetiğin tamamı `skor.py`'de. Buradaki
şema o dar işi tarif ediyor, kapı da onu denetliyor.

Kapı katı: bir kalem düşerse bildirimin tamamı düşer, kısmi yayın yok
(karar 2026-09-18). Yanlış-red kabul edilen maliyet.

Modül sağlayıcıdan bağımsız: burada ne Gemini ne başka bir SDK geçiyor.
Çıkarıcıyı değiştirmek `Cikarici` protokolünü uygulayan tek bir dosya
yazmak demek.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Literal, Protocol, Sequence

from pydantic import BaseModel, Field

__all__ = [
    "Cikarici",
    "CikarimMeta",
    "CikarimSonucu",
    "KapiSonucu",
    "Karar",
    "Tutar",
    "TutarCikarimi",
    "anlam_kapisi",
    "katmanli_cikar",
    "metin_kapisi",
    "PROMPT_VERSIYON",
    "SEMA_VERSIYON",
    "normalize",
    "prompt_kur",
    "sayilari_bul",
    "tutarlilik_kapisi",
]


# ------------------------------------------------------------ normalizasyon

# Türkçe noktasız ı indirgemesi. `"YAZILIM".casefold()` → 'yazilim' ama
# `"Yazılım".casefold()` → 'yazılım'; indirgenmezse eşleşme tam da
# manşet şirket adlarında sessizce başarısız olur (spec §6).
_I_ESLEMESI = str.maketrans({"İ": "i", "I": "i", "ı": "i"})

# Rakamların arasındaki ayraçlar silinir: 45.200.000 / 45,200,000 /
# 45 200 000 aynı dizeye iner. Aynı dönüşüm hem alıntıya hem ham metne
# uygulandığı için biçim farkı eşleşmeyi bozmaz.
_RAKAM_ARASI_AYRAC = re.compile(r"(?<=\d)[., \s](?=\d)")
_BOSLUK = re.compile(r"\s+")


def normalize(metin: str) -> str:
    """Alıntı karşılaştırması için metni sadeleştirir.

    Sıra önemli: önce Türkçe ı indirgemesi, sonra casefold. Ters sırada
    `İ` önce `i̇` (i + birleşen nokta) olur ve eşleşmez.
    """
    duz = unicodedata.normalize("NFC", metin or "")
    duz = duz.translate(_I_ESLEMESI).casefold()
    duz = _RAKAM_ARASI_AYRAC.sub("", duz)
    return _BOSLUK.sub(" ", duz).strip()


# Sayı belirteci: rakam grupları arasında nokta, virgül ya da boşluk,
# ardından isteğe bağlı çarpan sözcüğü. Şirketler büyük tutarları sık sık
# '25,02 milyon ABD Doları' diye yazıyor (CVKMD 1494067); çarpan okunmazsa
# A2 kapısı gerçek bir çıkarımı halüsinasyon sanıp reddeder.
_SAYI_BELIRTECI = re.compile(
    r"(\d+(?:[.,  ]\d+)*)(?:\s*(bin|milyon|milyar|trilyon)\b)?", re.IGNORECASE
)

_CARPANLAR = {
    "bin": Decimal("1000"),
    "milyon": Decimal("1000000"),
    "milyar": Decimal("1000000000"),
    "trilyon": Decimal("1000000000000"),
}


def _belirteci_coz(belirtec: str) -> Decimal | None:
    """'863.000' → 863000, '1.234,56' → 1234.56, '45,200,000' → 45200000.

    Kural: son ayraçtan sonraki grup üç haneliyse ayraç binliktir,
    değilse ondalıktır. Türkçe ve İngilizce yazımın ikisini de çözer.
    """
    gruplar = re.split(r"[.,  ]", belirtec)
    if len(gruplar) == 1:
        metin = gruplar[0]
    elif len(gruplar[-1]) == 3:
        metin = "".join(gruplar)
    else:
        metin = "".join(gruplar[:-1]) + "." + gruplar[-1]
    try:
        return Decimal(metin)
    except InvalidOperation:
        return None


def sayilari_bul(metin: str) -> list[Decimal]:
    """Metindeki sayıları değer olarak verir (A2 kapısı için).

    Çarpan sözcüğü varsa uygulanır: '25,02 milyon' → 25.020.000. Yalnız
    çarpılmış hâli dönüyor; LLM ham '25,02'yi yazdıysa bu bir hatadır ve
    kapının onu yakalaması gerekir.
    """
    degerler: list[Decimal] = []
    for belirtec, carpan in _SAYI_BELIRTECI.findall(metin or ""):
        deger = _belirteci_coz(belirtec)
        if deger is None:
            continue
        if carpan:
            deger *= _CARPANLAR[carpan.casefold()]
        degerler.append(deger)
    return degerler


# Para birimi sözlüğü, normalize edilmiş hâlleriyle.
# `\w*` kuyruğu Türkçe çekim ekleri için: 'Doları', 'Lirasıdır', 'Avrodur'.
# Sözlük ek almış hâlleri tanımazsa arşivdeki bildirimlerin büyük kısmı
# A3'ten döner — şirketler 'USD' yerine sık sık 'Amerikan Doları' yazıyor.
#
# Kodların sınırı `\b` değil HARF sınırı: şirketler '2.974.771,80USD' diye
# boşluksuz da yazıyor (CWENE 1502725) ve orada 'usd'nin solunda rakam var.
# Harf sınırı hem bunu geçirir hem 'atlanmıştır' içindeki 'tl' dizisini
# eler — sınırsız arama en sık hata kaynağıydı.
_HARF = "a-zçğıöşü"
_KOD = r"(?<![{h}]){kod}(?![{h}])"
_PARA_KALIPLARI: dict[str, re.Pattern[str]] = {
    "TRY": re.compile(
        _KOD.format(h=_HARF, kod="tl")
        + "|"
        + _KOD.format(h=_HARF, kod="try")
        + r"|₺|\btürk liras\w*|\blira\w*"
    ),
    "USD": re.compile(
        _KOD.format(h=_HARF, kod="usd") + r"|\$|\bdolar\w*|\bamerikan dolar\w*"
    ),
    "EUR": re.compile(
        _KOD.format(h=_HARF, kod="eur") + r"|€|\bavro\w*|\beuro\w*"
    ),
}


def _para_birimi_geciyor(normalize_alinti: str, para_birimi: str) -> bool:
    """Alıntıda o para biriminin adı geçiyor mu?

    'DIGER' etiketi için ters kontrol: bilinen üç para biriminden biri
    geçiyorsa etiket yanlıştır.
    """
    if para_birimi == "DIGER":
        return not any(k.search(normalize_alinti) for k in _PARA_KALIPLARI.values())
    kalip = _PARA_KALIPLARI.get(para_birimi)
    return bool(kalip and kalip.search(normalize_alinti))


# ------------------------------------------------------------------- şema

ParaBirimi = Literal["TRY", "USD", "EUR", "DIGER"]
TutarTipi = Literal["ilave_siparis", "fiyat_farki", "toplam_sozlesme", "tek_seferlik"]


class Tutar(BaseModel):
    """Serbest metinden çıkarılmış tek bir tutar kalemi.

    `deger` Decimal: net tutar toplamı ve ciro oranı bunun üzerinden
    hesaplanıyor, float yuvarlaması para hesabında birikir.
    """

    deger: Decimal
    para_birimi: ParaBirimi
    tip: TutarTipi
    alinti: str = Field(min_length=1)


class TutarCikarimi(BaseModel):
    """Bir bildirim için LLM'den beklenen çıktının tamamı."""

    tutarlar: list[Tutar]
    tutar_gizli: bool
    hap_ozet: list[str] = Field(min_length=3, max_length=3)
    guven: Literal["yuksek", "orta", "dusuk"]


@dataclass(frozen=True)
class CikarimMeta:
    """Çıkarımın künyesi — `cikarim` tablosu versiyonlu (spec §5)."""

    model: str
    katman: int
    prompt_versiyon: str
    sema_versiyon: str
    # Sağlayıcının bildirdiği gerçek token sayısı. Harcama izne bağlı
    # olduğu için koşu sonrası "ne kadar tuttu" sorusu tahminle değil
    # ölçümle cevaplanmalı. Sağlayıcı vermiyorsa None kalır — sıfır değil.
    girdi_token: int | None = None
    cikti_token: int | None = None


class Cikarici(Protocol):
    """Sağlayıcı-bağımsız çıkarım arayüzü (spec §7)."""

    def cikar(self, ham_metin: str) -> tuple[TutarCikarimi, CikarimMeta]: ...


# ------------------------------------------------------------------ prompt

# Sürüm `cikarim` tablosuna yazılıyor: bir sayının hangi prompt'la
# üretildiği sonradan sorulabilsin diye (spec §5, append-only).
PROMPT_VERSIYON = "v3"
SEMA_VERSIYON = "v1"

# v2 (2026-09-20): pilot koşusundan sonra 11. ve 12. kurallar eklendi —
# model çarpan sözcüğünü açmıyordu ve hap_ozet'i 2 maddeyle dönüyordu.
# v3 (2026-09-20): altın küme koşusunda 50 bildirimin 5'inde skor
# değişti. Üçünde yeni sözleşmeye 'toplam_sozlesme' denip skor silindi,
# ikisinde fazladan kalem skoru şişirdi. `tip` ayrımı Türkçe ifadeden
# 'yeni kazanılan iş mi' sorusuna taşındı; 2. ve 4. kurallara gerçek
# örnekler kondu.
#
# Kurallar altın kümeyi elle etiketlerken çıktı (Adım 8, 50 bildirim).
# Her biri gerçek bir bildirimde yapılmış/yapılabilecek bir hatayı
# kapatıyor; örnek indeksleri kasıtlı olarak yazılı.
_PROMPT = """Aşağıdaki KAP "Yeni İş İlişkisi" bildiriminden YALNIZCA parasal \
tutarları çıkar. Başka hiçbir şey çıkarma: karşı taraf, tarihler ve \
güncelleme bilgisi KAP'ın yapılandırılmış alanlarından geliyor.

Hiçbir aritmetik yapma. Para birimi çevirme, toplama, oran hesaplama yok.

Çıktı JSON şeması:
{{
  "tutarlar": [
    {{
      "deger": <sayı, binlik ayracı olmadan>,
      "para_birimi": "TRY" | "USD" | "EUR" | "DIGER",
      "tip": "ilave_siparis" | "fiyat_farki" | "toplam_sozlesme" | "tek_seferlik",
      "alinti": "<metinden BİREBİR kopyalanmış, tutarı içeren kısa parça>"
    }}
  ],
  "tutar_gizli": <bildirimde tutarın ticari sır olduğu söyleniyorsa true>,
  "hap_ozet": ["<madde 1>", "<madde 2>", "<madde 3>"],
  "guven": "yuksek" | "orta" | "dusuk"
}}

`tip` seçimi — Türkçe ifadeye DEĞİL, şu tek soruya bak:
**Bu tutar bu bildirimle YENİ kazanılan işi mi anlatıyor, yoksa daha önce \
duyurulmuş işin yeniden ifadesi mi?**

Yeni iş (bunlar sayılır):
- tek_seferlik  : yeni imzalanan sözleşmenin/siparişin kendi bedeli. Şirket \
buna "toplam sözleşme bedeli" dese bile, YENİ bir sözleşmenin bedeliyse tip \
budur. Örnek: "Yenilenen sözleşme 3 yıllık dönemi kapsamakta olup, bu döneme \
ilişkin toplam sözleşme bedeli 639.000 Amerikan Doları'dır" → tek_seferlik.
  Bir işin nihai/revize edilmiş tutarı açıklanıyorsa da tip budur ("nihai \
tutar 3.575.000 USD olarak gerçekleşmiştir").
- ilave_siparis : daha önce duyurulmuş, devam eden bir işe eklenen sipariş \
("ilave sipariş", "devam eden projelere ilave olarak").
- fiyat_farki   : fiyat farkı anlaşması tutarı.

Yeniden ifade (bu sayılmaz):
- toplam_sozlesme : ilave sipariş sonrası projenin ULAŞTIĞI kümülatif bedel. \
Yalnız aynı bildirimde yeni işin tutarı AYRICA yazılıysa kullanılır. Örnek: \
"940.002 USD tutarında ilave sipariş alınmıştır... böylece toplam sözleşme \
büyüklüğümüz 6.954.845 EUR ve 121.046.594 TL seviyesine ulaşmıştır" → \
940.002 USD ilave_siparis, diğer ikisi toplam_sozlesme.

Kurallar:
1. `alinti` bildirimde harfi harfine geçmeli. Geçmeyen çıkarım reddedilir.
2. Şirket kendi TL çevrimini veriyorsa (ör. "1.040.400 USD (50.613.963 TL)") \
bu AYRI BİR KALEM DEĞİLDİR; yalnız sözleşmenin asıl para birimini yaz. Kural \
çevrim parantez içinde olmasa da, ayrı satıra yazılmış olsa da geçerli: \
"1.850.000 ABD Doları (güncel TCMB kuruna göre\\n87.518.875\\nTürk Lirası)" \
TEK kalemdir.
3. Opsiyon tutarlarını yazma ("... 391.620 USD opsiyon eklenebilecektir"): \
kesinleşmiş iş değil.
4. Şirketin ÖDEDİĞİ bedeli yazma: gelir değil. Örnek: "Sözleşme devrine \
ilişkin bedel 8.000.000 ABD Doları + KDV olarak belirlenmiştir" — bu \
şirketin ödediği devir ücretidir, yazma.
5. Hedef/beklenti tutarlarını yazma ("yıllık 300 milyon USD ek iş hacmi \
hedeflenmektedir").
6. Alt siparişler ve onların toplamı birlikte veriliyorsa yalnız TOPLAMI yaz.
7. Aynı işin güncellenmiş nihai tutarı varsa yalnız nihai tutarı yaz.
8. Adet, kapasite, şube sayısı, çalışan sayısı gibi parasal olmayan sayıları \
yazma.
9. Tutar hiç açıklanmamışsa `tutarlar` boş liste olur. Bu bir hata değil.
10. Emin değilsen `guven` alanını "dusuk" yap; uydurma.
11. **Çarpan sözcüğünü aç.** "25,02 milyon ABD Doları" → `deger` 25020000 \
(25,02 değil); "1,04 milyar TL" → 1040000000. `alinti` ise çarpan sözcüğünü \
İÇERMELİ: "25,02 milyon ABD Doları".
12. `hap_ozet` tam olarak 3 madde olmalı — eksiği de fazlası da reddedilir.

Bildirim metni:
---
{metin}
---"""


def prompt_kur(ham_metin_tr: str) -> str:
    """Bir bildirim için çıkarım prompt'unu üretir.

    Yalnız Türkçe metin verilir: KAP iki dili aynı blokta taşıyor ve
    ayrılmazsa her rakam iki kez görünür, alıntı kapısı yanlış eşleşir.
    """
    return _PROMPT.format(metin=ham_metin_tr)


# -------------------------------------------------------------------- kapı


class Karar(Enum):
    YAYINLA = "yayinla"
    YUKSELT = "yukselt"  # Aşama A reddi: bir üst katman modele
    ELLE = "elle"  # Aşama B reddi: model hatası değil, veri şüphesi


@dataclass(frozen=True)
class KapiSonucu:
    karar: Karar
    red_nedeni: str | None = None

    @property
    def gecti(self) -> bool:
        return self.karar is Karar.YAYINLA


def metin_kapisi(cikarim: TutarCikarimi, ham_metin_tr: str) -> KapiSonucu:
    """Aşama A — çıkarımı yalnızca metne bakarak denetler (spec §6).

    §8 hesaplarından önce koşar. Red → bir üst katman modele yükseltilir;
    o da reddederse çağıran elle kuyruğa alır.
    """
    if cikarim.guven == "dusuk":
        return KapiSonucu(Karar.YUKSELT, "A6: guven dusuk")

    if cikarim.tutar_gizli and cikarim.tutarlar:
        return KapiSonucu(
            Karar.YUKSELT, "A4: tutar_gizli=true ama tutarlar dolu"
        )

    gorulen: set[tuple[str, str]] = set()
    metin = normalize(ham_metin_tr)

    for kalem in cikarim.tutarlar:
        alinti = normalize(kalem.alinti)
        if alinti not in metin:
            return KapiSonucu(
                Karar.YUKSELT, f"A1: alinti ham metinde yok -> {kalem.alinti[:60]!r}"
            )
        if kalem.deger not in sayilari_bul(kalem.alinti):
            return KapiSonucu(
                Karar.YUKSELT, f"A2: deger {kalem.deger} alintida gecmiyor"
            )
        if not _para_birimi_geciyor(alinti, kalem.para_birimi):
            return KapiSonucu(
                Karar.YUKSELT, f"A3: para birimi {kalem.para_birimi} alintida yok"
            )
        anahtar = (kalem.para_birimi, kalem.tip)
        if anahtar in gorulen:
            return KapiSonucu(Karar.YUKSELT, f"A5: mukerrer kalem {anahtar}")
        gorulen.add(anahtar)

    # A7 (2026-09-26): özet sitede "ÖZET" başlığıyla gösteriliyor ama
    # hiç denetlenmiyordu. İki bildirimde model metinde olmayan bir yılı
    # kendisi ekledi, ikisinde de yanlış ("Ağustos ayı" → "Ağustos 2024",
    # 2026 bildiriminde). Yıl, tarih içinde de olsa metinde geçmeli.
    # Normalize metinle karşılaştırılıyor: şirketler "2 024" de yazıyor
    # (EFOR 2024-12-19) ve rakam arası boşluk orada siliniyor.
    for madde in cikarim.hap_ozet:
        for yil in _YIL.findall(madde):
            if yil not in metin:
                return KapiSonucu(
                    Karar.YUKSELT, f"A7: ozette metinde olmayan yil {yil}"
                )

    return KapiSonucu(Karar.YAYINLA)


_YIL = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


# ------------------------------------------------ Aşama B: sayının anlamı
#
# 2026-09-26 veri denetimi: 962 skorlu bildirimin 10'unda tutar metinde
# birebir geçiyordu (A1–A3 doğru geçti) ama şirketin geliri değildi —
# şirketin kendi alımı, kendi yatırımı, idarenin tahmini bedeli ya da
# artışla birlikte ikinci kez sayılan yeni toplam. Onunun onu da "önemli"
# ya da "mega" kademesindeydi: bu hata tutarı hep büyütüyor. Prompt'un 4.
# ve 5. kuralı bunları zaten yasaklıyor; model aynı şirketin aynı tip
# metninde bir kez uyup bir kez uymadı (TOASO 2024-11 / 2025-09).
#
# Buradaki red model hatası sayılmaz, veri şüphesidir: bildirim elle
# kuyruğa düşer. Elle karar `data/elle_duzeltmeler.json`'a yazılır.

# Tutarın geçtiği cümlede aranır (normalize edilmiş metin: ı → i).
# Kalıplar denetimde gerçek bildirimlerle ayarlandı; "imzalamak için
# davet" bilerek YOK — kamu ihalesinde işi kazandın demek (ALVES).
_ANLAM_KALIPLARI: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("tahmini ihale bedeli", re.compile(r"muhammen|yaklaşik maliyet")),
    (
        "yatirim tutari",
        re.compile(
            r"yatirim (bütçe|tutar|bedel|maliyet)\w*|tutara kadar yatirim"
            r"|toplam yatirim\b"
        ),
    ),
    (
        "gorusme asamasi",
        re.compile(r"görüşmelere başlan|görüşmelerine davet|müzakerelere başlan"),
    ),
    ("on odeme", re.compile(r"ön ödeme")),
)

# Artış + yeni toplam eşleşmesinde fark bu kadardan küçükse tesadüf
# sayılır (yıllar, adetler metinde her yerde).
_ASGARI_FARK = Decimal("1000")


def _tutar_cumlesi(metin: str, alinti: str) -> str:
    """Normalize metinde alıntıyı içeren cümle."""
    i = metin.find(alinti)
    if i < 0:
        return alinti
    bas = max(metin.rfind(". ", 0, i), metin.rfind("\n", 0, i)) + 1
    sonlar = [
        j
        for j in (metin.find(". ", i + len(alinti)), metin.find("\n", i + len(alinti)))
        if j >= 0
    ]
    return metin[bas : min(sonlar) if sonlar else len(metin)]


def anlam_kapisi(
    skorlu: Sequence[Tutar],
    ham_metin_tr: str,
    *,
    karsi_taraf_niteligi: str | None,
) -> KapiSonucu:
    """Aşama B, anlam kontrolleri (B4–B6): sayı şirketin geliri mi?

    Yalnız skora giren kalemlere bakılır; tutar yoksa büyüklük iddiası da
    yoktur ve bildirim bu kapıdan geçer.
    """
    if not skorlu:
        return KapiSonucu(Karar.YAYINLA)

    # B4: KAP'ın yapılandırılmış alanı karşı tarafı tedarikçi diyor —
    # şirket alıcı olabilir. Alan tek başına güvenilir değil (FORTE,
    # ALVES kendilerini yazmış) ama denetimde 8 işaretin 4'ü gerçek
    # alımdı: elle bakmaya değer.
    nitelik = (karsi_taraf_niteligi or "").casefold()
    if "tedarik" in nitelik or "supplier" in nitelik:
        return KapiSonucu(
            Karar.ELLE, "B4: karsi taraf niteligi tedarikci, sirket alici olabilir"
        )

    metin = normalize(ham_metin_tr)
    for kalem in skorlu:
        cumle = _tutar_cumlesi(metin, normalize(kalem.alinti))
        for ad, kalip in _ANLAM_KALIPLARI:
            if kalip.search(cumle):
                return KapiSonucu(Karar.ELLE, f"B5: tutar cumlesinde {ad}")

    # B6: bir kalem = aynı para birimindeki başka kalem + metindeki bir
    # sayı → büyüğü "yeni toplam", küçüğü artış; ikisi birden sayılmış.
    # ORGE 2025-03-18: 360 mn = 213,2 mn (eski) + 146,8 mn (artış).
    metin_sayilari = set(sayilari_bul(ham_metin_tr))
    for buyuk in skorlu:
        for kucuk in skorlu:
            if buyuk is kucuk or buyuk.para_birimi != kucuk.para_birimi:
                continue
            fark = buyuk.deger - kucuk.deger
            if fark >= _ASGARI_FARK and fark in metin_sayilari:
                return KapiSonucu(
                    Karar.ELLE,
                    f"B6: {buyuk.deger} = {kucuk.deger} + {fark}, "
                    "yeni toplam artisla birlikte sayilmis",
                )

    return KapiSonucu(Karar.YAYINLA)


# Ciro oranı bu eşiği aşıyorsa büyük ihtimalle toplam sözleşme bedeli
# ilave sipariş sanıldı ya da payda yanlış (spec §6, B1).
AZAMI_CIRO_ORANI = Decimal("2")

# Aynı tutarın iki para biriminde tekrarı: TL karşılıkları bu kadar
# yakınsa aynı tutar iki kez sayılmış demektir.
MUKERRER_TOLERANSI = Decimal("0.05")


def tutarlilik_kapisi(
    *,
    ciro_orani: Decimal | None,
    kur_bulundu: bool,
    tl_kalemler: Sequence[tuple[str, Decimal]] = (),
) -> KapiSonucu:
    """Aşama B — §8 hesapları koştuktan sonra (spec §6).

    Buradaki red yükseltilmez: model hatası değil veri şüphesi, doğrudan
    elle inceleme kuyruğuna düşer.
    """
    if ciro_orani is not None and ciro_orani > AZAMI_CIRO_ORANI:
        return KapiSonucu(Karar.ELLE, f"B1: ciro orani %{ciro_orani * 100:.0f}")

    if not kur_bulundu:
        return KapiSonucu(Karar.ELLE, "B2: bildirim tarihli TCMB kuru bulunamadi")

    mukerrer = _mukerrer_kalem(tl_kalemler)
    if mukerrer is not None:
        return KapiSonucu(
            Karar.ELLE, f"B3: ayni tutar iki para biriminde tekrarlaniyor {mukerrer}"
        )

    return KapiSonucu(Karar.YAYINLA)


@dataclass(frozen=True)
class CikarimSonucu:
    """Katmanlı yönlendirmenin çıktısı (spec §7)."""

    cikarim: TutarCikarimi | None
    meta: CikarimMeta | None
    kapi: KapiSonucu

    @property
    def yayina_hazir(self) -> bool:
        return self.kapi.gecti


def katmanli_cikar(
    ham_metin_tr: str, cikaricilar: Sequence[Cikarici]
) -> CikarimSonucu:
    """Ucuz modelden başlayıp kapıdan geçene kadar yükseltir (spec §7).

    Kapının kendisi bedava bir güven sinyali: Aşama A'yı geçemeyen
    çıkarım bir üst katmana gider, son katman da geçemezse elle inceleme
    kuyruğuna düşer. Hacmin ~%85'inin ilk katmanda bitmesi bekleniyor,
    maliyet planı buna dayanıyor.
    """
    son = CikarimSonucu(None, None, KapiSonucu(Karar.ELLE, "hic cikarici yok"))

    for cikarici in cikaricilar:
        cikarim, meta = cikarici.cikar(ham_metin_tr)
        kapi = metin_kapisi(cikarim, ham_metin_tr)
        son = CikarimSonucu(cikarim, meta, kapi)
        if kapi.gecti:
            return son

    # Son katman da reddetti: yükseltecek yer kalmadı.
    return CikarimSonucu(
        son.cikarim, son.meta, KapiSonucu(Karar.ELLE, son.kapi.red_nedeni)
    )


def _mukerrer_kalem(
    tl_kalemler: Sequence[tuple[str, Decimal]],
) -> tuple[str, Decimal] | None:
    """Aynı tipte, TL karşılığı birbirine çok yakın iki kalem var mı?

    ARDYZ 1664397 gerçek örneği: '1.040.400 USD (50.613.963 TL)'. Tek
    sipariş, şirket kendi çevirisini parantez içinde vermiş. İkisi de
    kalem sayılırsa net tutar tam iki katına çıkar ve A5 bunu görmez —
    para birimleri farklı.
    """
    for i, (tip, deger) in enumerate(tl_kalemler):
        for diger_tip, diger in tl_kalemler[i + 1 :]:
            if tip != diger_tip or not deger or not diger:
                continue
            fark = abs(deger - diger) / max(deger, diger)
            if fark <= MUKERRER_TOLERANSI:
                return (tip, deger)
    return None
