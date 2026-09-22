"""Fon raporlarını ayrıştırır, yazar ve bağlam tablolarını hesaplar (F2).

Kullanım:  python scripts/fon_yukle.py [--kuru]

Girdi: data/ham/fon/pdf/{index}.pdf (ya da .muaf) + data/ham/fon/liste/.
Her PDF bir kez ayrıştırılır, sonuç yanına {index}.json olarak yazılır.

Yazdıkları:
  fon_raporu, fon_pozisyon  — ham ama doğrulanmış pozisyonlar
  fon_baglam                — bildirim anında (point-in-time)
  hisse_fon_guncel          — bugün (hisse sayfası)

Point-in-time kuralı: bir bildirim için her fonun bildirimden ÖNCE
yayınlanmış son raporu, en fazla GUNCELLIK gün eski. Tasfiye tutarı yalnız
karar tarihinden sonraki bildirimlerde sayılır.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.fon import portfoy_sirketi, rapor_ayristir  # noqa: E402

ISTANBUL = ZoneInfo("Europe/Istanbul")
FON_KOKU = KOK / "data" / "ham" / "fon"
PDF = FON_KOKU / "pdf"
GUNCELLIK = timedelta(days=70)
HACIM_SEANS = 20


def liste_kunyesi() -> dict[int, dict]:
    kunye = {}
    for dosya in (FON_KOKU / "liste").glob("*.json"):
        for k in json.loads(dosya.read_text(encoding="utf-8")):
            if k.get("subject") == "Portföy Dağılım Raporu":
                kunye[k["disclosureIndex"]] = k
    return kunye


def ayristir(indeks: int) -> dict | None:
    """PDF → önbellekli sonuç; PDF yoksa .muaf'a bakar."""
    onbellek = PDF / f"{indeks}.json"
    if onbellek.exists():
        return json.loads(onbellek.read_text(encoding="utf-8"))
    if (PDF / f"{indeks}.muaf").exists():
        sonuc = {"durum": "muaf", "donem": None, "toplam": None, "net": {}}
    elif (PDF / f"{indeks}.pdf").exists():
        try:
            metin = "\n".join(
                p.extract_text() or "" for p in PdfReader(PDF / f"{indeks}.pdf").pages
            )
        except Exception:
            return None
        r = rapor_ayristir(metin)
        if not r.pozisyonlar and r.rapor_hisse_toplami is None:
            durum = "hisse_yok"
        else:
            durum = "tutarli" if r.tutarli else "tutarsiz"
        sonuc = {"durum": durum, "donem": r.donem, "toplam": r.rapor_hisse_toplami,
                 "net": r.net() if durum == "tutarli" else {}}
    else:
        return None
    onbellek.write_text(json.dumps(sonuc, ensure_ascii=False), encoding="utf-8")
    return sonuc


def baglam_hesapla(an, pozisyonlar, raporlar_fon, tasfiye):
    """Bir hisse için `an` anındaki fon durumu.

    pozisyonlar: [(fon, yayin, net_tl, sirket)] — yalnız tutarlı raporlar
    raporlar_fon: fon → sıralı [(yayin, indeks)] — o fonun tüm raporları
    """
    son: dict[str, tuple] = {}
    for fon, yayin, net, sirket in pozisyonlar:
        if an - GUNCELLIK <= yayin < an and (fon not in son or yayin > son[fon][0]):
            son[fon] = (yayin, net, sirket)
    # Fonun daha yeni bir raporu var ama bu hisse onda yoksa pozisyon kapanmış.
    son = {
        f: v for f, v in son.items()
        if not any(v[0] < y < an for y, _ in raporlar_fon.get(f, []))
    }
    son = {f: v for f, v in son.items() if v[1] > 0}
    if not son:
        return None
    toplam = sum(v[1] for v in son.values())
    sirket_tl: dict[str, float] = defaultdict(float)
    for _, net, sirket in son.values():
        sirket_tl[sirket or "?"] += net
    tasfiye_fonlar = [
        v for v in son.values()
        if v[2] in tasfiye and tasfiye[v[2]] <= an.date()
    ]
    return {
        "fon_sayisi": len(son),
        "fon_tl": toplam,
        "sirket_sayisi": len(sirket_tl),
        "en_buyuk_pay": max(sirket_tl.values()) / toplam,
        "tasfiye_tl": sum(v[1] for v in tasfiye_fonlar),
        "tasfiye_fon": len(tasfiye_fonlar),
        "sirketler": set(sirket_tl),
        "donem": max(v[0] for v in son.values()),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kuru", action="store_true")
    secenek = ap.parse_args()

    kunye = liste_kunyesi()
    raporlar = []
    sayac = defaultdict(int)
    for dosya in sorted(PDF.glob("*")):
        if dosya.suffix not in (".pdf", ".muaf"):
            continue
        indeks = int(dosya.stem)
        k = kunye.get(indeks)
        sonuc = ayristir(indeks) if k else None
        if sonuc is None:
            continue
        sayac[sonuc["durum"]] += 1
        yayin = datetime.strptime(k["publishDate"], "%d.%m.%Y %H:%M:%S").replace(
            tzinfo=ISTANBUL)
        raporlar.append({
            "indeks": indeks, "fon": k.get("fundCode") or k["kapTitle"],
            "ad": k["kapTitle"], "sirket": portfoy_sirketi(k["kapTitle"]),
            "yayin": yayin, **sonuc,
        })
    print(f"rapor: {len(raporlar)}  {dict(sayac)}")

    raporlar_fon: dict[str, list] = defaultdict(list)
    ticker_poz: dict[str, list] = defaultdict(list)
    for r in raporlar:
        if r["durum"] in ("tutarli", "hisse_yok"):
            raporlar_fon[r["fon"]].append((r["yayin"], r["indeks"]))
        for t, net in r["net"].items():
            ticker_poz[t].append((r["fon"], r["yayin"], net, r["sirket"]))
    son_muaf = {}
    for r in sorted(raporlar, key=lambda r: r["yayin"]):
        son_muaf[r["fon"]] = (r["durum"] == "muaf", r["sirket"])

    with psycopg.connect(dsn_bul(), connect_timeout=30) as b:
        with b.cursor() as c:
            c.execute("select portfoy_sirketi, karar_tarihi from tasfiye_kurulus")
            tasfiye = dict(c.fetchall())
            c.execute("select kap_id, ticker, yayin_zamani from bildirim")
            bildirimler = c.fetchall()
            c.execute("select ticker, tarih, kapanis_duzeltilmis * hacim from fiyat_gunluk "
                      "where hacim > 0 order by ticker, tarih")
            hacim_seri: dict[str, list] = defaultdict(list)
            for t, g, v in c.fetchall():
                hacim_seri[t].append((g, float(v)))

        def ort_hacim(ticker, an):
            s = [v for g, v in hacim_seri.get(ticker, []) if g < an.date()][-HACIM_SEANS:]
            return sum(s) / len(s) if len(s) >= 10 else None

        baglam_satir = []
        for kap_id, ticker, yayin in bildirimler:
            bg = baglam_hesapla(yayin, ticker_poz.get(ticker, []), raporlar_fon, tasfiye)
            if bg:
                baglam_satir.append((kap_id, bg["fon_sayisi"], bg["fon_tl"], bg["sirket_sayisi"],
                                     bg["en_buyuk_pay"], bg["tasfiye_tl"], ort_hacim(ticker, yayin)))

        simdi = datetime.now(ISTANBUL)
        guncel_satir = []
        for ticker, poz in ticker_poz.items():
            bg = baglam_hesapla(simdi, poz, raporlar_fon, tasfiye)
            if not bg:
                continue
            once = baglam_hesapla(simdi - timedelta(days=91), poz, raporlar_fon, tasfiye)
            muaf = sum(1 for m, s in son_muaf.values() if m and s in bg["sirketler"])
            guncel_satir.append((
                ticker, bg["fon_sayisi"], bg["fon_tl"], bg["sirket_sayisi"], bg["en_buyuk_pay"],
                bg["tasfiye_tl"], bg["tasfiye_fon"], ort_hacim(ticker, simdi),
                once["fon_tl"] if once else None, bg["donem"].strftime("%Y-%m"), muaf,
            ))

        print(f"fon_baglam: {len(baglam_satir)} / {len(bildirimler)} bildirimde fon pozisyonu var")
        print(f"hisse_fon_guncel: {len(guncel_satir)} hisse · tasfiye baskısı olan "
              f"{sum(1 for s in guncel_satir if s[5] > 0)}")
        for s in sorted(guncel_satir, key=lambda s: -s[5])[:8]:
            gun = f"{s[5] / s[7]:.1f} gün" if s[7] else "hacim yok"
            print(f"  {s[0]:<6} fon {s[2] / 1e9:6.1f} mr · tasfiyede {s[5] / 1e9:6.1f} mr · {gun}")
        if secenek.kuru:
            print("--kuru: yazılmadı.")
            return 0

        with b.cursor() as c:
            c.executemany(
                "insert into fon_raporu (kap_index, fon_kodu, fon_adi, portfoy_sirketi, donem, "
                "yayin_zamani, durum, hisse_toplam_tl) values (%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict (kap_index) do update set durum = excluded.durum, "
                "donem = excluded.donem, hisse_toplam_tl = excluded.hisse_toplam_tl",
                [(r["indeks"], r["fon"], r["ad"], r["sirket"], r["donem"], r["yayin"],
                  r["durum"], r["toplam"]) for r in raporlar],
            )
            c.execute("delete from fon_pozisyon")
            c.executemany(
                "insert into fon_pozisyon (kap_index, ticker, net_tl) values (%s,%s,%s)",
                [(r["indeks"], t, n) for r in raporlar for t, n in r["net"].items()],
            )
            c.execute("delete from fon_baglam")
            c.executemany(
                "insert into fon_baglam (kap_id, fon_sayisi, fon_tl, portfoy_sirketi_sayisi, "
                "en_buyuk_pay, tasfiye_tl, gunluk_hacim_tl) values (%s,%s,%s,%s,%s,%s,%s)",
                baglam_satir,
            )
            c.execute("delete from hisse_fon_guncel")
            c.executemany(
                "insert into hisse_fon_guncel (ticker, fon_sayisi, fon_tl, "
                "portfoy_sirketi_sayisi, en_buyuk_pay, tasfiye_tl, tasfiye_fon_sayisi, "
                "gunluk_hacim_tl, fon_tl_3ay_once, son_rapor_donemi, muaf_fon_sayisi) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                guncel_satir,
            )
        b.commit()
    print("yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
