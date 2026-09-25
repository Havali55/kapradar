"""Karşı taraf alanı gerçek bir isim mi, anonim bir tanım mı?

KAP'ın "Yeni İş İlişkisi" şablonunda karşı taraf serbest metin. Şirket
ismi vermek istemediğinde alanı boş bırakmak yerine çoğu zaman bir tanım
yazıyor: "Uluslararası Müşteri", "Yurt Dışı Yerleşik Şirket", hatta tek
bir nokta. 2026-09-24'e kadar "alan boş değil" = "karşı taraf açık"
sayılıyordu; "açık" görünen 877 bildirimin 254'ü aslında anonimdi ve
K çarpanı (skor.guvenilirlik) bunlara 1,00 veriyordu.

Kural sırası:
  1. Harf yoksa ya da bilinen bir "cevap vermeme" kalıbıysa → anonim.
  2. Hukuki ek (A.Ş., Ltd., GmbH…) ya da kurum sözcüğü (Bakanlığı,
     Belediyesi, Müdürlüğü…) varsa → isim.
  3. Genel sözcükler (müşteri, yerleşik, ülke adları, sektörler…)
     atılınca geriye bir şey kalmıyorsa → anonim.
  4. Metin genel bir baş adla bitiyorsa ("… bir firma", "… şirketi")
     → anonim. Yazım hatalı ülke adı gibi 3. kuralın kaçırdıklarını
     yakalıyor ("Kuzay Makedonya'da Yerleşik Bir Firma").
  5. Kalan her şey → isim.

Kural kasıtlı olarak "isim" tarafına yatık: şüpheli bir değeri anonim
saymak skoru düşürür ama yanlış bir olgu yazmaz; ancak bu dosya
gerçek örneklerle sınanıyor (tests/test_karsi_taraf.py), yeni kalıp
görülünce oraya eklenmeli.
"""

from __future__ import annotations

import re

__all__ = ["karsi_taraf_acik"]

_CEVAPSIZ = re.compile(
    r"(aşağıda|bulunmamaktadır|açıklanmamış|açıklanmayacak|gizli|ticari sır|belirtilmemiş|bilgi verilmemiş)",
    re.I,
)

_HUKUKI = re.compile(
    r"(\ba\.?\s?ş\b|\banonim şirket|\bltd\b|\blimited\b|\binc\b|\bllc\b|\bgmbh\b|\bcorp\b"
    r"|\bcorporation\b|\bs\.?\s?a\.?\b|\bs\.?p\.?a\b|\bplc\b|\bb\.?\s?v\b|\ba\.?g\b|\bjsc\b|\bcjsc\b"
    r"|\bllp\b|\bpte\b|\bco\.|\bs\.?r\.?o\b|\bs\.?r\.?l\b|\bsp\.? z\b|\bsas\b|\baps\b|\bspc\b"
    r"|\bpty\b|\bholding\b|\badi ortaklığı|\biş ortaklığı)",
    re.I,
)

_KURUM = re.compile(
    r"(bakanlığ|müdürlüğ|belediye|başkanlığ|hastane|üniversite|komutanlığ|başhekimliğ|valiliğ"
    r"|federasyon|teşkilat|kuvvetleri|kurulu\b|iş kurumu|ajansı|tcdd|türksat|aselsan|havelsan|roketsan"
    r"|tusaş|botaş|tedaş|teiaş|emniyet|jandarma)",
    re.I,
)

_GENEL = frozenset(
    """
    müşteri müşteriler müşterisi müşterimiz müşterilere şirket şirketi şirketler şirketleri
    firma firması firmalar firmaları işletme işletmesi kurum kurumu kuruluş kuruluşu kuruluşlar
    alıcı alıcılar banka bayi bayiler bayileri bayilerimiz satış noktası noktaları noktalarımız
    bir iki üç dört beş muhtelif çeşitli yeni iş ilişkisi
    yurt yurtiçi yurtdışı yurtiçinde yurtdışında içi dışı içinde dışında için yur
    yerleşik yerlşik mukim menşeli merkezli bulunan kurulu faaliyet gösteren hizmet veren
    uluslararası kurumsal yabancı özel kamu global genelindeki ülkemizde alanında sektörüne sektöründe
    dünyanın en büyük önde gelen köklü ortaklı premium markası üst yapıcı yatırımcı
    ve ile de da
    teknoloji enerji savunma sanayi sanayii telekomünikasyon lojistik posta servis sağlayıcı
    akaryakıt dağıtım beyaz eşya ev aletleri mobilya elektronik ürünler üretici üreticisi
    üreticileri otomotiv inşaat gıda ilaç bilişim
    türkiye türk abd amerika almanya alman ingiltere fransa italya ispanya hollanda rusya çin
    japonya kore hindistan irak iran azerbaycan kazakistan özbekistan kırgızistan gürcistan
    romanya bulgaristan polonya ukrayna mısır katar kuveyt dubai makedonya kuzey güney
    porto riko karayip adaları adalarında avrupa asya afrika ortadoğu
    """.split()
)

# 4. kural: metnin son sözcüğü bunlardan biriyse tanım bir isim değil.
_BAS_AD = frozenset(
    """
    müşteri müşteriler şirket şirketi şirketler şirketleri firma firması firmalar firmaları
    işletme kurum kuruluş kuruluşu alıcı alıcılar banka markası üreticileri üreticisi
    """.split()
)


def _kucult(metin: str) -> str:
    # Python'un lower()'ı "İ"yi "i̇" (i + birleşik nokta) yapıyor; "Yurt İçi"
    # ayrıştırılamaz hâle geliyordu.
    return metin.replace("İ", "i").replace("I", "ı").lower()


def _sozcukler(metin: str) -> list[str]:
    metin = _kucult(metin).replace("’", "'")
    # Ekler kesme işaretinden sonra: "Türkiye'de", "Kırgızistan'da".
    metin = re.sub(r"'\w*", " ", metin)
    metin = re.sub(r"[^\wçğıöşü]+", " ", metin)
    return [s for s in metin.split() if s and not s.isdigit()]


def karsi_taraf_acik(ad: str | None) -> bool:
    """Karşı taraf gerçekten açıklanmış mı (isim var mı)."""
    if ad is None or not ad.strip():
        return False
    if not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", ad):
        return False
    if _CEVAPSIZ.search(_kucult(ad)):
        return False
    if _HUKUKI.search(_kucult(ad)) or _KURUM.search(_kucult(ad)):
        return True
    sozcukler = _sozcukler(ad)
    if not [s for s in sozcukler if s not in _GENEL]:
        return False
    if sozcukler and sozcukler[-1] in _BAS_AD:
        return False
    return True
