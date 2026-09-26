"""Veri seti denetimi — kapının göremediğini ve karar bekleyeni raporlar.

Kullanım:
    python scripts/veri_denetimi.py          # rapor, çıkış kodu 0
    python scripts/veri_denetimi.py --kati   # kapı regresyonu ya da karar
                                             # bekleyen varsa çıkış kodu 1

LLM yok, ağa çıkmaz (yalnız veritabanı). Kontroller ve 2026-09-26'daki
ilk denetimin bulguları: docs/arastirma/2026-09-26-veri-denetimi.md.

  1. Kapı regresyonu: yayındaki (elle olmayan) çıkarımı bugünkü kapı
     reddediyor mu? Kural sıkılaşınca eski satırlar sessizce yayında kalır.
  2. Karar bekleyen: anlam kapısının (B4–B6, A7) elle kuyruğa attığı,
     `data/elle_duzeltmeler.json`'da kararı olmayan bildirimler.
  3. Bağlanmamış tekrar: aynı hisse, aynı skorlu tutar, 365 gün içinde,
     bağ yok. Bayraksız olanlar çoğu zaman ayrı iştir (KAYSE); okunmalı.
  4. Sıklık tutarlılığı: arşivden sayılan 12 aylık bildirim sayısı
     veritabanındakiyle aynı mı (açık pencere hatası 2026-09-26).
  5. Bilinen sapmalar (bilgi): KDV dahil tutar, özette metinde olmayan
     sayı, ciro oranı %50 üstü.
"""

from __future__ import annotations

import argparse
import sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.cikarim import anlam_kapisi, metin_kapisi  # noqa: E402
from kap_radar.degerlendirme import ELLE_MODELI, cikarimi_kur  # noqa: E402
from kap_radar.denetim import kdv_dahil_mi, ozette_metinde_olmayan_sayi  # noqa: E402
from kap_radar.elle import kararlari_oku  # noqa: E402
from kap_radar.skor import MEGA_ORAN, ONEMLI_ORAN, SKORA_GIREN_TIPLER  # noqa: E402

ELLE_DOSYASI = KOK / "data" / "elle_duzeltmeler.json"
# Veritabanındaki bildirimler bu tarihten başlıyor; 12 aylık sayım ancak
# bundan bir yıl sonrası için tam.
DB_BASI = datetime(2024, 9, 1)
ANLAM_KODLARI = ("A7", "B4", "B5", "B6")

SORGU = """
select b.kap_id, b.ticker, b.yayin_zamani, b.ham_metin_tr, b.guncelleme_mi,
       b.duzeltme_mi, b.kap_alanlari->>'karsi_taraf_niteligi',
       c.model, c.veri, c.yayina_hazir, c.red_nedeni, c.ciro_orani,
       exists (select 1 from public.akis a where a.kap_id = b.kap_id),
       g.onceki_kap_id, sd.yeni_is_12a
from public.bildirim b
join lateral (
  select model, veri, yayina_hazir, red_nedeni, ciro_orani
  from public.cikarim c where c.kap_id = b.kap_id order by c.id desc limit 1
) c on true
left join public.bildirim_bag g on g.kap_id = b.kap_id
left join public.siklik_durumu sd on sd.kap_id = b.kap_id
order by b.yayin_zamani
"""


def baslik(metin: str) -> None:
    print(f"\n--- {metin}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kati", action="store_true", help="bulgu varsa çıkış kodu 1")
    ap.add_argument("--liste", type=int, default=10, help="her bölümde en çok kaç satır")
    secenek = ap.parse_args()
    n = secenek.liste

    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(SORGU)
            satirlar = imlec.fetchall()
    kararli = {k.kap_id for k in kararlari_oku(ELLE_DOSYASI)}

    yayinda = [s for s in satirlar if s[12]]
    skorlu = [s for s in yayinda if s[11] is not None]
    print(f"bildirim {len(satirlar)} · yayında {len(yayinda)} · skorlu {len(skorlu)}")

    # 1. kapı regresyonu
    regresyon = []
    for s in yayinda:
        kap_id, ticker, an, metin, _, _, nitelik, model, veri, *_ = s
        if model == ELLE_MODELI:
            continue
        cikarim = cikarimi_kur(veri)
        kapi = metin_kapisi(cikarim, metin or "")
        if kapi.gecti and s[11] is not None:
            kapi = anlam_kapisi(
                [t for t in cikarim.tutarlar if t.tip in SKORA_GIREN_TIPLER],
                metin or "",
                karsi_taraf_niteligi=nitelik,
            )
        if not kapi.gecti:
            regresyon.append(f"{ticker:6}{an.date()} {kap_id} {kapi.red_nedeni}")
    baslik(f"1. kapı regresyonu (yayında ama bugünkü kapıdan geçmiyor): {len(regresyon)}")
    for r in regresyon[:n]:
        print(f"  {r}")

    # 2. elle kuyruk
    kuyruk = [s for s in satirlar if not s[9]]
    nedenler = Counter((s[10] or "?").split(":")[0] for s in kuyruk)
    bekleyen = [
        s for s in kuyruk
        if (s[10] or "").startswith(ANLAM_KODLARI) and s[0] not in kararli
    ]
    baslik(f"2. elle kuyruk: {len(kuyruk)} {dict(sorted(nedenler.items()))} · "
           f"karar bekleyen (A7/B4–B6): {len(bekleyen)}")
    for s in bekleyen[:n]:
        print(f"  {s[1]:6}{s[2].date()} {s[0]} {s[10]}")

    # 3. bağlanmamış tekrar
    hisse = defaultdict(list)
    for s in skorlu:
        veri = s[8] or {}
        kalem = {(Decimal(str(t["deger"])), t["para_birimi"])
                 for t in veri.get("tutarlar") or [] if t["tip"] in SKORA_GIREN_TIPLER}
        hisse[s[1]].append((s[2], s, kalem))
    bayrakli, bayraksiz = [], []
    for liste in hisse.values():
        for i, (an, s, kalem) in enumerate(liste):
            if s[13] is not None:
                continue
            for onceki_an, onceki, onceki_kalem in liste[:i]:
                if an - onceki_an <= timedelta(days=365) and kalem & onceki_kalem:
                    satir = f"{s[1]:6}{onceki_an.date()} -> {an.date()} {s[0]}"
                    (bayrakli if (s[4] or s[5]) else bayraksiz).append(satir)
                    break
    baslik(f"3. bağlanmamış aynı-tutar tekrarı: güncelleme/düzeltme bayraklı "
           f"{len(bayrakli)} · bayraksız {len(bayraksiz)} (çoğu ayrı iş, okunmalı)")
    for r in bayrakli[:n]:
        print(f"  bayraklı  {r}")
    for r in bayraksiz[:n]:
        print(f"  bayraksız {r}")

    # 4. sıklık tutarlılığı
    zaman = defaultdict(list)
    for s in satirlar:
        zaman[s[1]].append(s[2])
    farkli = []
    for s in satirlar:
        an, sayim = s[2], s[14]
        if sayim is None or an.replace(tzinfo=None) < DB_BASI + timedelta(days=366):
            continue
        z = zaman[s[1]]
        db = bisect_right(z, an + timedelta(seconds=1)) - bisect_left(
            z, an - timedelta(days=365)
        )
        if db != sayim:
            farkli.append(f"{s[1]:6}{an.date()} arşiv {sayim} / db {db}")
    baslik(f"4. sıklık: arşiv sayımı veritabanından farklı: {len(farkli)}")
    for r in farkli[:n]:
        print(f"  {r}")

    # 5. bilinen sapmalar
    kdv = kademe_degisen = ozet_sayi = asiri = 0
    for s in skorlu:
        veri, oran = s[8] or {}, Decimal(s[11])
        if any(kdv_dahil_mi(t["alinti"]) for t in veri.get("tutarlar") or []
               if t["tip"] in SKORA_GIREN_TIPLER):
            kdv += 1
            yeni = oran / Decimal("1.2")
            if (oran >= MEGA_ORAN) != (yeni >= MEGA_ORAN) or (
                oran >= ONEMLI_ORAN) != (yeni >= ONEMLI_ORAN):
                kademe_degisen += 1
        if ozette_metinde_olmayan_sayi(veri.get("hap_ozet") or [], s[3] or ""):
            ozet_sayi += 1
        if oran > Decimal("0.5"):
            asiri += 1
    baslik("5. bilinen sapmalar (bilgi)")
    print(f"  KDV dahil tutarlı skorlu bildirim : {kdv} (KDV hariçle kademesi "
          f"değişecek: {kademe_degisen})")
    print(f"  özette metinde olmayan sayı       : {ozet_sayi}")
    print(f"  ciro oranı %50 üstü               : {asiri}")

    bulgu = len(regresyon) + len(bekleyen)
    if secenek.kati and bulgu:
        print(f"\n--kati: {bulgu} bulgu", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
