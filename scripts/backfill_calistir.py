"""12 aylık backfill'i canlı KAP'a karşı koşturur (spec §9, Adım 4).

Kullanım:
    python scripts/backfill_calistir.py                  # son 365 gün
    python scripts/backfill_calistir.py --gun-sayisi 7   # deneme koşusu
    python scripts/backfill_calistir.py --baslangic 2025-09-19 --bitis 2026-09-18

Maliyet sıfır: yalnızca KAP'ın kimliksiz JSON API'si kullanılıyor, LLM
devrede değil. Koşu kesilirse aynı komut kaldığı yerden devam eder —
arşivdeki pencere yeniden sorulmaz, arşivdeki bildirim yeniden çekilmez.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.backfill import backfill  # noqa: E402
from kap_radar.istemci import VARSAYILAN_USER_AGENT, KapIstemcisi  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"

# Günde ~475 bildirim düşüyor; KAP listeyi 2.000'de kesiyor. 3 günlük
# pencere sınırın altında kalıyor, 7 günlük pencere her seferinde bölünüp
# yeniden sorulacağı için boşa istek üretirdi.
VARSAYILAN_PENCERE_GUN = 3


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
    # Windows konsolu varsayılanda cp1254; Türkçe kayıt satırları
    # UnicodeEncodeError ile koşuyu ortasından kesmesin.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="KAP backfill")
    ayristirici.add_argument("--gun-sayisi", type=int, default=365)
    ayristirici.add_argument("--baslangic", type=tarih_coz)
    ayristirici.add_argument("--bitis", type=tarih_coz)
    ayristirici.add_argument("--pencere", type=int, default=VARSAYILAN_PENCERE_GUN)
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    secenek = ayristirici.parse_args()

    bitis = secenek.bitis or date.today()
    baslangic = secenek.baslangic or bitis - timedelta(days=secenek.gun_sayisi - 1)

    env = env_oku(KOK / ".env")
    aralik_ms = int(env.get("KAP_ISTEK_ARALIGI_MS", "500"))
    istemci = KapIstemcisi(
        user_agent=env.get("KAP_USER_AGENT") or VARSAYILAN_USER_AGENT,
        istek_araligi_sn=aralik_ms / 1000,
        maks_deneme=int(env.get("KAP_MAKS_YENIDEN_DENEME", "5")),
    )

    print(f"aralik   : {baslangic} — {bitis}")
    print(f"pencere  : {secenek.pencere} gün")
    print(f"arsiv    : {secenek.arsiv}")
    print(f"hiz      : {aralik_ms} ms/istek\n", flush=True)

    baslangic_an = datetime.now()
    try:
        ozet = backfill(
            istemci=istemci,
            arsiv=HamArsiv(secenek.arsiv),
            baslangic=baslangic,
            bitis=bitis,
            pencere_gun=secenek.pencere,
            gunluk=lambda mesaj: print(mesaj, flush=True),
        )
    finally:
        istemci.kapat()

    sure = datetime.now() - baslangic_an
    print("\n--- ozet ---")
    print(f"pencere  : {ozet.pencere}")
    print(f"aday     : {ozet.aday}")
    print(f"cekildi  : {ozet.cekildi}")
    print(f"atlandi  : {ozet.atlandi}")
    print(f"sure     : {sure}")

    if ozet.hatalar:
        print(f"HATA ALAN {len(ozet.hatalar)} bildirim: {ozet.hatalar}")
        print("Aynı komutu tekrar çalıştırmak yalnızca bunları dener.")
    if ozet.tasan_pencereler:
        print(f"SINIRA DAYANAN pencereler (veri eksik olabilir): {ozet.tasan_pencereler}")

    return 1 if ozet.hatalar or ozet.tasan_pencereler else 0


if __name__ == "__main__":
    raise SystemExit(main())
