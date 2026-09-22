"""Tasfiyedeki fonların hisse pozisyonları ve "kaç günlük hacim" baskısı. Yazmaz.

Kullanım:  python scripts/fon_cek.py && python scripts/fon_hesapla.py

Her rapor ayrıştırılıp kendi 'Hisse Türk' grup toplamıyla doğrulanıyor;
tutmayan rapor toplama GİRMİYOR ve listeleniyor. Baskı ölçüsü:

    gün = krizdeki fonların net TL pozisyonu / kriz öncesi 20 seans ort. TL hacim

Yani "bu pozisyonların tamamı satılsa piyasanın kaç günlük işlemi eder".
Hacim yalnız fiyat_gunluk'taki hisseler için var (bildirim evrenimiz).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.fon import rapor_ayristir  # noqa: E402

FON_KOKU = KOK / "data" / "ham" / "fon"
CIKTI = KOK / "data" / "fon_baski.csv"
KRIZ_ONCESI = date(2026, 9, 8)
HACIM_SEANS = 20


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    secim = json.loads((FON_KOKU / "secim.json").read_text(encoding="utf-8"))

    durum = Counter()
    sirket_durum = Counter()
    net: dict[str, float] = defaultdict(float)
    sahip: dict[str, set] = defaultdict(set)
    tutarsiz = []
    for s in secim:
        pdf = FON_KOKU / "pdf" / f"{s['index']}.pdf"
        if not pdf.exists():
            durum[s["durum"].split(":")[0]] += 1
            sirket_durum[(s["sirket"], s["durum"].split(":")[0])] += 1
            continue
        metin = "\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
        rapor = rapor_ayristir(metin)
        if not rapor.pozisyonlar and rapor.rapor_hisse_toplami is None:
            etiket = "hisse yok"
        elif rapor.tutarli:
            etiket = "tutarlı"
            for kod, tl in rapor.net().items():
                net[kod] += tl
                sahip[kod].add(s["fon"])
        else:
            etiket = "TUTARSIZ"
            tutarsiz.append((s["fon"], s["baslik"][:50], rapor.ayristirilan_toplam,
                             rapor.rapor_hisse_toplami))
        durum[etiket] += 1
        sirket_durum[(s["sirket"], etiket)] += 1

    print(f"rapor: {len(secim)}  →  {dict(durum)}")
    for (sk, et), n in sorted(sirket_durum.items()):
        print(f"  {sk:<7} {et:<10} {n}")
    for t in tutarsiz[:10]:
        print(f"  !! {t[0]} {t[1]} ayrıştırılan {t[2]:,.0f} ≠ rapor {t[3]}")

    toplam = sum(v for v in net.values() if v > 0)
    print(f"\nkrizdeki fonların yurt içi hisse pozisyonu: {toplam / 1e9:,.1f} milyar TL, "
          f"{sum(1 for v in net.values() if v > 0)} hisse")

    with psycopg.connect(dsn_bul(), connect_timeout=30) as b, b.cursor() as c:
        c.execute(
            "select ticker, avg(kapanis_duzeltilmis * hacim) from ("
            "  select ticker, kapanis_duzeltilmis, hacim, row_number() over "
            "    (partition by ticker order by tarih desc) sira "
            "  from fiyat_gunluk where tarih <= %s and hacim > 0) x "
            "where sira <= %s group by ticker",
            (KRIZ_ONCESI, HACIM_SEANS),
        )
        hacim = {t: float(v) for t, v in c.fetchall()}
        c.execute("select distinct ticker from bildirim")
        bizim = {r[0] for r in c.fetchall()}

    satirlar = sorted(
        ((k, v, len(sahip[k]), hacim.get(k)) for k, v in net.items() if v > 0),
        key=lambda x: -x[1],
    )
    print(f"\nEN BÜYÜK 25 POZİSYON (★ = bizim bildirim evrenimizde)")
    print(f"  {'KOD':<7} {'NET TL':>16} {'FON':>4} {'GÜNLÜK HACİM':>14} {'GÜN':>7}")
    for k, v, n, h in satirlar[:25]:
        gun = f"{v / h:7.1f}" if h else "      —"
        yildiz = "★" if k in bizim else " "
        print(f"  {k:<6}{yildiz} {v:>16,.0f} {n:>4} {h or 0:>14,.0f} {gun}")

    ortak = [s for s in satirlar if s[0] in bizim]
    print(f"\nbizim 111 hisseden krizdeki fonlarda bulunan: {len(ortak)}")
    with open(CIKTI, "w", encoding="utf-8") as f:
        f.write("ticker,net_tl,fon_sayisi,ort_tl_hacim_20g,gun\n")
        for k, v, n, h in satirlar:
            f.write(f"{k},{v:.0f},{n},{h or ''},{v / h if h else ''}\n")
    print(f"{CIKTI.name} yazıldı. Veritabanına hiçbir şey yazılmadı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
