"""Modül B bağlamını gerçek KAP verisinden hesaplar (tahta + sıklık).

Kullanım:
    python scripts/baglam_hesapla.py --kuru    # yalnız dağılım ve karşılaştırma
    python scripts/baglam_hesapla.py           # tahta_durumu + siklik_durumu yaz

Girdi (ağa çıkmaz):
  - data/ham/liste/     KAP liste arşivi, 2024-09'dan beri tüm türler
  - data/ham/vbts/      VBTS duyurularının detayı (scripts/vbts_cek.py)
  - endeks_gunluk       işlem takvimi

Her sayım POINT-IN-TIME: yalnız bildirim anından önce yayınlanmış
kayıtlar. Tanımlar `src/kap_radar/baglam.py`, eşikler `skor.py`.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from bisect import insort
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.baglam import (  # noqa: E402
    DEVRE_KESICI_BASLADI,
    DEVRE_KESICI_KONUSU,
    VBTS_OZETI,
    YENI_IS_KONUSU,
    VbtsAyristirmaHatasi,
    aktif_vbts_kademesi,
    ayri_gun_sayisi,
    pencere_sayisi,
    seans_baslangici,
    vbts_ayristir,
)
from kap_radar.skor import siklik_bayragi, tahta_bayragi  # noqa: E402

ISTANBUL = ZoneInfo("Europe/Istanbul")
LISTE_KLASORU = KOK / "data" / "ham" / "liste"
VBTS_KOKU = KOK / "data" / "ham" / "vbts"
YONTEM = "kap_v1"
CSV_CIKTI = KOK / "data" / "baglam_kap_v1.csv"
V90_SEANS, V5_SEANS = 90, 5


def zaman(kayit: dict) -> datetime:
    return datetime.strptime(kayit["publishDate"], "%d.%m.%Y %H:%M:%S")


def kodlar(alan: str | None) -> list[str]:
    return [k.strip() for k in (alan or "").split(",") if k.strip()]


def govde_metni(detay: dict) -> str:
    govde = detay.get("disclosureBody") or []
    metin = " ".join(govde) if isinstance(govde, list) else str(govde)
    metin = html.unescape(re.sub(r"<[^>]+>", " ", metin))
    return re.sub(r"\s+", " ", metin)


def arsivi_oku():
    kayitlar: dict[int, dict] = {}
    for dosya in sorted(LISTE_KLASORU.glob("*.json")):
        for k in json.loads(dosya.read_text(encoding="utf-8")):
            kayitlar[k["disclosureIndex"]] = k

    devre = defaultdict(list)
    yeni_is = defaultdict(list)
    oda = defaultdict(list)
    ilk = {}
    vbts_indeks = []
    for k in kayitlar.values():
        z = zaman(k)
        sirket_kodlari = kodlar(k.get("stockCodes"))
        for kod in sirket_kodlari:
            ilk[kod] = min(ilk.get(kod, z), z)
        if k.get("subject") == DEVRE_KESICI_KONUSU and any(
            s in (k.get("summary") or "").lower() for s in DEVRE_KESICI_BASLADI
        ):
            for kod in kodlar(k.get("relatedStocks")):
                insort(devre[kod], z)
        elif VBTS_OZETI in (k.get("summary") or ""):
            vbts_indeks.append(k["disclosureIndex"])
        if k.get("disclosureClass") == "ODA":
            for kod in sirket_kodlari:
                insort(oda[kod], z)
        if k.get("subject") == YENI_IS_KONUSU:
            for kod in sirket_kodlari:
                insort(yeni_is[kod], z)
    return len(kayitlar), devre, yeni_is, oda, ilk, vbts_indeks


def vbts_oku(indeksler: list[int]):
    arsiv = HamArsiv(VBTS_KOKU)
    tedbirler = defaultdict(list)
    eksik, hatali = [], []
    for i in indeksler:
        if not arsiv.var_mi(i):
            eksik.append(i)
            continue
        try:
            for t in vbts_ayristir(govde_metni(arsiv.oku(i))):
                tedbirler[t.ticker].append(t)
        except VbtsAyristirmaHatasi as hata:
            hatali.append((i, str(hata)))
    return tedbirler, eksik, hatali


def ucluk_esikleri(degerler: list[int]) -> tuple[int, int]:
    s = sorted(degerler)
    return s[len(s) // 3], s[2 * len(s) // 3]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kuru", action="store_true", help="yazma")
    ap.add_argument(
        "--yalniz-siklik",
        action="store_true",
        help="tahta_durumu'na dokunma, yalnız siklik_durumu yaz",
    )
    secenek = ap.parse_args()

    n_kayit, devre, yeni_is, oda, ilk, vbts_indeks = arsivi_oku()
    tedbirler, eksik, hatali = vbts_oku(vbts_indeks)
    print(f"liste arşivi : {n_kayit} tekil bildirim")
    print(f"devre kesici : {sum(map(len, devre.values()))} başlangıç, {len(devre)} hisse")
    print(f"VBTS         : {len(vbts_indeks)} duyuru, {sum(map(len, tedbirler.values()))} "
          f"hisse-tedbir, {len(tedbirler)} hisse")
    if eksik or hatali:
        print(f"  !! detayı eksik {len(eksik)}, ayrıştırılamayan {len(hatali)}")
        for i, h in hatali[:10]:
            print(f"     {i}: {h}")
        if not secenek.kuru:
            print("  Eksik/hatalı VBTS varken yazılmaz — tahta olduğundan temiz görünür.")
            return 1

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute("select tarih from public.endeks_gunluk order by tarih")
            takvim = [r[0] for r in imlec.fetchall()]
            imlec.execute(
                "select b.kap_id, b.ticker, b.yayin_zamani, td.bayrak "
                "from public.bildirim b "
                "left join public.tahta_durumu td on td.kap_id = b.kap_id "
                "order by b.yayin_zamani"
            )
            bildirimler = imlec.fetchall()

        tahta_satir, siklik_satir = [], []
        gecis = Counter()
        kademe_say = Counter()
        for kap_id, ticker, yayin, eski_bayrak in bildirimler:
            an = yayin.astimezone(ISTANBUL).replace(tzinfo=None)
            gun = an.date()

            bas90 = datetime.combine(seans_baslangici(takvim, gun, V90_SEANS), time())
            bas5 = datetime.combine(seans_baslangici(takvim, gun, V5_SEANS), time())
            v90 = ayri_gun_sayisi(devre[ticker], an, bas90)
            v5 = ayri_gun_sayisi(devre[ticker], an, bas5)
            # Duyuru ertesi seanstan başlıyor ve bir önceki akşam
            # yayınlanıyor; `bas <= gun` koşulu yalnız bilinen tedbiri sayar.
            kademe = aktif_vbts_kademesi(tedbirler[ticker], gun)
            bitis = max(
                (t.bitis for t in tedbirler[ticker]
                 if t.baslangic <= gun <= t.bitis and t.kademe == kademe),
                default=None,
            )
            bayrak = tahta_bayragi(v90=v90, v5=v5, vbts_kademe=kademe).value
            tahta_satir.append((kap_id, v90, v5, bayrak, YONTEM, kademe, bitis))
            gecis[(eski_bayrak, bayrak)] += 1
            kademe_say[kademe] += 1

            # Pencere bildirimin kendisini de içersin: an + 1 sn.
            son = an + timedelta(seconds=1)
            bas12 = an - timedelta(days=365)
            yeni = pencere_sayisi(yeni_is[ticker], son, bas12)
            aciklama = pencere_sayisi(oda[ticker], son, bas12)
            arsiv_gun = min(365, (an - ilk.get(ticker, an)).days)
            siklik_satir.append((kap_id, yeni, aciklama, arsiv_gun))

        print(f"\nbildirim     : {len(bildirimler)}")
        dagilim = Counter(s[3] for s in tahta_satir)
        for ad in ("temiz", "hareketli", "tedbirli"):
            print(f"  {ad:<10}: {dagilim[ad]:>4}  (%{dagilim[ad]/len(tahta_satir)*100:.1f})")
        print(f"  yürürlükte VBTS kademesi: {dict(sorted(kademe_say.items()))}")
        print("\n  vekil → gerçek geçişleri:")
        for (a, b), n in sorted(gecis.items(), key=lambda x: (str(x[0][0]), x[0][1])):
            print(f"    {str(a):<10} → {b:<10} {n:>4}")

        sayilar = [s[1] for s in siklik_satir]
        u1, u2 = ucluk_esikleri(sayilar)
        eski = Counter()
        for s in sayilar:
            eski[siklik_bayragi(s).value] += 1
        kisa = sum(1 for s in siklik_satir if s[3] < 365)
        print(f"\nsıklık (12 ay, point-in-time): medyan {sorted(sayilar)[len(sayilar)//2]}, "
              f"max {max(sayilar)}")
        print(f"  mevcut eşiklerle (8/18): {dict(eski)}")
        print(f"  bildirim ağırlıklı üçlük kesimleri: {u1} / {u2}")
        print(f"  arşiv penceresi 12 aydan kısa (yeni halka arz): {kisa}")

        # Kuru koşuda da diske dökülüyor: analiz_baglam.py bayrağı canlı
        # tabloya yazmadan sınayabilsin.
        with open(CSV_CIKTI, "w", encoding="utf-8", newline="") as f:
            yazici = csv.writer(f)
            yazici.writerow(["kap_id", "dk90", "dk5", "bayrak", "vbts_kademe",
                             "yeni_is_12a", "kap_oda_12a", "arsiv_gun"])
            for t, s in zip(tahta_satir, siklik_satir):
                yazici.writerow([t[0], t[1], t[2], t[3], t[5], s[1], s[2], s[3]])
        print(f"\n{CSV_CIKTI.name} yazıldı.")

        if secenek.kuru:
            print("--kuru: veritabanına yazılmadı.")
            return 0

        with baglanti.cursor() as imlec:
            if secenek.yalniz_siklik:
                tahta_satir = []
            imlec.executemany(
                "insert into public.tahta_durumu "
                "(kap_id, v90, v5, bayrak, yontem, vbts_kademe, vbts_bitis) "
                "values (%s, %s, %s, %s, %s, %s, %s) "
                "on conflict (kap_id) do update set v90 = excluded.v90, "
                "v5 = excluded.v5, bayrak = excluded.bayrak, "
                "yontem = excluded.yontem, vbts_kademe = excluded.vbts_kademe, "
                "vbts_bitis = excluded.vbts_bitis, hesaplandi_at = now()",
                tahta_satir,
            )
            imlec.executemany(
                "insert into public.siklik_durumu "
                "(kap_id, yeni_is_12a, kap_oda_12a, arsiv_gun) "
                "values (%s, %s, %s, %s) "
                "on conflict (kap_id) do update set "
                "yeni_is_12a = excluded.yeni_is_12a, "
                "kap_oda_12a = excluded.kap_oda_12a, "
                "arsiv_gun = excluded.arsiv_gun, hesaplandi_at = now()",
                siklik_satir,
            )
        baglanti.commit()
        print(f"\n{len(tahta_satir)} tahta + {len(siklik_satir)} sıklık satırı yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
