"""Arşivdeki finansal raporları Postgres'e yükler ve kapsamayı ölçer (Adım 7).

Kullanım:
    python scripts/finansal_yukle.py            # arşiv -> Supabase
    python scripts/finansal_yukle.py --kuru     # yazmadan ne olacağını göster

Ağa çıkmaz; kaynağı `scripts/finansal_cek.py`ın indirdiği arşiv.

Koşunun sonundaki kapsama raporu Adım 7'nin asıl sınavı: 613 bildirimin
kaçında, **o bildirimin yayınlandığı anda** TTM hasılat çözülebiliyor.
Çözülemeyen bildirimde ciro oranı gösterilmez, dolayısıyla skor da
gösterilmez (spec §8) — bu yüzden oran sessizce kabul edilmez, basılır.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.finansal import (  # noqa: E402
    aykiri_indeksler,
    finansal_ayristir,
    ttm_coz,
)

VARSAYILAN_ARSIV = KOK / "data" / "ham"
COMMIT_ARALIGI = 200


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="Finansal raporları yükle")
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    ayristirici.add_argument("--kuru", action="store_true")
    secenek = ayristirici.parse_args()

    arsiv = HamArsiv(secenek.arsiv)
    indeksler = arsiv.finansal_indeksler()
    print(f"arsiv    : {secenek.arsiv} ({len(indeksler)} rapor)")

    donemler = []
    ayristirilamayan = []
    for indeks in indeksler:
        donem = finansal_ayristir(arsiv.finansal_oku(indeks))
        if donem is None or not donem.ticker or donem.yayin_zamani is None:
            ayristirilamayan.append(indeks)
            continue
        donemler.append(donem)

    print(f"ayristi  : {len(donemler)}")
    if ayristirilamayan:
        print(f"AYRISMADI: {len(ayristirilamayan)} -> {ayristirilamayan[:10]}")

    para = Counter(d.para_birimi for d in donemler)
    print(f"para     : {dict(para)}")
    carpan = Counter(str(d.birim_carpani) for d in donemler)
    print(f"birim    : {dict(carpan)}")
    ay = Counter(d.ay_sayisi for d in donemler)
    print(f"donem ayi: {dict(sorted(ay.items()))}")

    donemler, aykiri = aykirilari_ayikla(donemler)
    if aykiri:
        print(f"\nAYKIRI BIRIM BEYANI: {len(aykiri)} rapor yuklenmedi")
        for d in aykiri:
            print(
                f"  {d.kap_index} {d.ticker} {d.donem_sonu} "
                f"birim_carpani={d.birim_carpani} hasilat={d.hasilat:,.0f}"
            )

    if secenek.kuru:
        print("kuru koşu — veritabanına yazılmadı")
        return 0

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        bilinen = set(depo.tickerlar())

        eklenen = mevcut = 0
        yabanci = Counter()
        for sira, donem in enumerate(donemler, start=1):
            if donem.ticker not in bilinen:
                # Şirket satırı yoksa yabancı anahtar düşer. Bildirimi
                # olmayan şirketin hasılatına da ihtiyacımız yok.
                yabanci[donem.ticker] += 1
                continue
            if depo.finansal_kaydet(donem):
                eklenen += 1
            else:
                mevcut += 1
            if sira % COMMIT_ARALIGI == 0:
                baglanti.commit()
        baglanti.commit()

        print("\n--- yukleme ---")
        print(f"eklenen  : {eklenen}")
        print(f"zaten var: {mevcut}")
        if yabanci:
            print(f"sirketi yok: {sum(yabanci.values())} rapor / {len(yabanci)} kod")

        onbellek_tazele(depo, bilinen)
        baglanti.commit()
        kapsama_raporu(baglanti, depo)

    return 0


def aykirilari_ayikla(donemler: list) -> tuple[list, list]:
    """Sunum birimi beyanı şirketin kendi serisiyle çelişen raporları ayırır.

    ONCSM 1559324: şirket her raporunu sade TL sunarken 2025 yıllığında
    sunum birimini '1.000.000 TL' yazmış; rakam ise diğer dönemlerin
    doğal devamı. Beyana uyulsa hasılat bir milyon kat şişer, ciro oranı
    sıfıra iner ve skor sessizce yok olur. Yüklemek yerine bildiriliyor.
    """
    tickera_gore: dict[str, list] = {}
    for d in donemler:
        tickera_gore.setdefault(d.ticker, []).append(d)

    aykiri_kumesi: set[int] = set()
    for kayitlar in tickera_gore.values():
        aykiri_kumesi.update(aykiri_indeksler(kayitlar))

    temiz = [d for d in donemler if d.kap_index not in aykiri_kumesi]
    aykiri = [d for d in donemler if d.kap_index in aykiri_kumesi]
    return temiz, aykiri


def onbellek_tazele(depo: Depo, tickerlar: set[str]) -> None:
    """`sirket` üzerindeki tek satırlık TTM önbelleğini bugüne göre tazeler.

    Sitenin "son yıllık hasılat" alanı burayı okuyor. Skorun paydası
    okumuyor — o point-in-time olmak zorunda (spec §8).
    """
    simdi = datetime.now(timezone.utc)
    dolu = tl_disi = bos = 0

    for ticker in sorted(tickerlar):
        ttm = ttm_coz(depo.donem_hasilatlari(ticker), simdi)
        if ttm is None:
            bos += 1
            continue
        if ttm.para_birimi != "TL":
            # TL'ye çevrim skor anında bildirim tarihli kurla yapılıyor;
            # önbelleğe yanlış tarihli bir çevrim yazmak yanıltıcı olur.
            tl_disi += 1
            continue
        depo.sirket_hasilat_guncelle(
            ticker,
            hasilat_tl=ttm.hasilat,
            donem=f"{ttm.donem_sonu:%Y/%m}",
            kaynak=f"https://www.kap.org.tr/tr/Bildirim/{ttm.kaynak_indeksler[-1]}",
        )
        dolu += 1

    print("\n--- sirket onbellegi ---")
    print(f"dolduruldu: {dolu}")
    print(f"TL disi   : {tl_disi}")
    print(f"TTM yok   : {bos}")


def kapsama_raporu(baglanti, depo: Depo) -> None:
    """Her bildirim için, o andaki TTM çözülebiliyor mu?"""
    with baglanti.cursor() as imlec:
        imlec.execute(
            "select kap_id, ticker, yayin_zamani from public.bildirim "
            "where ticker is not null order by ticker, yayin_zamani"
        )
        bildirimler = imlec.fetchall()

    onbellek: dict[str, list] = {}
    cozulen = Counter()
    eksik_ticker = Counter()

    for _kap_id, ticker, an in bildirimler:
        if ticker not in onbellek:
            onbellek[ticker] = depo.donem_hasilatlari(ticker)
        ttm = ttm_coz(onbellek[ticker], an)
        if ttm is None:
            cozulen["yok"] += 1
            eksik_ticker[ticker] += 1
        else:
            cozulen[ttm.yontem] += 1

    toplam = len(bildirimler)
    basarili = toplam - cozulen["yok"]
    print("\n--- kapsama (point-in-time TTM) ---")
    print(f"bildirim  : {toplam}")
    print(f"cozuldu   : {basarili} (%{100 * basarili / toplam:.1f})")
    print(f"  ytd kop.: {cozulen['ytd_koprusu']}")
    print(f"  yillik  : {cozulen['yillik']}")
    print(f"cozulmedi : {cozulen['yok']}")
    if eksik_ticker:
        print(f"en cok eksik: {eksik_ticker.most_common(10)}")


if __name__ == "__main__":
    raise SystemExit(main())
