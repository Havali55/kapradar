"""Güncelleme ve düzeltme bildirimlerini önceki bildirime bağlar.

Kullanım:
    python scripts/bag_kur.py --kuru    # yalnız özet
    python scripts/bag_kur.py           # bildirim_bag'i baştan yazar

Kural `src/kap_radar/bag.py`'de. Tablo türetilmiş: her koşu silip
yeniden yazar, çünkü yeni bir çıkarım ya da elle karar eski bağın
türünü değiştirebilir (skorsuza dönen ihale bildirimi artık "aynı iş"
değildir). Ağa çıkmaz, LLM yok.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.bag import BagGirdisi, baglari_kur  # noqa: E402
from kap_radar.cikarim import sayilari_bul  # noqa: E402
from kap_radar.skor import SKORA_GIREN_TIPLER  # noqa: E402

ISTANBUL = ZoneInfo("Europe/Istanbul")
# Ortaklık için yıl, adet, gün gibi küçük sayılar sayılmaz.
ASGARI_SAYI = Decimal("10000")

SORGU = """
select b.kap_id, b.ticker, b.yayin_zamani, b.guncelleme_mi, b.duzeltme_mi,
       b.onceki_aciklama_tarihleri, b.ham_metin_tr,
       c.veri, c.yayina_hazir, c.ciro_orani
from public.bildirim b
left join lateral (
  select veri, yayina_hazir, ciro_orani from public.cikarim c
  where c.kap_id = b.kap_id order by c.id desc limit 1
) c on true
"""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kuru", action="store_true", help="yazma")
    secenek = ap.parse_args()

    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(SORGU)
            satirlar = imlec.fetchall()

        girdiler = []
        ticker_ve_an = {}
        for (kap_id, ticker, yayin, guncelleme, duzeltme, onceki, metin,
             veri, hazir, oran) in satirlar:
            # "Zaten sayıldı" yalnız sitede sayılan kalem için doğru:
            # yayında ve skorlu çıkarımın skora giren kalemleri.
            kalemler = frozenset(
                (Decimal(str(t["deger"])), t["para_birimi"])
                for t in ((veri or {}).get("tutarlar") or [])
                if hazir and oran is not None and t["tip"] in SKORA_GIREN_TIPLER
            )
            an = yayin.astimezone(ISTANBUL).replace(tzinfo=None)
            ticker_ve_an[kap_id] = (ticker, an)
            girdiler.append(
                BagGirdisi(
                    kap_id=kap_id,
                    ticker=ticker,
                    an=an,
                    guncelleme_mi=bool(guncelleme),
                    duzeltme_mi=bool(duzeltme),
                    onceki_tarihler=tuple(onceki or ()),
                    kalemler=kalemler,
                    metin_sayilari=frozenset(
                        s for s in sayilari_bul(metin or "") if s >= ASGARI_SAYI
                    ),
                )
            )

        baglar = baglari_kur(girdiler)
        bayrakli = sum(1 for g in girdiler if g.guncelleme_mi or g.duzeltme_mi)
        print(f"bildirim            : {len(girdiler)}")
        print(f"güncelleme/düzeltme : {bayrakli}")
        print(f"bağlanan            : {len(baglar)}")
        for (tur, yontem), n in sorted(Counter((b.tur, b.yontem) for b in baglar).items()):
            print(f"  {tur:<10} {yontem:<9} {n:>4}")
        for b in baglar:
            if b.tur in ("duzeltme", "ayni_is"):
                ticker, an = ticker_ve_an[b.kap_id]
                _, onceki_an = ticker_ve_an[b.onceki_kap_id]
                print(f"    {b.tur:<9} {ticker:6} {onceki_an:%Y-%m-%d} -> {an:%Y-%m-%d}")

        if secenek.kuru:
            print("--kuru: veritabanına yazılmadı.")
            return 0

        with baglanti.cursor() as imlec:
            imlec.execute("delete from public.bildirim_bag")
            imlec.executemany(
                "insert into public.bildirim_bag (kap_id, onceki_kap_id, tur, yontem) "
                "values (%s, %s, %s, %s)",
                [(b.kap_id, b.onceki_kap_id, b.tur, b.yontem) for b in baglar],
            )
        baglanti.commit()
        print(f"{len(baglar)} bağ yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
