"""BIST kapanış serilerini ve XU100'ü çekip veritabanına yazar (Adım 6).

Kullanım:
    python scripts/fiyat_cek.py                    # bildirim aralığı + tampon
    python scripts/fiyat_cek.py --ticker ORGE      # tek hisse
    python scripts/fiyat_cek.py --baslangic 2025-09-01 --bitis 2026-09-18

Maliyet sıfır. Aralık varsayılanı bildirimlerin kapsadığı dönem artı
tampon: CAR penceresi t0'dan sonra üç işlem günü istiyor, getiri hesabı
da t0'dan **önceki** kapanışı istiyor. Tampon olmazsa ilk ve son
bildirimlerin tepkisi hesaplanamaz.

yfinance resmî kaynak değil (spec §13, risk 4): her seri tutarlılık
kontrolünden geçiyor. Uyarı veren gün **yine de yazılıyor** — %50'lik bir
düşüş düzeltilmemiş bir sermaye işlemi de olabilir, gerçek bir çöküş de.
Veriyi sessizce atmak ikincisini siler; karar insana bırakılıyor, uyarılar
koşu çıktısında listeleniyor.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.depo import Depo  # noqa: E402
from kap_radar.fiyat import (  # noqa: E402
    XU100_SEMBOLU,
    seri_cek,
    seri_dogrula,
    yf_sembolu,
)

KONTROL_NOKTASI = "fiyat_cekim"

# Tepki penceresi için her iki uçta bırakılan takvim günü tamponu.
TAMPON_GUN = 15


def env_oku(yol: Path) -> dict[str, str]:
    if not yol.exists():
        return {}
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def tarih_coz(metin: str) -> date:
    return datetime.strptime(metin, "%Y-%m-%d").date()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="BIST fiyat batch")
    ayristirici.add_argument("--baslangic", type=tarih_coz)
    ayristirici.add_argument("--bitis", type=tarih_coz)
    ayristirici.add_argument("--ticker", action="append", dest="tickerlar")
    ayristirici.add_argument("--endeks-atla", action="store_true")
    secenek = ayristirici.parse_args()

    dsn = env_oku(KOK / ".env").get("DATABASE_URL", "")
    if not dsn or "<PAROLA>" in dsn:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor.", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute(
                "select min(yayin_zamani)::date, max(yayin_zamani)::date "
                "from public.bildirim"
            )
            ilk, son = imlec.fetchone()
            tickerlar = secenek.tickerlar
            if not tickerlar:
                imlec.execute(
                    "select distinct ticker from public.bildirim "
                    "where ticker is not null order by 1"
                )
                tickerlar = [satir[0] for satir in imlec.fetchall()]

        if ilk is None and not (secenek.baslangic and secenek.bitis):
            print("Veritabanında bildirim yok; --baslangic/--bitis verin.", file=sys.stderr)
            return 1

        baslangic = secenek.baslangic or ilk - timedelta(days=TAMPON_GUN)
        bitis = secenek.bitis or min(son + timedelta(days=TAMPON_GUN), date.today())

        print(f"aralik   : {baslangic} — {bitis}")
        print(f"hisse    : {len(tickerlar)}\n", flush=True)

        toplam_satir = uyari_sayisi = bos_seri = 0

        if not secenek.endeks_atla:
            endeks = seri_cek(XU100_SEMBOLU, baslangic, bitis)
            uyarilar = seri_dogrula(endeks)
            for uyari in uyarilar:
                print(f"  UYARI {uyari}", flush=True)
            uyari_sayisi += len(uyarilar)
            eklenen = depo.endeks_kaydet(endeks.kapanislar)
            baglanti.commit()
            print(f"XU100: {len(endeks.kapanislar)} gün, {eklenen} yeni\n", flush=True)

        for sira, ticker in enumerate(tickerlar, start=1):
            seri = seri_cek(yf_sembolu(ticker), baslangic, bitis)
            if not seri.kapanislar:
                # Ticker değişmiş ya da pay işlem görmüyor olabilir;
                # sessiz geçmek yerine sayılıyor.
                bos_seri += 1
                print(f"  {ticker}: seri boş", flush=True)
                continue

            uyarilar = seri_dogrula(seri)
            for uyari in uyarilar:
                print(f"  UYARI {uyari}", flush=True)
            uyari_sayisi += len(uyarilar)

            toplam_satir += depo.fiyat_kaydet(ticker, seri.kapanislar, seri.hacimler)
            if sira % 20 == 0:
                baglanti.commit()
                print(f"  {sira}/{len(tickerlar)} hisse", flush=True)

        depo.kontrol_noktasi_yaz(
            KONTROL_NOKTASI,
            son_islenen_tarih=bitis,
            notlar={"hisse": len(tickerlar), "satir": toplam_satir},
        )
        baglanti.commit()

    print("\n--- ozet ---")
    print(f"eklenen fiyat satiri : {toplam_satir}")
    print(f"bos seri             : {bos_seri}")
    print(f"tutarlilik uyarisi   : {uyari_sayisi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
