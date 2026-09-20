"""Altın küme için 50 bildirimlik tabakalı örnek seçer (spec §9, Adım 8).

Kullanım:
    python scripts/altin_kume_sec.py > data/altin_kume_ham.txt

Rastgele 50 bildirim yanlış olurdu: doğruluk ölçümünün işe yaraması için
örnek **zor olanı** temsil etmeli. Tabakalar gerçek hatalardan çıkarıldı:

- `ilave_toplam`  : ilave sipariş ile revize toplam sözleşme bedeli aynı
                    metinde. Karıştırılırsa ciro oranı ~12 kat şişiyor
                    (ORGE 1665567). Spec en az 10 tane istiyor.
- `mukerrer_cevrim`: aynı tutar iki para biriminde, biri parantez içinde
                    (ARDYZ 1664397: '1.040.400 USD (50.613.963 TL)').
                    İki kalem sayılırsa net tutar ikiye katlanıyor.
- `cok_para`      : birden çok para birimi, mükerrer çevrim olmadan.
- `tutarsiz`      : tutar açıklanmamış ya da ticari sır. Kapının
                    `tutar_gizli` dalı burada sınanıyor.
- `guncelleme`    : önceki bir açıklamanın güncellemesi.
- `gizli_karsi_taraf`: KAP'ın karşı taraf alanı boş (bildirimlerin %36,5'i).
- `sade`          : tek tutar, tek para birimi — kolay hâl de temsil edilsin.

Seçim deterministik (kap_index sırası): aynı komut aynı 50 bildirimi verir.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayristirici import bildirim_ayristir  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"

KOTALAR = {
    "ilave_toplam": 12,
    "mukerrer_cevrim": 5,
    "cok_para": 8,
    "tutarsiz": 6,
    "guncelleme": 6,
    "gizli_karsi_taraf": 6,
    "sade": 7,
}

_PARA = {
    "TRY": re.compile(r"\b(?:TL|TRY)\b|₺", re.IGNORECASE),
    "USD": re.compile(r"\b(?:USD|Dolar)\b|\$", re.IGNORECASE),
    "EUR": re.compile(r"\b(?:EUR|Euro|Avro)\b|€", re.IGNORECASE),
}
_ILAVE = re.compile(r"ilave|ek sipariş|artırıl|arttırıl", re.IGNORECASE)
# Dar kalıp ('toplam sözleşme|revize') arşivde yalnız 9 bildirim buluyordu,
# spec en az 10 istiyor. Şirketler kümülatif bedeli 'sözleşme tutarı',
# 'toplam bedel', 'proje bedeli' diye de yazıyor.
_TOPLAM = re.compile(
    r"toplam sözleşme|sözleşme bedeli|sözleşme büyüklüğü|revize"
    r"|sözleşme tutarı|toplam bedel|proje bedeli|toplam tutar",
    re.IGNORECASE,
)
# '1.040.400 USD (50.613.963 TL)' — parantez içinde şirketin kendi çevirisi
_CEVRIM = re.compile(r"\d[\d.,]*\s*(?:USD|EUR|\$|€)[^()]{0,40}\(\s*[\d.,\s]+\s*TL", re.IGNORECASE)
_SAYI = re.compile(r"\d[\d.]{4,}")
_GIZLI = re.compile(r"ticari sır|açıklanmamış|paylaşılmamaktadır", re.IGNORECASE)


def tabaka(bildirim) -> str:
    metin = bildirim.ham_metin_tr or ""
    paralar = {ad for ad, kalip in _PARA.items() if kalip.search(metin)}

    # Sıra önemli: ilave/toplam ayrımı en kritik tabaka, mükerrer
    # çevrimle aynı bildirimde görünse bile oraya yazılıyor.
    if _ILAVE.search(metin) and _TOPLAM.search(metin):
        return "ilave_toplam"
    if _CEVRIM.search(metin):
        return "mukerrer_cevrim"
    if not _SAYI.search(metin) or _GIZLI.search(metin):
        return "tutarsiz"
    if len(paralar) > 1:
        return "cok_para"
    if bildirim.guncelleme_mi:
        return "guncelleme"
    if not bildirim.kap_alanlari.get("karsi_taraf"):
        return "gizli_karsi_taraf"
    return "sade"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    arsiv = HamArsiv(VARSAYILAN_ARSIV)
    tabakalar: dict[str, list] = {ad: [] for ad in KOTALAR}

    for indeks in arsiv.indeksler():
        bildirim = bildirim_ayristir(arsiv.oku(indeks))
        if bildirim.sablon_kodu != "oda-12000":
            continue
        tabakalar[tabaka(bildirim)].append(bildirim)

    print("# tabaka dagilimi", file=sys.stderr)
    for ad, kayitlar in tabakalar.items():
        print(f"#   {ad:20} {len(kayitlar):>4} (kota {KOTALAR[ad]})", file=sys.stderr)

    secilen = []
    for ad, kota in KOTALAR.items():
        secilen.extend((ad, b) for b in tabakalar[ad][:kota])

    print(f"# secilen: {len(secilen)} bildirim", file=sys.stderr)

    for ad, b in secilen:
        karsi = b.kap_alanlari.get("karsi_taraf") or "-"
        print("=" * 78)
        print(f"KAP_ID     : {b.kap_id}")
        print(f"INDEX      : {b.kap_index}")
        print(f"TABAKA     : {ad}")
        print(f"TICKER     : {b.ticker}  ({b.sirket_unvani})")
        print(f"ZAMAN      : {b.yayin_zamani}")
        print(f"KARSI TARAF: {karsi}")
        print(f"GUNCELLEME : {b.guncelleme_mi}   DUZELTME: {b.duzeltme_mi}")
        print("-" * 78)
        print(b.ham_metin_tr.strip())
        kosullar = b.kap_alanlari.get("sozlesme_kosullari")
        if kosullar:
            print("--- sozlesme kosullari ---")
            print(kosullar.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
