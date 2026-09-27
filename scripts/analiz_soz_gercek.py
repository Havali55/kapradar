"""Söz ve gerçek: tanım varyantları ve seçilen tanımın sonucu.

Kullanım:  python scripts/analiz_soz_gercek.py [--ayrinti]

docs/arastirma/2026-09-27-soz-ve-gercek.md'deki tablo bu betiğin
çıktısı. Girdi: `akis` (yayındaki skorlu bildirimler) + `donem_buyume`
(scripts/ciro_seri_yaz.py). Ağa çıkmaz, LLM yok.

Dört varyant, yalnız D sitede:
  A  Σ ciro oranı,          TMS 29 süzgeci yok   (maket v2)
  B  Σ ciro oranı,          yalnız reel
  C  TL toplamı / FY ciro,  süzgeç yok
  D  TL toplamı / FY ciro,  yalnız reel          (seçilen)
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.soz_gercek import SozSatiri, buyume_donemi_sec, ozetle  # noqa: E402

# Yıl sınırı İstanbul saatiyle: 1 Ocak 01:00'deki bildirim UTC'de önceki yıla düşerdi.
SORGU_DUYURU = """
select ticker, sum(net_tutar_tl), sum(ciro_orani), count(*)
from public.akis
where ciro_orani is not null
  and coalesce(onceki_tur, '') <> 'ayni_is'
  and yayin_zamani >= make_timestamptz(%(yil)s, 1, 1, 0, 0, 0, 'Europe/Istanbul')
  and yayin_zamani <  make_timestamptz(%(yil)s + 1, 1, 1, 0, 0, 0, 'Europe/Istanbul')
group by ticker
"""
SORGU_BUYUME = """
select ticker, donem_sonu, ay_sayisi, hasilat, buyume, reel, para_birimi
from public.donem_buyume
"""

VARYANTLAR = (
    ("A", "Σ ciro oranı, süzgeçsiz", "oran", False),
    ("B", "Σ ciro oranı, yalnız reel", "oran", True),
    ("C", "TL ÷ FY ciro, süzgeçsiz", "tl", False),
    ("D", "TL ÷ FY ciro, yalnız reel (seçilen)", "tl", True),
)


def yuzde(x: float) -> str:
    return f"{x * 100:+.1f}".replace(".", ",")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ayrinti", action="store_true", help="D'nin satırlarını bas")
    secenek = ap.parse_args()

    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(SORGU_BUYUME)
            buyume_satirlari = imlec.fetchall()

            # Dönem seçimi: büyümesi olan şirket sayısı, dönem sonuna göre.
            kapsam_kume: dict[date, set[str]] = defaultdict(set)
            for ticker, sonu, _ay, _h, g, _r, _pb in buyume_satirlari:
                if g is not None:
                    kapsam_kume[sonu].add(ticker)
            donem = buyume_donemi_sec({d: len(t) for d, t in kapsam_kume.items()})
            if donem is None:
                print("büyüme dönemi seçilemedi")
                return 1
            soz_yili = donem.year - 1

            imlec.execute(SORGU_DUYURU, {"yil": soz_yili})
            duyuru = {t: (tl, oran, n) for t, tl, oran, n in imlec.fetchall()}

    # Büyüme dönemindeki satır: şirket başına en uzun kümülatif dönem.
    buyume: dict[str, tuple[float, bool]] = {}
    en_uzun: dict[str, int] = {}
    fy_ciro: dict[str, float] = {}
    for ticker, sonu, ay, hasilat, g, reel, pb in buyume_satirlari:
        if sonu == donem and g is not None and ay > en_uzun.get(ticker, 0):
            en_uzun[ticker] = ay
            buyume[ticker] = (float(g), reel)
        if sonu == date(soz_yili, 12, 31) and ay == 12 and pb == "TL" and hasilat > 0:
            fy_ciro[ticker] = float(hasilat)

    print(f"büyüme dönemi {donem} · söz yılı {soz_yili} · "
          f"söz yılında skorlu işi olan {len(duyuru)} şirket")
    reel_disi = sorted(t for t in duyuru if t in buyume and not buyume[t][1])
    print(f"yeniden ifade etmeyen (nominal) aday: {len(reel_disi)} {reel_disi}")
    print()
    print(f"{'':2}{'varyant':38}{'n':>4}   {'Az':>7}{'Orta':>7}{'Çok':>7}   {'ρ':>6}{'t':>6}")

    secilen = None
    for kod, ad, tur, sadece_reel in VARYANTLAR:
        satirlar = []
        for ticker, (tl, oran, _n) in duyuru.items():
            if ticker not in buyume:
                continue
            g, reel = buyume[ticker]
            if sadece_reel and not reel:
                continue
            if tur == "oran":
                y = float(oran)
            elif ticker in fy_ciro:
                y = float(tl) / fy_ciro[ticker]
            else:
                continue
            satirlar.append(SozSatiri(ticker=ticker, yogunluk=y, buyume=g))
        ozet = ozetle(satirlar)
        if ozet is None:
            print(f"{kod} {ad}: yetersiz satır")
            continue
        m = [yuzde(gr.medyan_buyume) for gr in ozet.gruplar]
        print(f"{kod} {ad:38}{ozet.n:>4}   {m[0]:>7}{m[1]:>7}{m[2]:>7}   "
              f"{ozet.rho:>6.3f}{ozet.t:>6.2f}")
        if kod == "D":
            secilen = ozet

    if secilen is not None:
        print()
        print("D grup medyanı (duyuru/ciro):",
              [f"{gr.medyan_yogunluk:.2f}×" for gr in secilen.gruplar])
        print("D üst grup belirgin önde:", secilen.ust_grup_onde)
        if secenek.ayrinti:
            for gr in secilen.gruplar:
                print(f"\n{gr.ad}")
                for s in gr.satirlar:
                    print(f"  {s.ticker:6} {s.yogunluk:6.2f}×  {yuzde(s.buyume):>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
