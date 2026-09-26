"""Modül B bağlamı: gerçek VBTS, devre kesici ve bildirim sıklığı.

Adım 17'deki tahta bayrağı fiyat serisinden bir VEKİLLE hesaplanıyordu
(|günlük getiri| ≥ %9 olan gün). 2026-09-22'de liste arşivinin
(`data/ham/liste/`) Borsa İstanbul'un kendi kayıtlarını taşıdığı
görüldü:

  - "Pay Bazında Devre Kesici Bildirimi": hissede devre kesicinin
    başladığı an. Onaylanan eşikler (V90 ≤ 2 temiz, V90 > 6 tedbirli)
    zaten bu sayı üzerine kurulmuştu. Eski belgelerde buna "VBTS"
    deniyordu; yanlış ad, bu devre kesici.
  - "Pay Piyasasında Volatilite Bazlı Tedbir Sistemi": asıl VBTS.
    Detay metni tedbirin kademesini ve başlangıç–bitiş seansını veriyor.

Vekille karşılaştırma: vekilin "tedbirli" dediği 87 bildirimin 50'sinde
90 günde hiç VBTS yok, "temiz" dediklerinin 12'si gerçekte VBTS altında.

Bildirim sıklığı da buraya taşındı çünkü aynı kusuru taşıyordu: arşivin
tamamından sayılıyordu, yani Ekim 2025'teki bir bildirim Ağustos 2026'da
yapılacakları da sayıyordu. Artık yalnız bildirim anından önceki 12 ay.

Buradaki her şey saf; disk ve veritabanı `scripts/baglam_hesapla.py`'de.
"""

from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from kap_radar.skor import TAHTA_TEDBIRLI_V90

DEVRE_KESICI_KONUSU = "Pay Bazında Devre Kesici Bildirimi"
# İki ifade dönemi var: 2024–25 "Başlamıştır", sonrası "devreye girmiştir".
DEVRE_KESICI_BASLADI = ("başlamıştır", "devreye girmiştir")
VBTS_OZETI = "Volatilite Bazlı Tedbir"
YENI_IS_KONUSU = "Yeni İş İlişkisi"


class VbtsKademesi:
    """VBTS kademeleri — sayı büyüdükçe tedbir ağırlaşır."""

    KREDI_YASAGI = 1  # kredili işlem (ve BIST 50 dışında açığa satış) yasağı
    BRUT_TAKAS = 2
    EMIR_PAKETI = 3
    TEK_FIYAT = 4


# Ağırdan hafife: emir paketi metni önceki kademelerin sürdüğünü de
# yazıyor, ilk eşleşen ağır olan kazanmalı.
_KADEME_KALIPLARI = (
    (VbtsKademesi.TEK_FIYAT, "tek fiyat"),
    (VbtsKademesi.EMIR_PAKETI, "emir paketi"),
    (VbtsKademesi.BRUT_TAKAS, "brüt takas"),
    (VbtsKademesi.KREDI_YASAGI, "kredili işlem"),
    (VbtsKademesi.KREDI_YASAGI, "açığa satış"),
)
_TARIH = r"(\d{2})/(\d{2})/(\d{4})"
_ARALIK = re.compile(
    _TARIH + r" tarihli işlemlerden.*?" + _TARIH + r" tarihli işlemlere",
    re.S,
)
_PAY = re.compile(r"\b([A-Z0-9]{3,6})\.E\b")


@dataclass(frozen=True)
class VbtsTedbiri:
    ticker: str
    kademe: int
    baslangic: date
    bitis: date


class VbtsAyristirmaHatasi(ValueError):
    pass


def _tarih(g: tuple[str, str, str]) -> date:
    gun, ay, yil = g
    return date(int(yil), int(ay), int(gun))


def vbts_ayristir(metin: str) -> list[VbtsTedbiri]:
    """Duyurunun Türkçe metninden hisse başına tedbir.

    Tanınmayan bir kalıp sessizce atlanmaz, hata verir: yanlış ya da eksik
    tedbir, tahtayı olduğundan temiz gösterir.
    """
    bas = metin.find("(VBTS) kapsamında")
    if bas == -1:
        raise VbtsAyristirmaHatasi("Türkçe VBTS cümlesi bulunamadı")
    cumle = metin[bas:]
    son = cumle.find("Not:")
    if son != -1:
        cumle = cumle[:son]

    aralik = _ARALIK.search(cumle)
    if aralik is None:
        raise VbtsAyristirmaHatasi("tarih aralığı bulunamadı")
    paylar = _PAY.findall(cumle[: aralik.start()])
    if not paylar:
        raise VbtsAyristirmaHatasi("pay kodu bulunamadı")

    kucuk = cumle.lower()
    kademe = next((k for k, kalip in _KADEME_KALIPLARI if kalip in kucuk), None)
    if kademe is None:
        raise VbtsAyristirmaHatasi("tedbir türü tanınmadı")

    baslangic = _tarih(aralik.groups()[:3])
    bitis = _tarih(aralik.groups()[3:])
    return [VbtsTedbiri(p, kademe, baslangic, bitis) for p in dict.fromkeys(paylar)]


def aktif_vbts_kademesi(tedbirler: Sequence[VbtsTedbiri], gun: date) -> int:
    """`gun` itibarıyla yürürlükteki en ağır kademe; yoksa 0."""
    return max(
        (t.kademe for t in tedbirler if t.baslangic <= gun <= t.bitis),
        default=0,
    )


def pencere_sayisi(
    zamanlar: Sequence[datetime], an: datetime, baslangic: datetime
) -> int:
    """[baslangic, an) içindeki olay sayısı. `zamanlar` sıralı olmalı.

    Aralık `an`da AÇIK: bildirimle aynı anda ya da sonra olan olay
    bildirim anında bilinemezdi.
    """
    return bisect_left(zamanlar, an) - bisect_left(zamanlar, baslangic)


def ayri_gun_sayisi(
    zamanlar: Sequence[datetime], an: datetime, baslangic: datetime
) -> int:
    """[baslangic, an) içinde olay görülen AYRI gün sayısı (devre kesici).

    Aynı gün birden fazla tetiklenme tahtanın o günkü karakterini
    değiştirmiyor; ifade değişikliği döneminde aynı olayın iki kez
    yayınlanmış olması da sayıyı şişirmiyor.
    """
    lo, hi = bisect_left(zamanlar, baslangic), bisect_left(zamanlar, an)
    return len({z.date() for z in zamanlar[lo:hi]})


def seans_baslangici(takvim: Sequence[date], gun: date, seans: int) -> date:
    """`gun` dahil geriye doğru `seans` işlem gününün ilki."""
    i = bisect_right(takvim, gun)  # gun'e kadar (dahil) kaç işlem günü
    return takvim[max(0, i - seans)]


def on_iki_ay_once(an: datetime) -> datetime:
    return an - timedelta(days=365)


def piyasa_oynak_orani(
    devre: Mapping[str, Sequence[datetime]],
    *,
    evren: Iterable[str],
    an: datetime,
    bas90: datetime,
    bas5: datetime,
) -> float | None:
    """Evrendeki hisselerin kaçı `an` itibarıyla "çok oynak" sayılırdı?

    Tahta bayrağıyla aynı sayım kuralı (V90 > eşik ya da V5 ≥ 2); VBTS
    hariç, çünkü soru devre kesici sayımının piyasa geneline göre ne
    kadar sıra dışı olduğu. 2026-09 bildirimlerinin %66'sı "çok
    oynak"tı ama piyasanın da %44'ü öyleydi: taban oranı olmadan etiket
    şirkete özgü okunuyor.
    """
    hisseler = list(evren)
    if not hisseler:
        return None
    oynak = sum(
        1
        for h in hisseler
        if ayri_gun_sayisi(devre.get(h, ()), an, bas90) > TAHTA_TEDBIRLI_V90
        or ayri_gun_sayisi(devre.get(h, ()), an, bas5) >= 2
    )
    return oynak / len(hisseler)
