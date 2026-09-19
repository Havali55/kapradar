"""Her bildirim için t0 ve anormal getiriyi hesaplar (Adım 6, spec §8).

Kullanım:
    python scripts/tepki_hesapla.py
    python scripts/tepki_hesapla.py --pencere-basi 1   # spec'in yazılı formülü

Ağa çıkmaz: girdisi `bildirim`, `fiyat_gunluk` ve `endeks_gunluk`.
Tekrar koşmak güvenli — tepki türetilmiş veri, üzerine yazılır.

Pencere: varsayılan `t0` dahil üç işlem günü. Spec §8'in yazılı formülü
`t0+1 .. t0+3` idi, ama t0 zaten "piyasanın ilk tepki verebileceği gün"
olarak tanımlı; ikisi birleşince asıl tepki günü pencerenin dışında
kalıyordu. `--pencere-basi 1` eski tanıma döner.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.depo import Depo  # noqa: E402
from kap_radar.fiyat import sicrama_gunleri  # noqa: E402
from kap_radar.tepki import car_hesapla, t0_bul  # noqa: E402

KONTROL_NOKTASI = "tepki_hesap"
PENCERELER = {"car_1g": 1, "car_3g": 3, "car_5g": 5}


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

    ayristirici = argparse.ArgumentParser(description="CAR hesabı")
    ayristirici.add_argument("--pencere-basi", type=int, default=0)
    secenek = ayristirici.parse_args()

    dsn = env_oku(KOK / ".env").get("DATABASE_URL", "")
    if not dsn or "<PAROLA>" in dsn:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor.", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)

        with baglanti.cursor() as imlec:
            imlec.execute(
                "select kap_id, ticker, yayin_zamani from public.bildirim "
                "where ticker is not null order by yayin_zamani"
            )
            bildirimler = imlec.fetchall()
            imlec.execute(
                "select min(tarih), max(tarih) from public.endeks_gunluk"
            )
            endeks_ilk, endeks_son = imlec.fetchone()

        if endeks_ilk is None:
            print("endeks_gunluk boş; önce scripts/fiyat_cek.py", file=sys.stderr)
            return 1

        # Endeks serisi hem takvim hem karşılaştırma tabanı; bir kez okunup
        # bellekte tutuluyor (bir yıl ≈ 250 satır).
        endeks = depo.endeks_serisi(endeks_ilk, endeks_son)
        seriler: dict[str, dict] = {}
        supheli: dict[str, set] = {}

        print(f"bildirim : {len(bildirimler)}")
        print(f"endeks   : {len(endeks)} işlem günü ({endeks_ilk} — {endeks_son})")
        print(f"pencere  : t0+{secenek.pencere_basi} başlangıçlı\n", flush=True)

        yazilan = 0
        t0_yok = 0
        eksik = defaultdict(int)

        for sira, (kap_id, ticker, yayin_zamani) in enumerate(bildirimler, start=1):
            t0 = t0_bul(yayin_zamani, endeks)
            if t0 is None:
                # Bildirim fiyat serisinin bittiği günden sonraysa tepki
                # henüz oluşmamıştır; uydurulmaz.
                t0_yok += 1
                continue

            if ticker not in seriler:
                seri = depo.fiyat_serisi(ticker, endeks_ilk, endeks_son)
                seriler[ticker] = seri
                # Düzeltilmemiş bedelsizler: fiyat "var" olduğu için eksik
                # sayılmaz ama getirisi anlamsızdır (spec §13, risk 4).
                supheli[ticker] = set(sicrama_gunleri(seri))
                if supheli[ticker]:
                    print(f"  {ticker}: şüpheli gün {sorted(supheli[ticker])}")

            carlar = {}
            for ad, gun in PENCERELER.items():
                carlar[ad] = car_hesapla(
                    seriler[ticker],
                    endeks,
                    t0,
                    pencere=(
                        secenek.pencere_basi,
                        secenek.pencere_basi + gun - 1,
                    ),
                    supheli_gunler=supheli[ticker],
                )
                if carlar[ad] is None:
                    eksik[ad] += 1

            depo.tepki_kaydet(
                kap_id,
                t0=t0,
                pencere_basi=secenek.pencere_basi,
                **carlar,
            )
            yazilan += 1

            if sira % 100 == 0:
                baglanti.commit()
                print(f"  {sira}/{len(bildirimler)} işlendi", flush=True)

        depo.kontrol_noktasi_yaz(
            KONTROL_NOKTASI,
            son_islenen_tarih=endeks_son,
            notlar={"yazilan": yazilan, "pencere_basi": secenek.pencere_basi},
        )
        baglanti.commit()

    print("\n--- ozet ---")
    print(f"tepki yazilan : {yazilan}")
    print(f"t0 bulunamadi : {t0_yok}")
    for ad in PENCERELER:
        print(f"{ad} hesaplanamayan : {eksik[ad]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
