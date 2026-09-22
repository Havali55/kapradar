"""Bildirim anındaki tahta kalitesini hesaplar (Modül B) — Adım 17.

**YERİNİ `baglam_hesapla.py` ALDI (2026-09-22).** Bu betik limit yakını
gün VEKİLİ kullanıyor; tahta artık Borsa İstanbul'un kendi devre kesici
ve VBTS kayıtlarından hesaplanıyor. Karşılaştırma için duruyor ve
varsayılan olarak yazmıyor — `--vekil-yaz` verilmeden gerçek veriyi
ezmez.

Neden var: Adım 16b'de ölçüldü ki skorun piyasa ilgisiyle ilişkisi
TEMİZ tahtalarda var (+0,083), spekülatif tahtalarda yok (−0,039).
Tahta bayrağı bu yüzden yanında duran bir süs değil, Modül C'nin
gösterilip gösterilmeyeceğini belirleyen geçerlilik koşulu.

VBTS verisi henüz çekilmedi (Adım 11). Vekil ölçü: BIST günlük limiti
±%10 olduğundan |günlük getiri| >= %9 olan gün "limit yakını" sayılır.
Eşikler ve karar sırası `skor.tahta_bayragi` ile aynı — ikinci bir
kopya yazılmadı ki biri düzeltilip diğeri unutulmasın.

    python scripts/tahta_hesapla.py            # hesapla ve yaz
    python scripts/tahta_hesapla.py --kuru     # yalnız dağılımı bas
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.skor import tahta_bayragi  # noqa: E402

# BIST günlük limit ±%10; %9 eşiği limit yakını hareketi yakalar.
LIMIT_ESIGI = 0.09
# Bedelsiz kaynaklı sahte sıçramalar — auto_adjust BIST bedelsizlerini
# düzeltmiyor (HRKET 87,9 -> 6,15). Elenmezse her bedelsiz bir "limit
# günü" sayılır ve temiz tahtalar tedbirli görünür.
AZAMI_GUNLUK_GETIRI = 0.40

V90_GUN, V5_GUN = 90, 5
ASGARI_GECMIS = 30


SORGU_BILDIRIM = """
select b.kap_id, b.ticker, coalesce(t.t0, b.yayin_zamani::date) as t0
from public.bildirim b
left join public.tepki t on t.kap_id = b.kap_id
order by b.yayin_zamani
"""

SORGU_FIYAT = """
select ticker, tarih, kapanis_duzeltilmis
from public.fiyat_gunluk
where kapanis_duzeltilmis is not null
order by ticker, tarih
"""

SORGU_TAKVIM = "select tarih from public.endeks_gunluk order by tarih"


def getiri_serileri(satirlar) -> dict[str, dict]:
    """ticker -> {tarih: günlük getiri}. Sıçramalar burada eleniyor."""
    seri: dict[str, dict] = {}
    onceki: dict[str, tuple] = {}
    for ticker, tarih, kapanis in satirlar:
        kapanis = float(kapanis)
        if ticker in onceki:
            _, onceki_kapanis = onceki[ticker]
            if onceki_kapanis > 0:
                g = kapanis / onceki_kapanis - 1.0
                if abs(g) < AZAMI_GUNLUK_GETIRI:
                    seri.setdefault(ticker, {})[tarih] = g
        onceki[ticker] = (tarih, kapanis)
    return seri


def say(getiriler: dict, takvim: list, i0: int, gun: int) -> int | None:
    """t0'dan önceki `gun` seansta kaç limit yakını hareket var."""
    pencere = [takvim[j] for j in range(max(0, i0 - gun), i0)]
    gorulen = [getiriler[t] for t in pencere if t in getiriler]
    if len(gorulen) < min(ASGARI_GECMIS, gun):
        return None
    return sum(1 for g in gorulen if abs(g) >= LIMIT_ESIGI)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Tahta kalitesi hesabı")
    ap.add_argument("--kuru", action="store_true", help="yazma, yalnız dağılım")
    ap.add_argument(
        "--vekil-yaz",
        action="store_true",
        help="gerçek veriyi vekille EZ (yalnız bilerek)",
    )
    secenek = ap.parse_args()

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(SORGU_TAKVIM)
            takvim = [r[0] for r in imlec.fetchall()]
            imlec.execute(SORGU_FIYAT)
            getiri = getiri_serileri(imlec.fetchall())
            imlec.execute(SORGU_BILDIRIM)
            bildirimler = imlec.fetchall()

        ix = {g: i for i, g in enumerate(takvim)}
        dagilim: Counter = Counter()
        atlanan = 0
        satirlar = []

        for kap_id, ticker, t0 in bildirimler:
            if ticker not in getiri or t0 not in ix:
                atlanan += 1
                continue
            i0 = ix[t0]
            v90 = say(getiri[ticker], takvim, i0, V90_GUN)
            v5 = say(getiri[ticker], takvim, i0, V5_GUN)
            if v90 is None:
                atlanan += 1
                continue
            bayrak = tahta_bayragi(v90=v90, v5=v5 or 0)
            dagilim[bayrak.value] += 1
            satirlar.append((kap_id, v90, v5 or 0, bayrak.value))

        toplam = sum(dagilim.values())
        print(f"  hesaplanan : {toplam}")
        print(f"  atlanan    : {atlanan}  (yetersiz fiyat geçmişi)")
        for ad in ("temiz", "hareketli", "tedbirli"):
            n = dagilim[ad]
            print(f"  {ad:<10} : {n:>3}  (%{n/toplam*100:.1f})" if toplam else ad)

        if secenek.kuru or not secenek.vekil_yaz:
            print("\n  Yazılmadı (vekil; gerçek veri için baglam_hesapla.py).")
            return 0

        with baglanti.cursor() as imlec:
            imlec.executemany(
                "insert into public.tahta_durumu (kap_id, v90, v5, bayrak) "
                "values (%s, %s, %s, %s) "
                "on conflict (kap_id) do update set "
                "v90 = excluded.v90, v5 = excluded.v5, "
                "bayrak = excluded.bayrak, hesaplandi_at = now()",
                satirlar,
            )
        baglanti.commit()
        print(f"\n  {len(satirlar)} satır yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
