"""Disk arşivindeki ham bildirimleri Postgres'e yükler (spec §9, Adım 4).

Kullanım:
    python scripts/yukle.py                 # data/ham -> Supabase
    python scripts/yukle.py --kuru          # yazmadan ne olacağını göster

Ağa çıkmaz: kaynağı `scripts/backfill_calistir.py`ın indirdiği arşiv.
Şema veya ayrıştırıcı değişirse bu komut yeniden koşturulur, KAP'tan
tekrar veri istenmez. Upsert idempotent olduğu için tekrar koşmak
zararsız (spec §5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayristirici import bildirim_ayristir  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"
HEDEF_SABLON = "oda-12000"
KONTROL_NOKTASI = "backfill_yukleme"

# Commit aralığı: her satırda commit etmek 1.100 gidiş-dönüş demek,
# hiç commit etmemek kesintide her şeyi kaybettirir.
COMMIT_ARALIGI = 100


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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="Arşivi Postgres'e yükle")
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    ayristirici.add_argument("--sablon", default=HEDEF_SABLON)
    ayristirici.add_argument(
        "--kuru", action="store_true", help="veritabanına yazmadan say"
    )
    secenek = ayristirici.parse_args()

    arsiv = HamArsiv(secenek.arsiv)
    indeksler = arsiv.indeksler()
    print(f"arsiv    : {secenek.arsiv} ({len(indeksler)} bildirim)")

    ayristirilan = []
    yanlis_sablon = []
    for indeks in indeksler:
        bildirim = bildirim_ayristir(arsiv.oku(indeks))
        if bildirim.sablon_kodu != secenek.sablon:
            # Ön eleme liste kaydındaki Türkçe `subject`e bakıyor; asıl
            # doğrulama şablon kodu (spec §9). Uyuşmayan yüklenmez.
            yanlis_sablon.append((indeks, bildirim.sablon_kodu))
            continue
        ayristirilan.append(bildirim)

    print(f"hedef    : {len(ayristirilan)} bildirim ({secenek.sablon})")
    if yanlis_sablon:
        print(f"ATLANAN  : {len(yanlis_sablon)} farklı şablon -> {yanlis_sablon[:5]}")

    if secenek.kuru:
        print("kuru koşu — veritabanına yazılmadı")
        return 0

    dsn = env_oku(KOK / ".env").get("DATABASE_URL", "")
    if not dsn or "<PAROLA>" in dsn:
        print(
            "DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor.\n"
            "Supabase panel > Settings > Database > Reset database password",
            file=sys.stderr,
        )
        return 1

    eklenen = mevcut = 0
    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        for sira, bildirim in enumerate(ayristirilan, start=1):
            if depo.bildirim_kaydet(bildirim):
                eklenen += 1
            else:
                mevcut += 1
            if sira % COMMIT_ARALIGI == 0:
                depo.kontrol_noktasi_yaz(
                    KONTROL_NOKTASI,
                    son_islenen_index=bildirim.kap_index,
                    notlar={"eklenen": eklenen, "mevcut": mevcut},
                )
                baglanti.commit()
                print(f"  {sira}/{len(ayristirilan)} işlendi", flush=True)

        depo.kontrol_noktasi_yaz(
            KONTROL_NOKTASI,
            son_islenen_index=ayristirilan[-1].kap_index if ayristirilan else None,
            notlar={"eklenen": eklenen, "mevcut": mevcut},
        )
        baglanti.commit()

    print("\n--- ozet ---")
    print(f"eklenen  : {eklenen}")
    print(f"zaten var: {mevcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
