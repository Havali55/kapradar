"""Point-in-time ciro basamaklarını ve dönem büyümelerini yazar.

Kullanım:
    python scripts/ciro_seri_yaz.py --kuru   # yalnız özet
    python scripts/ciro_seri_yaz.py          # ttm_seri ve donem_buyume'yi baştan yazar

Kurallar `src/kap_radar/finansal.py`'de (`ttm_basamaklari`,
`donem_buyumeleri`); burada yalnız okuma ve yazma var. Tablolar
türetilmiş: her koşu silip yeniden yazar, çünkü geç gelen bir rapor ya
da revizyon geçmiş basamakları değiştirebilir. Ağa çıkmaz, LLM yok.
Site bu tabloları `ciro_seri` ve `reel_buyume` görünümlerinden okur.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.finansal import donem_buyumeleri, ttm_basamaklari  # noqa: E402

BASAMAK_EKLE = """
insert into public.ttm_seri (ticker, gecerlilik_basi, hasilat, donem_sonu,
  para_birimi, yontem, enflasyon_carpani, kaynak_kap_index)
values (%s, %s, %s, %s, %s, %s, %s, %s)
"""
BUYUME_EKLE = """
insert into public.donem_buyume (ticker, kap_index, donem_sonu, ay_sayisi,
  yayin_zamani, hasilat, onceki_yil_hasilat, para_birimi, buyume, katsayi, reel)
values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
# Özet satırında "en yeni dönem" sayılmak için gereken asgari şirket
# sayısı; tek şirketin özel hesap dönemi (Temmuz sonu) seçilmesin.
OZET_ASGARI = 10


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kuru", action="store_true", help="yazma")
    secenek = ap.parse_args()

    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        depo = Depo(baglanti)
        basamaklar: list[tuple] = []
        buyumeler: list[tuple] = []
        for ticker in depo.tickerlar():
            donemler = depo.donem_hasilatlari(ticker)
            for b in ttm_basamaklari(donemler):
                t = b.ttm
                if t is None:
                    basamaklar.append(
                        (ticker, b.gecerlilik_basi, None, None, None, None, None, None)
                    )
                else:
                    basamaklar.append(
                        (ticker, b.gecerlilik_basi, t.hasilat, t.donem_sonu,
                         t.para_birimi, t.yontem, t.enflasyon_carpani,
                         t.kaynak_indeksler[-1])
                    )
            for g in donem_buyumeleri(donemler):
                buyumeler.append(
                    (g.ticker, g.kap_index, g.donem_sonu, g.ay_sayisi,
                     g.yayin_zamani, g.hasilat, g.onceki_yil_hasilat,
                     g.para_birimi, g.buyume, g.katsayi, g.reel)
                )

        buyumeli = [g for g in buyumeler if g[8] is not None]
        print(f"şirket (serisi olan) : {len({s[0] for s in basamaklar})}")
        print(f"ciro basamağı        : {len(basamaklar)} "
              f"({sum(1 for s in basamaklar if s[2] is None)} boşluk)")
        print(f"dönem                : {len(buyumeler)} "
              f"({len(buyumeli)} büyümeli, {sum(1 for g in buyumeler if g[10])} reel)")
        sayim = Counter(g[2] for g in buyumeli)
        son = max((d for d, n in sayim.items() if n >= OZET_ASGARI), default=None)
        if son is not None:
            dagilim = Counter(
                "reel" if g[10] else ("k=1" if g[9] == 1 else "k yok/aralık dışı")
                for g in buyumeli
                if g[2] == son
            )
            print(f"en yeni dönem {son}: {dict(dagilim)}")

        if secenek.kuru:
            print("--kuru: veritabanına yazılmadı.")
            return 0

        with baglanti.cursor() as imlec:
            imlec.execute("delete from public.ttm_seri")
            imlec.executemany(BASAMAK_EKLE, basamaklar)
            imlec.execute("delete from public.donem_buyume")
            imlec.executemany(BUYUME_EKLE, buyumeler)
        baglanti.commit()
        print(f"{len(basamaklar)} basamak, {len(buyumeler)} dönem yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
