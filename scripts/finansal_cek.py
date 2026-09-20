"""Şirketlerin finansal raporlarını KAP'tan çekip arşive indirir (Adım 7).

Kullanım:
    python scripts/finansal_cek.py                       # 2024-09-01 -> bugün
    python scripts/finansal_cek.py --baslangic 2025-01-01
    python scripts/finansal_cek.py --tickerlar ORGE,ARDYZ  # deneme koşusu

Maliyet sıfır: KAP'ın kimliksiz JSON API'si, LLM yok.

Aralık neden 2024-09'dan başlıyor: elimizdeki en eski bildirim
2025-09-22. O bildirimin paydası için o gün açıklanmış son raporu ve
TTM köprüsünün yıllık bacağını (FY2024, genelde Şubat-Nisan 2025'te
yayınlanıyor) görmek gerekiyor. Geç bildiren şirketler için bir yıl
daha pay bırakıldı.

Kaldığı yerden devam eder: arşivdeki pencere yeniden sorulmaz, arşivdeki
rapor yeniden çekilmez.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import env_oku  # noqa: E402
from kap_radar.backfill import finansal_backfill  # noqa: E402
from kap_radar.istemci import VARSAYILAN_USER_AGENT, KapIstemcisi  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"
VARSAYILAN_BASLANGIC = date(2024, 9, 1)
VARSAYILAN_PENCERE_GUN = 3


def tarih_coz(metin: str) -> date:
    return datetime.strptime(metin, "%Y-%m-%d").date()


def arsivden_tickerlar(arsiv: HamArsiv) -> set[str]:
    """Bildirim arşivindeki şirketler.

    Kaynak veritabanı değil arşiv: bu betik ağ betiği, DSN'e bağımlı
    olmasın. Zaten hangi şirketlerin hasılatına ihtiyaç olduğu tam
    olarak "bildirimi olan şirketler" demek.
    """
    tickerlar: set[str] = set()
    for indeks in arsiv.indeksler():
        kunye = arsiv.oku(indeks)["disclosure"]["disclosureBasic"]
        kod = (kunye.get("stockCode") or "").strip()
        if kod:
            tickerlar.update(parca.strip() for parca in kod.split(",") if parca.strip())
    return tickerlar


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="KAP finansal rapor çekimi")
    ayristirici.add_argument("--baslangic", type=tarih_coz, default=VARSAYILAN_BASLANGIC)
    ayristirici.add_argument("--bitis", type=tarih_coz, default=date.today())
    ayristirici.add_argument("--pencere", type=int, default=VARSAYILAN_PENCERE_GUN)
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    ayristirici.add_argument(
        "--tickerlar", help="virgülle ayrılmış liste; verilmezse arşivden çıkarılır"
    )
    ayristirici.add_argument("--hiz-ms", type=int)
    ayristirici.add_argument("--deneme", type=int)
    secenek = ayristirici.parse_args()

    arsiv = HamArsiv(secenek.arsiv)
    if secenek.tickerlar:
        tickerlar = {t.strip() for t in secenek.tickerlar.split(",") if t.strip()}
    else:
        tickerlar = arsivden_tickerlar(arsiv)

    env = env_oku(KOK / ".env")
    aralik_ms = secenek.hiz_ms or int(env.get("KAP_ISTEK_ARALIGI_MS", "500"))
    deneme = secenek.deneme or int(env.get("KAP_MAKS_YENIDEN_DENEME", "5"))
    istemci = KapIstemcisi(
        user_agent=env.get("KAP_USER_AGENT") or VARSAYILAN_USER_AGENT,
        istek_araligi_sn=aralik_ms / 1000,
        maks_deneme=deneme,
    )

    print(f"aralik   : {secenek.baslangic} — {secenek.bitis}")
    print(f"sirket   : {len(tickerlar)}")
    print(f"arsiv    : {secenek.arsiv}")
    print(f"hiz      : {aralik_ms} ms/istek, {deneme} deneme\n", flush=True)

    baslangic_an = datetime.now()
    try:
        ozet = finansal_backfill(
            istemci=istemci,
            arsiv=arsiv,
            baslangic=secenek.baslangic,
            bitis=secenek.bitis,
            tickerlar=tickerlar,
            pencere_gun=secenek.pencere,
            gunluk=lambda mesaj: print(mesaj, flush=True),
        )
    finally:
        istemci.kapat()

    print("\n--- ozet ---")
    print(f"pencere  : {ozet.pencere}")
    print(f"aday     : {ozet.aday}")
    print(f"cekildi  : {ozet.cekildi}")
    print(f"atlandi  : {ozet.atlandi}")
    print(f"sure     : {datetime.now() - baslangic_an}")

    if ozet.gelir_tablosuz:
        print(
            f"GELIR TABLOSU YOK: {len(ozet.gelir_tablosuz)} rapor "
            f"-> {ozet.gelir_tablosuz[:10]}"
        )
    if ozet.hatalar:
        print(f"HATA ALAN {len(ozet.hatalar)} rapor: {ozet.hatalar[:20]}")
        print("Aynı komutu tekrar çalıştırmak yalnızca bunları dener.")
    if ozet.hatali_pencereler:
        print(f"CEKILEMEYEN {len(ozet.hatali_pencereler)} pencere (WAF):")
        for basi, sonu in ozet.hatali_pencereler:
            print(f"  {basi} — {sonu}")
        print("Aynı komutu tekrar çalıştırmak yalnızca bunları dener.")
    if ozet.tasan_pencereler:
        print(f"SINIRA DAYANAN pencereler: {ozet.tasan_pencereler}")

    eksik = ozet.hatalar or ozet.tasan_pencereler or ozet.hatali_pencereler
    return 1 if eksik else 0


if __name__ == "__main__":
    raise SystemExit(main())
