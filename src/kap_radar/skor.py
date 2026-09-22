"""Etki skoru, tepki paneli ve tahta bayrağı — deterministik hesaplar.

Kaynak: `docs/arastirma/2026-09-19-skor-formulu-onerisi.md` (onaylandı
2026-09-20). Spec §8'in eski toplamsal formülü
(`2.5 + w1·f(ciro) + w2·g(karşı taraf) + w3·h(süre)`) kanıt taramasından
sonra bırakıldı. Üç değişiklik:

1. **2,5 tabanı kalktı.** Tutarı açıklanmamış bildirim otomatik "orta
   etki" almıyor; tutar ya da hasılat yoksa skor hiç gösterilmiyor.
2. **Süre bileşeni düştü.** KAP yalnız başlangıç tarihini veriyor ve
   sürenin önemli olduğuna dair kanıt yok.
3. **Devre kesici skora girmiyor.** En güçlü istatistiksel sinyal o
   (−2,48 puan) ama bildirimin değil *hissenin* özelliği: skora
   katılsaydı "neden 3,2?" sorusunun cevabı "çünkü hisse spekülatif"
   olurdu. Ayrı bayrak olarak yanında duruyor.

Skor bir **getiri tahmini değil**. Kanıt taraması tepkinin
öngörülemediğini gösterdi (tüm sinyaller 3 günlük CAR'ın %6,4'ünü
açıklıyor). Burada üretilen sayı bildirimin *büyüklüğü*; geçmiş tepki
ayrı ve betimleyici bir panelde duruyor.

Modülün tamamı saf fonksiyon: aynı girdi → aynı skor, LLM kanaati yok.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Callable, Sequence

from kap_radar.cikarim import Tutar

__all__ = [
    "Agirliklar",
    "MEGA_ESIGI",
    "ONEMLI_ESIGI",
    "SiklikBayragi",
    "TahtaBayragi",
    "TepkiPaneli",
    "VARSAYILAN_AGIRLIKLAR",
    "buyukluk_skoru",
    "f_oran",
    "guvenilirlik",
    "kademe",
    "net_tutar_tl",
    "siklik_bayragi",
    "tahta_bayragi",
    "tepki_paneli",
]


@dataclass(frozen=True)
class Agirliklar:
    """Skorun ayarlanabilir sabitleri.

    Kodda gömülü değil: altın küme büyüdükçe yeniden kalibre edilecek
    ve aynı girdinin hangi ayarla hangi skoru verdiği izlenebilir olmalı.
    """

    azami: Decimal = Decimal("5")
    # Taban 2026-09-22'de %1'den %0,25'e indirildi. Adım 16 geçerlilik
    # sınaması %1 tabanını çürüttü: taban altındaki 58 bildirimde işlem
    # hacmi yine %+33,4 artıyor (t=+3,39) ve taban üstünden ayırt
    # edilemiyor (Welch p=0,51). Eski eşik 480 skorlu bildirimin 62'sine
    # "olay değil" diyordu; yeni eşikte bu 7'ye iniyor.
    #
    # Sıfırlanmıyor, yalnız indiriliyor: f(r) logaritmik, taban 0 olursa
    # log10(0) tanımsız.
    taban_oran: Decimal = Decimal("0.0025")  # %0,25 altı: ölçülemeyecek kadar küçük
    # Tavan %100'de KALIYOR. Adım 16'da "işlevsiz, nadiren bağlıyor"
    # diye ölçüldü ve %50'ye çekilmesi önerilmişti; ölçüm doğru, çıkarım
    # yanlıştı. İşlevsiz bir tavan zarar vermiyor, indirmek zarar
    # veriyor: %100'de 480 kaydın 1'ini bağlıyor, %50'de 12'sini — yani
    # tepedeki bir düzine bildirim 5,00'de birbirine eşitlenip ayrım
    # kayboluyordu.
    tavan_oran: Decimal = Decimal("1.00")  # %100 üstü: daha fazla ayrım yok

    # K — güvenilirlik çarpanı. Kanıt taramasındaki 2×2 tablodan:
    # açık+ilk +%1,23 (n=327) · açık+güncelleme +%0,68 (n=55)
    # gizli+ilk +%0,02 (n=213) · gizli+güncelleme −%5,18 (n=6)
    k_acik_ilk: Decimal = Decimal("1.00")
    k_acik_guncelleme: Decimal = Decimal("0.85")
    k_gizli_ilk: Decimal = Decimal("0.70")
    k_gizli_guncelleme: Decimal = Decimal("0.50")


VARSAYILAN_AGIRLIKLAR = Agirliklar()

# Skora giren tipler. `toplam_sozlesme` projenin kümülatif bedeli —
# yeni iş değil; karıştırılırsa ORGE örneğinde oran ~12 kat şişer.
SKORA_GIREN_TIPLER = frozenset({"ilave_siparis", "fiyat_farki", "tek_seferlik"})

# Kademe eşikleri — kanonik tanım burası. `site/lib/veri.ts::kademeBul`
# bunun birebir kopyası; biri değişirse diğeri de değişmeli, yoksa
# arayüzdeki etiket ile betiklerin raporladığı dağılım ayrışır.
#
# 2026-09-22: taban %1'den %0,25'e indiği için 3,0/2,0 → 3,5/2,5.
# Eşikler kademelerin nüfus payını koruyacak şekilde seçildi (yüzdelik
# eşleme): mega 55 bildirim (eskiden 60), önemli+ 164 (eskiden 153).
MEGA_ESIGI = Decimal("3.5")
ONEMLI_ESIGI = Decimal("2.5")

_IKI_HANE = Decimal("0.01")


def _yuvarla(deger: Decimal) -> Decimal:
    return deger.quantize(_IKI_HANE, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- f(r)


def f_oran(
    oran: Decimal, agirliklar: Agirliklar = VARSAYILAN_AGIRLIKLAR
) -> Decimal:
    """Ciro oranını 0–1 aralığına logaritmik olarak taşır.

    Neden logaritmik: materyallik çarpımsaldır — %1'den %2'ye çıkmak ile
    %10'dan %20'ye çıkmak aynı şeyi söyler. Doğrusal ölçek aralığın
    tamamını dev sözleşmelere harcar ve asıl ayrımın olduğu %1–%20
    bandını ezer.
    """
    if oran <= agirliklar.taban_oran:
        return Decimal("0")
    if oran >= agirliklar.tavan_oran:
        return Decimal("1")

    taban = math.log10(float(agirliklar.taban_oran))
    tavan = math.log10(float(agirliklar.tavan_oran))
    konum = (math.log10(float(oran)) - taban) / (tavan - taban)
    return Decimal(str(konum))


def guvenilirlik(
    *,
    karsi_taraf_acik: bool,
    guncelleme_mi: bool,
    agirliklar: Agirliklar = VARSAYILAN_AGIRLIKLAR,
) -> Decimal:
    """K — büyüklüğü ezmeyen, onu ölçekleyen güvenilirlik çarpanı.

    Çarpımsal, toplamsal değil: karşı tarafı gizli dev bir sözleşme hâlâ
    büyüktür, sadece daha az güvenilirdir.
    """
    if karsi_taraf_acik:
        return (
            agirliklar.k_acik_guncelleme if guncelleme_mi else agirliklar.k_acik_ilk
        )
    return agirliklar.k_gizli_guncelleme if guncelleme_mi else agirliklar.k_gizli_ilk


# ----------------------------------------------------------- net tutar


def net_tutar_tl(
    tutarlar: Sequence[Tutar],
    kur_coz: Callable[[str], Decimal | None],
) -> Decimal | None:
    """Skora giren kalemleri bildirim tarihli kurla TL'ye çevirip toplar.

    `kur_coz` bir para birimi kodu alıp o günün TCMB alış kurunu verir;
    bulamazsa None. Eksik kuru sıfır saymak toplamı sessizce küçültürdü,
    bu yüzden tek eksik kur tüm sonucu None yapar (§6 kapısı B2 bunu
    elle incelemeye düşürür).
    """
    skora_girenler = [t for t in tutarlar if t.tip in SKORA_GIREN_TIPLER]
    if not skora_girenler:
        return None

    toplam = Decimal("0")
    for kalem in skora_girenler:
        kur = kur_coz(kalem.para_birimi)
        if kur is None:
            return None
        toplam += kalem.deger * kur
    return _yuvarla(toplam)


# --------------------------------------------------------------- skor


def buyukluk_skoru(
    *,
    net_tutar_tl: Decimal | None,
    ttm_hasilat: Decimal | None,
    karsi_taraf_acik: bool,
    guncelleme_mi: bool,
    agirliklar: Agirliklar = VARSAYILAN_AGIRLIKLAR,
) -> Decimal | None:
    """`S = clamp(5 · f(r) · K, 0, 5)` — bildirimin büyüklüğü.

    Tutar ya da hasılat yoksa None: skor gösterilmez, yerine etiket
    konur. Bildirimlerin ~%15'i skorsuz kalıyor ve bu kabul edilmiş bir
    sonuç — uydurulmuş bir payda ile üretilen skor, skorsuzluktan kötü.
    """
    if not net_tutar_tl or not ttm_hasilat or ttm_hasilat <= 0:
        return None

    oran = net_tutar_tl / ttm_hasilat
    ham = (
        agirliklar.azami
        * f_oran(oran, agirliklar)
        * guvenilirlik(
            karsi_taraf_acik=karsi_taraf_acik,
            guncelleme_mi=guncelleme_mi,
            agirliklar=agirliklar,
        )
    )
    return _yuvarla(max(Decimal("0"), min(agirliklar.azami, ham)))


def kademe(skor: Decimal | None) -> str | None:
    """Skoru kullanıcının gördüğü etikete çevirir.

    Skorsuz bildirim kademesiz: `None` "rutin" değildir. Tutarı
    açıklanmamış bir bildirime "rutin" demek, ölçmediğimiz şeyi küçük
    ilan etmek olurdu.
    """
    if skor is None:
        return None
    if skor >= MEGA_ESIGI:
        return "mega"
    if skor >= ONEMLI_ESIGI:
        return "onemli"
    return "rutin"


# -------------------------------------------------------- tepki paneli


@dataclass(frozen=True)
class TepkiPaneli:
    """Benzer bildirimlerin geçmiş tepkisi — tahmin değil, betimleme."""

    n: int
    medyan: Decimal
    alt_ceyrek: Decimal
    ust_ceyrek: Decimal
    pozitif_orani: Decimal


def tepki_paneli(carlar: Sequence[Decimal]) -> TepkiPaneli | None:
    """Anormal getiri kümesini medyan ve çeyrekliklerle özetler.

    Ortalama bilerek yok: 20 günlük ortalamalarımız (+%2,82) medyanlarla
    (+%2,13 / −%2,51) çelişiyor, yani birkaç uç gözleme ait. Ortalamayı
    yayınlamak tipik bir yatırımcının göreceği şeyi yanlış anlatır.
    """
    if not carlar:
        return None

    sirali = sorted(carlar)
    pozitif = sum(1 for c in sirali if c > 0)
    return TepkiPaneli(
        n=len(sirali),
        medyan=_yuzdelik(sirali, Decimal("0.50")),
        alt_ceyrek=_yuzdelik(sirali, Decimal("0.25")),
        ust_ceyrek=_yuzdelik(sirali, Decimal("0.75")),
        pozitif_orani=Decimal(pozitif) / Decimal(len(sirali)),
    )


def _yuzdelik(sirali: Sequence[Decimal], oran: Decimal) -> Decimal:
    """En yakın sıra istatistiği; ara değer üretmiyor.

    Gerçekte gözlenmiş bir getiriyi göstermek, iki gözlem arasında
    hiç yaşanmamış bir sayı uydurmaktan dürüst.
    """
    indeks = int(oran * (len(sirali) - 1))
    return sirali[indeks]


# ------------------------------------------------------- tahta bayrağı


class TahtaBayragi(Enum):
    """Hissenin tahta kalitesi — bildirimin değil, hissenin özelliği."""

    TEMIZ = "temiz"
    HAREKETLI = "hareketli"
    TEDBIRLI = "tedbirli"


class SiklikBayragi(Enum):
    """Şirketin bildirim sıklığı — bildirim yorgunluğu bağlamı."""

    SEYREK = "seyrek"
    ORTA = "orta"
    SIK = "sik"


# Eşikler arşiv penceresindeki (12 ay) bildirim sayısının ÜÇLÜK
# kesimlerinden: 613 bildirimi %33,9 / %33,1 / %33,0 diye bölüyor.
# Adım 16'nın kendi analizi de sıklığı üçlüklere ayırmıştı, aynı kesim.
# Şirket sayısı dağılımı çok daha çarpık (87 / 16 / 8): birkaç sık
# bildirimci bildirimlerin üçte birini tek başına üretiyor.
SIKLIK_ORTA_ESIGI = 8
SIKLIK_SIK_ESIGI = 18


def siklik_bayragi(adet: int) -> SiklikBayragi:
    """Son 12 ayda `adet` bildirim yapmış şirketin yorgunluk kademesi.

    **Skora girmez.** Adım 16'nın en sağlam bulgusu buydu — ln(sıklık)
    katsayısı −0,111, hisse-kümelenmiş t=−2,48 (p=0,013); yılda ~30
    bildirim yapan şirketlerde bildirim başına tepki seyreklerin
    yarısından az. Skora katılmamasının sebebi tahta bayrağıyla aynı:
    bu *şirketin* özelliği, bildirimin değil. Skora gömülseydi "neden
    2,4?" sorusunun cevabı "çünkü şirket çok bildirim yapıyor" olurdu.

    `adet` bildirimden ÖNCEKİ 12 aydaki Yeni İş İlişkisi sayısı, bu
    bildirim dahil (`siklik_durumu.yeni_is_12a`). 2026-09-22'ye kadar
    arşivin tamamından sayılıyordu — ileriye bakıyordu ve 613 bildirimin
    121'inde kademeyi değiştiriyordu. Bulgu lookahead'siz ölçüyle de
    ayakta: katsayı −0,116, kümelenmiş t=−2,29 (p=0,022). Eşikler
    değişmedi; point-in-time sayımın üçlükleri 7/18, mevcut 8/18.
    """
    if adet >= SIKLIK_SIK_ESIGI:
        return SiklikBayragi.SIK
    if adet >= SIKLIK_ORTA_ESIGI:
        return SiklikBayragi.ORTA
    return SiklikBayragi.SEYREK


# Devre kesici günü (90 seans) üçlükleri — bkz. tahta_bayragi.
TAHTA_TEMIZ_V90 = 4
TAHTA_TEDBIRLI_V90 = 8


def tahta_bayragi(*, v90: int, v5: int, vbts_kademe: int = 0) -> TahtaBayragi:
    """Son 90 ve son 5 seanstaki devre kesici günü + yürürlükteki VBTS.

    Eşikler formül önerisinden. Sıra tersten kuruldu — en ağır durum
    önce: `v90=3, v5=2` hem 'hareketli' hem 'tedbirli' eşiğini
    karşılıyor, iki devre kesici gören bir tahtayı 'hareketli' diye
    yayınlamak yanıltıcı olurdu.

    `vbts_kademe` > 0: bildirim anında Borsa İstanbul'un volatilite
    tedbiri yürürlükte. Bu, "tedbirli" kelimesinin tam anlamı; sayım
    eşiklerinin altında kalsa bile tahta tedbirlidir.

    Eşikler (2026-09-22, Hüseyin onayı): v90 bildirim ağırlıklı
    üçlüklerden (4 / 8) — sıklık etiketiyle aynı kural. Önceki 2 / 6
    limit yakını gün vekili için kurulmuştu; gerçek devre kesici daha sık
    tetiklendiği için bildirimlerin %47'sini "tedbirli" yapıyordu. S~AV
    katsayısı gruplara göre: 4/8 ile +0,168 / +0,026 / −0,068; 2/6 ile
    +0,109 / +0,121 / −0,060. 4/8 sonuçlar görüldükten sonra seçildi —
    gerekçesi sonuç değil, sıklıkla aynı üçlük kuralı.
    """
    if vbts_kademe > 0 or v90 > TAHTA_TEDBIRLI_V90 or v5 >= 2:
        return TahtaBayragi.TEDBIRLI
    if v90 <= TAHTA_TEMIZ_V90 and v5 == 0:
        return TahtaBayragi.TEMIZ
    return TahtaBayragi.HAREKETLI
