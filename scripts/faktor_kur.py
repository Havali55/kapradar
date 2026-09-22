"""BIST eşit ağırlıklı getiri serisi — küçük hisse faktörünün hammaddesi.

Kullanım:
    python scripts/faktor_kur.py            # indir (arşivde yoksa) + özet bas
    python scripts/faktor_kur.py --yaz      # faktor_gunluk tablosuna da yaz

Neden: 8–18 Eylül 2026'da XU100 −%7,8 düşerken bizim 111 hissemizin
medyanı −%19,8 düştü; "temiz" tahtalar dahil. XU100 büyük hisse endeksi,
fon tasfiyesi gibi küçük hisselere özgü ortak şoku görmüyor ve piyasa
modeli bu şoku bildirime "tepki" diye yazıyor. yfinance'te küçük hisse
endeksi (XTUMY, XUTUM) yok; bu yüzden kendimiz kuruyoruz.

Evren: KAP arşivinde pay bazında devre kesici görmüş ya da özel durum
açıklaması yapmış her pay kodu (~600). Günlük getiri kesitsel ORTALAMA;
|getiri| ≥ %50 olan gün (düzeltilmemiş bedelsiz) o hisse için atılıyor.
Ham kapanışlar data/ham/evren/ altında; veritabanına yalnız seri gider.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from datetime import date
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

LISTE_KLASORU = KOK / "data" / "ham" / "liste"
EVREN_KLASORU = KOK / "data" / "ham" / "evren"
KAPANIS_CSV = EVREN_KLASORU / "kapanis.csv"
BASLANGIC = "2024-06-01"
PARCA = 40
SICRAMA = 0.50
ASGARI_HISSE = 100  # o gün bu kadar hisse yoksa seri yazılmaz

_KOD = re.compile(r"^[A-Z][A-Z0-9]{2,5}$")


def evren() -> list[str]:
    kodlar: set[str] = set()
    for dosya in LISTE_KLASORU.glob("*.json"):
        for k in json.loads(dosya.read_text(encoding="utf-8")):
            if k.get("subject") == "Pay Bazında Devre Kesici Bildirimi":
                kaynak = k.get("relatedStocks")
            elif k.get("disclosureClass") == "ODA":
                kaynak = k.get("stockCodes")
            else:
                continue
            for kod in (kaynak or "").split(","):
                kod = kod.strip()
                if _KOD.match(kod):
                    kodlar.add(kod)
    return sorted(kodlar)


def indir(kodlar: list[str], bitis: str) -> pd.DataFrame:
    import yfinance as yf

    parcalar = []
    for i in range(0, len(kodlar), PARCA):
        semboller = [f"{k}.IS" for k in kodlar[i : i + PARCA]]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            veri = yf.download(
                semboller, start=BASLANGIC, end=bitis, auto_adjust=True,
                progress=False, threads=True,
            )
        kapanis = veri["Close"] if "Close" in veri else veri
        kapanis.columns = [str(c).removesuffix(".IS") for c in kapanis.columns]
        parcalar.append(kapanis)
        print(f"  {min(i + PARCA, len(kodlar))}/{len(kodlar)}", flush=True)
    return pd.concat(parcalar, axis=1)


def ew_seri(kapanis: pd.DataFrame) -> pd.DataFrame:
    getiri = kapanis.sort_index().pct_change(fill_method=None)
    getiri = getiri.where(getiri.abs() < SICRAMA)
    return pd.DataFrame({
        "ew_getiri": getiri.mean(axis=1, skipna=True),
        "n_hisse": getiri.notna().sum(axis=1),
    }).iloc[1:]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yaz", action="store_true")
    secenek = ap.parse_args()

    EVREN_KLASORU.mkdir(parents=True, exist_ok=True)
    if KAPANIS_CSV.exists():
        kapanis = pd.read_csv(KAPANIS_CSV, index_col=0, parse_dates=True)
    else:
        kodlar = evren()
        print(f"evren: {len(kodlar)} pay kodu", flush=True)
        kapanis = indir(kodlar, date.today().isoformat())
        kapanis = kapanis.dropna(axis=1, how="all")
        kapanis.to_csv(KAPANIS_CSV)
    print(f"fiyatı gelen hisse: {kapanis.shape[1]}, gün: {kapanis.shape[0]}")

    seri = ew_seri(kapanis)
    seri = seri[seri["n_hisse"] >= ASGARI_HISSE]
    print(f"seri: {len(seri)} gün, medyan hisse/gün {int(seri['n_hisse'].median())}")
    eyl = seri.loc["2026-09-08":"2026-09-18", "ew_getiri"]
    print(f"8–18 Eylül birikimli (ertesi günden): %{((1 + eyl.iloc[1:]).prod() - 1) * 100:+.1f}")

    if not secenek.yaz:
        print("--yaz verilmedi, veritabanına yazılmadı.")
        return 0

    import psycopg

    from kap_radar.ayarlar import dsn_bul

    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.executemany(
                "insert into public.faktor_gunluk (tarih, ew_getiri, n_hisse) "
                "values (%s, %s, %s) on conflict (tarih) do update set "
                "ew_getiri = excluded.ew_getiri, n_hisse = excluded.n_hisse",
                [(t.date(), float(r.ew_getiri), int(r.n_hisse))
                 for t, r in seri.iterrows()],
            )
        baglanti.commit()
    print(f"{len(seri)} gün yazıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
