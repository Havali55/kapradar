"""12 aylık geçmiş bildirimleri KAP'tan çekip arşive indirir (spec §9, Adım 4).

İş bölümü: bu modül *ne çekileceğine* karar verir, `KapIstemcisi` nasıl
istendiğini bilir, `HamArsiv` ne saklandığını. Buradaki her karar tek bir
kısıttan doğuyor — KAP'ın WAF'ı asıl darboğaz (spec §13, risk 2):

- liste kaydındaki `subject` ile ön eleme: 949 bildirimlik bir haftada
  yalnızca ~6'sının detayı isteniyor
- arşivdeki her şey atlanıyor: aynı bildirim iki kez istenmiyor
- tek bir bildirimin hatası koşuyu durdurmuyor, özete yazılıp geçiliyor

LLM burada devreye girmiyor; bu adımın maliyeti sıfır.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta

from kap_radar.arsiv import HamArsiv
from kap_radar.istemci import KapErisimHatasi, KapIstemcisi

# Hedef şablonun liste yanıtındaki Türkçe adı. Şablonun makine kodu
# (`oda-12000`) yalnızca detay gövdesinde bulunduğu için ön eleme buna
# bakmak zorunda; kod doğrulaması ayrıştırma sırasında yapılır.
YENI_IS_ILISKISI = "Yeni İş İlişkisi"

# KAP liste yanıtını bu sayıda kesiyor (Adım 0 bulgusu). Dolu dönen bir
# pencerenin tam olduğu varsayılamaz.
LISTE_SINIRI = 2000


@dataclass
class BackfillOzeti:
    """Koşunun sonucu. Sessiz veri kaybı olmaması için eksikler de burada."""

    pencere: int = 0
    aday: int = 0
    cekildi: int = 0
    atlandi: int = 0
    hatalar: list[int] = field(default_factory=list)
    tasan_pencereler: list[tuple[date, date]] = field(default_factory=list)


def haftalik_pencereler(
    baslangic: date, bitis: date, gun: int = 7
) -> list[tuple[date, date]]:
    """Aralığı uç uca eklenen kapalı pencerelere böler.

    Pencereler bitişik: bir sonraki, bir öncekinin bitişinin ertesi günü
    başlar. Aradaki bir günlük boşluk o günün bildirimlerini sessizce
    kaybettirirdi.
    """
    pencereler: list[tuple[date, date]] = []
    pencere_basi = baslangic
    while pencere_basi <= bitis:
        pencere_sonu = min(pencere_basi + timedelta(days=gun - 1), bitis)
        pencereler.append((pencere_basi, pencere_sonu))
        pencere_basi = pencere_sonu + timedelta(days=1)
    return pencereler


def _pencere_kayitlari(
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    ozet: BackfillOzeti,
) -> list[dict]:
    """Bir pencerenin liste kayıtlarını verir; sınıra dayanırsa böler.

    Önbellekteki pencere yeniden sorulmaz. Yanıt 2.000'e dayandıysa
    pencere ikiye bölünüp yeniden sorulur — tam olduğu doğrulanamayan
    liste arşive yazılmaz, yoksa eksik veri kalıcılaşır.
    """
    if arsiv.liste_var_mi(baslangic, bitis):
        return arsiv.liste_oku(baslangic, bitis)

    kayitlar = istemci.liste(baslangic, bitis)

    if len(kayitlar) >= LISTE_SINIRI:
        if baslangic == bitis:
            # Tek gün bile sınıra dayanıyor: daha fazla bölünemez.
            ozet.tasan_pencereler.append((baslangic, bitis))
        else:
            orta = baslangic + (bitis - baslangic) // 2
            return _pencere_kayitlari(
                istemci, arsiv, baslangic, orta, ozet
            ) + _pencere_kayitlari(
                istemci, arsiv, orta + timedelta(days=1), bitis, ozet
            )

    arsiv.liste_yaz(baslangic, bitis, kayitlar)
    return kayitlar


def backfill(
    *,
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    konu: str = YENI_IS_ILISKISI,
    pencere_gun: int = 7,
    gunluk: Callable[[str], None] | None = None,
) -> BackfillOzeti:
    """Verilen aralıktaki hedef şablon bildirimlerini arşive indirir.

    Kaldığı yerden devam eder: arşivdeki pencereler yeniden sorulmaz,
    arşivdeki detaylar yeniden çekilmez. Aynı aralıkla ikinci kez
    çağrılmak güvenli ve ağ maliyeti neredeyse sıfır.
    """
    yaz = gunluk or (lambda mesaj: None)
    ozet = BackfillOzeti()

    for pencere_basi, pencere_sonu in haftalik_pencereler(
        baslangic, bitis, pencere_gun
    ):
        ozet.pencere += 1
        kayitlar = _pencere_kayitlari(istemci, arsiv, pencere_basi, pencere_sonu, ozet)
        adaylar = [k for k in kayitlar if k.get("subject") == konu]
        ozet.aday += len(adaylar)
        yaz(
            f"{pencere_basi} — {pencere_sonu}: {len(kayitlar)} bildirim, "
            f"{len(adaylar)} aday"
        )

        for aday in adaylar:
            indeks = int(aday["disclosureIndex"])
            if arsiv.var_mi(indeks):
                ozet.atlandi += 1
                continue
            try:
                arsiv.yaz(indeks, istemci.detay(indeks))
            except KapErisimHatasi as hata:
                # Tek bildirim yüzünden 20 dakikalık çekim çöpe gitmemeli;
                # eksik kalan indeks özette, ikinci koşu onu tekrar dener.
                ozet.hatalar.append(indeks)
                yaz(f"  HATA {indeks}: {hata}")
                continue
            ozet.cekildi += 1

    return ozet
