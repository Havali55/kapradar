"""TCMB kur arşivini doldurur ve Postgres'e yükler (spec §9, Adım 5).

Kullanım:
    python scripts/kur_cek.py                    # bildirimlerin kapsadığı aralık
    python scripts/kur_cek.py --baslangic 2025-09-01 --bitis 2026-09-18
    python scripts/kur_cek.py --yalniz-yukle     # ağa çıkmadan arşivi DB'ye bas

Maliyet sıfır. Kaldığı yerden devam eder: arşivde bülteni ya da "yayın
yok" işareti olan gün TCMB'ye yeniden sorulmaz.

Aralık varsayılanı veritabanındaki bildirimlerden türetiliyor ve başı
`AZAMI_GERI_GUN` kadar geriye çekiliyor: yılbaşı gibi uzun tatillerde
bildirim tarihinden önceki iş günü bir önceki yıla düşebiliyor.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.depo import AZAMI_GERI_GUN, Depo  # noqa: E402
from kap_radar.http_temel import VARSAYILAN_USER_AGENT  # noqa: E402
from kap_radar.tcmb import KurIstemcisi, kur_ayristir  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"
KONTROL_NOKTASI = "kur_cekim"


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


def bildirim_araligi(dsn: str) -> tuple[date, date] | None:
    """Veritabanındaki bildirimlerin kapsadığı tarih aralığı."""
    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(
                "select min(yayin_zamani)::date, max(yayin_zamani)::date "
                "from public.bildirim"
            )
            ilk, son = imlec.fetchone()
    return (ilk, son) if ilk else None


def gunler(baslangic: date, bitis: date):
    gun = baslangic
    while gun <= bitis:
        yield gun
        gun += timedelta(days=1)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="TCMB kur çekici")
    ayristirici.add_argument("--baslangic", type=tarih_coz)
    ayristirici.add_argument("--bitis", type=tarih_coz)
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    ayristirici.add_argument("--hiz-ms", type=int, default=500)
    ayristirici.add_argument(
        "--yalniz-yukle", action="store_true", help="ağa çıkma, arşivi DB'ye bas"
    )
    secenek = ayristirici.parse_args()

    dsn = env_oku(KOK / ".env").get("DATABASE_URL", "")
    if not dsn or "<PAROLA>" in dsn:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor.", file=sys.stderr)
        return 1

    baslangic, bitis = secenek.baslangic, secenek.bitis
    if not (baslangic and bitis):
        aralik = bildirim_araligi(dsn)
        if aralik is None:
            print("Veritabanında bildirim yok; --baslangic/--bitis verin.", file=sys.stderr)
            return 1
        baslangic = baslangic or aralik[0] - timedelta(days=AZAMI_GERI_GUN)
        bitis = bitis or aralik[1]

    arsiv = HamArsiv(secenek.arsiv)
    print(f"aralik   : {baslangic} — {bitis}")
    print(f"arsiv    : {secenek.arsiv}\n", flush=True)

    cekilen = yayin_yok = atlanan = 0
    if not secenek.yalniz_yukle:
        istemci = KurIstemcisi(
            user_agent=env_oku(KOK / ".env").get("KAP_USER_AGENT")
            or VARSAYILAN_USER_AGENT,
            istek_araligi_sn=secenek.hiz_ms / 1000,
        )
        try:
            for gun in gunler(baslangic, bitis):
                if arsiv.kur_var_mi(gun):
                    atlanan += 1
                    continue
                xml = istemci.ham(gun)
                if xml is None:
                    arsiv.kur_yok_isaretle(gun)
                    yayin_yok += 1
                else:
                    arsiv.kur_yaz(gun, xml)
                    cekilen += 1
                if (cekilen + yayin_yok) % 25 == 0:
                    print(
                        f"  {gun}: {cekilen} bülten, {yayin_yok} yayın yok",
                        flush=True,
                    )
        finally:
            istemci.kapat()

    # Yükleme ayrı geçiş: çekim kesilse bile arşivdeki her şey basılır.
    eklenen = mevcut = 0
    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        arsiv_gunleri = [g for g in arsiv.kur_gunleri() if baslangic <= g <= bitis]
        for sira, gun in enumerate(arsiv_gunleri, start=1):
            bulten = kur_ayristir(arsiv.kur_oku(gun))
            # Bülten tarihi dosya adından değil içerikten: TCMB bazen bir
            # günün dosyasını başka bir tarihle yayınlıyorsa kur yanlış
            # güne yazılmamalı.
            yeni = depo.kur_kaydet(bulten.tarih, bulten.kurlar)
            eklenen += yeni
            mevcut += len(bulten.kurlar) - yeni
            if sira % 50 == 0:
                baglanti.commit()
                print(f"  {sira}/{len(arsiv_gunleri)} bülten yüklendi", flush=True)

        depo.kontrol_noktasi_yaz(
            KONTROL_NOKTASI,
            son_islenen_tarih=bitis,
            notlar={"bulten": len(arsiv_gunleri), "kur_satiri": eklenen},
        )
        baglanti.commit()

    print("\n--- ozet ---")
    print(f"cekilen bulten : {cekilen}")
    print(f"yayin yok      : {yayin_yok}")
    print(f"arsivde vardi  : {atlanan}")
    print(f"eklenen kur    : {eklenen}")
    print(f"zaten vardi    : {mevcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
