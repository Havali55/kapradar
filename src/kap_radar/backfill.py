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
from kap_radar.finansal import gelir_tablosu_govdesi
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
    # Liste isteği tüm denemelere rağmen düştü (WAF). Koşuyu kesmiyor;
    # o noktaya kadar inen her şey korunuyor, ikinci koşu bunları dener.
    hatali_pencereler: list[tuple[date, date]] = field(default_factory=list)
    # Finansal raporda gelir tablosu parçası bulunamadı. Sessizce
    # atlanırsa o şirketin paydası sebepsiz boş kalır.
    gelir_tablosuz: list[int] = field(default_factory=list)


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


# Bitişi bugünden en çok bu kadar gün önce olan pencere "açık": arşivden
# okunmaz, arşive yazılmaz. Gün bitmeden çekilen liste yarımdır; arşive
# girerse o günün sonraki bildirimleri bir daha hiç sorulmaz. Dün de açık
# sayılıyor çünkü KAP akşam geç saatte de bildirim düşürüyor ve sabah
# koşusu dünü yeniden görmeli.
ACIK_PENCERE_GUN = 1


def acik_mi(bitis: date, bugun: date) -> bool:
    return bitis >= bugun - timedelta(days=ACIK_PENCERE_GUN)


def pencere_kayitlari(
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    ozet: BackfillOzeti,
    bugun: date | None = None,
) -> list[dict]:
    """Bir pencerenin liste kayıtlarını verir; sınıra dayanırsa böler.

    Önbellekteki pencere yeniden sorulmaz. Yanıt 2.000'e dayandıysa
    pencere ikiye bölünüp yeniden sorulur — tam olduğu doğrulanamayan
    liste arşive yazılmaz, yoksa eksik veri kalıcılaşır. Aynı sebeple
    açık pencere (bkz. `ACIK_PENCERE_GUN`) de yazılmaz.
    """
    acik = acik_mi(bitis, bugun or date.today())
    if not acik and arsiv.liste_var_mi(baslangic, bitis):
        return arsiv.liste_oku(baslangic, bitis)

    kayitlar = istemci.liste(baslangic, bitis)

    if len(kayitlar) >= LISTE_SINIRI:
        if baslangic == bitis:
            # Tek gün bile sınıra dayanıyor: daha fazla bölünemez.
            ozet.tasan_pencereler.append((baslangic, bitis))
        else:
            orta = baslangic + (bitis - baslangic) // 2
            return pencere_kayitlari(
                istemci, arsiv, baslangic, orta, ozet, bugun
            ) + pencere_kayitlari(
                istemci, arsiv, orta + timedelta(days=1), bitis, ozet, bugun
            )

    if acik:
        arsiv.acik_liste_yaz(baslangic, bitis, kayitlar)
    else:
        arsiv.liste_yaz(baslangic, bitis, kayitlar)
    return kayitlar


def kapanan_acik_listeleri_sil(arsiv: HamArsiv, bugun: date) -> int:
    """Pencere kapandıysa geçici listesi artık eski: kalıcı arşivde tamı var."""
    kapanan = [(b, s) for b, s in arsiv.acik_listeler() if not acik_mi(s, bugun)]
    for baslangic, bitis in kapanan:
        arsiv.acik_liste_sil(baslangic, bitis)
    return len(kapanan)


def _guvenli_pencere(
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    ozet: BackfillOzeti,
    yaz: Callable[[str], None],
    bugun: date | None = None,
) -> list[dict] | None:
    """Pencereyi çeker; WAF ısırırsa koşuyu kesmeden özete yazar.

    Detay hataları baştan beri tolere ediliyordu ama liste hatası koşuyu
    ortasından kesiyordu: 2026-09-20'de 250 pencerelik finansal çekim
    tam da böyle düştü ve o ana kadar inen 151 rapor özetsiz kaldı.
    """
    try:
        return pencere_kayitlari(istemci, arsiv, baslangic, bitis, ozet, bugun)
    except KapErisimHatasi as hata:
        ozet.hatali_pencereler.append((baslangic, bitis))
        yaz(f"  PENCERE HATASI {baslangic} — {bitis}: {hata}")
        return None


def backfill(
    *,
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    konu: str = YENI_IS_ILISKISI,
    pencere_gun: int = 7,
    gunluk: Callable[[str], None] | None = None,
    bugun: date | None = None,
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
        kayitlar = _guvenli_pencere(
            istemci, arsiv, pencere_basi, pencere_sonu, ozet, yaz, bugun
        )
        if kayitlar is None:
            continue
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

    kapanan_acik_listeleri_sil(arsiv, bugun or date.today())
    return ozet


# ------------------------------------------------------- finansal raporlar

# Liste yanıtındaki konu adı. `disclosureClass == "FR"` yetmiyor: aynı
# sınıfta sorumluluk beyanı ve faaliyet raporu da var, onlarda gelir
# tablosu yok.
FINANSAL_RAPOR = "Finansal Rapor"


def finansal_adaylari(kayitlar: list[dict], tickerlar: set[str]) -> list[int]:
    """Hedef şirketlerin finansal rapor indekslerini süzer.

    BIST'te 550'den fazla şirket var, bizim 111'imiz; ön eleme olmasa
    çekim beş katına çıkardı. `stockCodes` çift paylı şirketlerde
    'MRBAS, MRS' gibi tek alanda geliyor, bu yüzden bölünüyor.
    """
    adaylar: list[int] = []
    for kayit in kayitlar:
        if kayit.get("subject") != FINANSAL_RAPOR:
            continue
        kodlar = {
            kod.strip() for kod in (kayit.get("stockCodes") or "").split(",")
        }
        if kodlar & tickerlar:
            adaylar.append(int(kayit["disclosureIndex"]))
    return adaylar


def finansal_backfill(
    *,
    istemci: KapIstemcisi,
    arsiv: HamArsiv,
    baslangic: date,
    bitis: date,
    tickerlar: set[str],
    pencere_gun: int = 3,
    gunluk: Callable[[str], None] | None = None,
    bugun: date | None = None,
) -> BackfillOzeti:
    """Hedef şirketlerin finansal raporlarını arşive indirir (Adım 7).

    Arşive yalnızca künye ve gelir tablosu yazılıyor: tam rapor ~2 MB ve
    beş parçanın dördü (bilanço, nakit akış, özkaynak, dipnotlar) bu
    projede hiç açılmıyor.
    """
    yaz = gunluk or (lambda mesaj: None)
    ozet = BackfillOzeti()

    for pencere_basi, pencere_sonu in haftalik_pencereler(
        baslangic, bitis, pencere_gun
    ):
        ozet.pencere += 1
        kayitlar = _guvenli_pencere(
            istemci, arsiv, pencere_basi, pencere_sonu, ozet, yaz, bugun
        )
        if kayitlar is None:
            continue
        adaylar = finansal_adaylari(kayitlar, tickerlar)
        ozet.aday += len(adaylar)
        yaz(
            f"{pencere_basi} — {pencere_sonu}: {len(kayitlar)} bildirim, "
            f"{len(adaylar)} rapor"
        )

        for indeks in adaylar:
            if arsiv.finansal_var_mi(indeks):
                ozet.atlandi += 1
                continue
            try:
                detay = istemci.detay(indeks)
            except KapErisimHatasi as hata:
                ozet.hatalar.append(indeks)
                yaz(f"  HATA {indeks}: {hata}")
                continue

            govde = gelir_tablosu_govdesi(detay)
            if govde is None:
                # Bankalar ve bazı yatırım ortaklıkları farklı taksonomi
                # kullanıyor olabilir; sessizce atlanırsa o şirketin
                # paydası sebepsiz boş kalır.
                ozet.gelir_tablosuz.append(indeks)
                continue

            arsiv.finansal_yaz(
                indeks, {"disclosure": detay["disclosure"], "gelirTablosu": govde}
            )
            ozet.cekildi += 1

    kapanan_acik_listeleri_sil(arsiv, bugun or date.today())
    return ozet
