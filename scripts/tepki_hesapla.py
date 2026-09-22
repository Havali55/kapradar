"""Her bildirim için t0 ve anormal getiriyi hesaplar (Adım 6, spec §8).

Kullanım:
    python scripts/tepki_hesapla.py                    # piyasa modeli (varsayılan)
    python scripts/tepki_hesapla.py --model beta1      # eski Σ (hisse − xu100)
    python scripts/tepki_hesapla.py --pencere-basi 1   # spec'in yazılı formülü

Ağa çıkmaz: girdisi `bildirim`, `fiyat_gunluk` ve `endeks_gunluk`.
Tekrar koşmak güvenli — tepki türetilmiş veri, üzerine yazılır.

Pencere: varsayılan `t0` dahil üç işlem günü. Spec §8'in yazılı formülü
`t0+1 .. t0+3` idi, ama t0 zaten "piyasanın ilk tepki verebileceği gün"
olarak tanımlı; ikisi birleşince asıl tepki günü pencerenin dışında
kalıyordu. `--pencere-basi 1` eski tanıma döner.

Model (2026-09-22, Adım 16 Öneri 4, "model C"): her bildirim için kendi
geçmişinden piyasa modeli betası, Vasicek ile evren ortalamasına
küçültülmüş. İki geçiş gerekiyor çünkü küçültmenin çapası ve ağırlığı
bütün tahminlerin dağılımından geliyor. Geçmişi yetmeyen bildirimler
(yeni halka arz) evren ortalaması beta ve α=0 ile hesaplanıp
`beta_kaynak='evren_ort'` diye işaretleniyor.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.depo import Depo  # noqa: E402
from kap_radar.fiyat import sicrama_gunleri  # noqa: E402
from kap_radar.tepki import (  # noqa: E402
    beta_tahmin,
    car_hesapla,
    getiri_serisi,
    t0_bul,
    vasicek_kucult,
)

KONTROL_NOKTASI = "tepki_hesap"
PENCERELER = {"car_1g": 1, "car_3g": 3, "car_5g": 5}
# Aynı hissenin diğer bildirimlerinden beta tahminine girmeyecek günler:
# t0 dahil üç işlem günü (car_3g penceresi).
OLAY_GUNU = 3


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


def ondalik(deger: float, basamak: int) -> Decimal:
    """Saklanan değer CAR'da kullanılanla aynı olsun diye önce yuvarlanır."""
    return Decimal(f"{deger:.{basamak}f}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="CAR hesabı")
    ayristirici.add_argument("--pencere-basi", type=int, default=0)
    ayristirici.add_argument(
        "--model", choices=("piyasa", "beta1"), default="piyasa"
    )
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
        # bellekte tutuluyor.
        endeks = depo.endeks_serisi(endeks_ilk, endeks_son)
        gunler = sorted(endeks)
        sira_no = {g: i for i, g in enumerate(gunler)}
        piyasa = getiri_serisi(endeks, gunler)
        seriler: dict[str, dict] = {}
        getiriler: dict[str, dict] = {}
        supheli: dict[str, set] = {}

        print(f"bildirim : {len(bildirimler)}")
        print(f"endeks   : {len(endeks)} işlem günü ({endeks_ilk} — {endeks_son})")
        print(f"pencere  : t0+{secenek.pencere_basi} başlangıçlı")
        print(f"model    : {secenek.model}\n", flush=True)

        # --- 1. geçiş: t0 ve seriler ----------------------------------
        olaylar = []
        t0_yok = 0
        olay_gunleri: dict[str, set] = defaultdict(set)
        for kap_id, ticker, yayin_zamani in bildirimler:
            t0 = t0_bul(yayin_zamani, endeks)
            if t0 is None:
                # Bildirim fiyat serisinin bittiği günden sonraysa tepki
                # henüz oluşmamıştır; uydurulmaz.
                t0_yok += 1
                continue

            if ticker not in seriler:
                seri = depo.fiyat_serisi(ticker, endeks_ilk, endeks_son)
                seriler[ticker] = seri
                getiriler[ticker] = getiri_serisi(seri, gunler)
                # Düzeltilmemiş bedelsizler: fiyat "var" olduğu için eksik
                # sayılmaz ama getirisi anlamsızdır (spec §13, risk 4).
                supheli[ticker] = set(sicrama_gunleri(seri))
                if supheli[ticker]:
                    print(f"  {ticker}: şüpheli gün {sorted(supheli[ticker])}")

            i = sira_no[t0]
            olay_gunleri[ticker].update(gunler[i : i + OLAY_GUNU])
            olaylar.append((kap_id, ticker, t0))

        # --- 2. geçiş: beta tahmini ve küçültme ------------------------
        katsayilar: dict[str, dict] = {}
        capa = None
        if secenek.model == "piyasa":
            tahminler = {
                kap_id: beta_tahmin(
                    getiriler[ticker],
                    piyasa,
                    gunler,
                    t0,
                    # Kendi olay günleri tahmin penceresine zaten girmiyor
                    # (tampon), diğerlerininkiler dışlanıyor.
                    haric=olay_gunleri[ticker],
                )
                for kap_id, ticker, t0 in olaylar
            }
            gecerli = [(k, t) for k, t in tahminler.items() if t is not None]
            if not gecerli:
                print("Beta tahmin edilebilen bildirim yok.", file=sys.stderr)
                return 1
            capa, kucuk = vasicek_kucult([t for _, t in gecerli])

            for (kap_id, tahmin), beta_k in zip(gecerli, kucuk):
                katsayilar[kap_id] = {
                    "model": "piyasa",
                    "beta": ondalik(beta_k, 6),
                    "alfa": ondalik(tahmin.alfa, 8),
                    "beta_ham": ondalik(tahmin.beta, 6),
                    "beta_gozlem": tahmin.gozlem,
                    "beta_r2": ondalik(tahmin.r2, 4),
                    "beta_kaynak": "tahmin",
                }
            for kap_id, tahmin in tahminler.items():
                if tahmin is None:
                    # Yeni halka arz: bu evrende β=1'den daha doğru varsayım
                    # evrenin kendi ortalaması. α uydurulmuyor.
                    katsayilar[kap_id] = {
                        "model": "piyasa",
                        "beta": ondalik(capa, 6),
                        "alfa": Decimal(0),
                        "beta_kaynak": "evren_ort",
                    }

        # --- 3. geçiş: CAR --------------------------------------------
        yazilan = 0
        eksik = defaultdict(int)
        for sira, (kap_id, ticker, t0) in enumerate(olaylar, start=1):
            model = katsayilar.get(kap_id, {"model": "beta1"})
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
                    alfa=model.get("alfa", Decimal(0)),
                    beta=model.get("beta", Decimal(1)),
                )
                if carlar[ad] is None:
                    eksik[ad] += 1

            depo.tepki_kaydet(
                kap_id,
                t0=t0,
                pencere_basi=secenek.pencere_basi,
                **carlar,
                **model,
            )
            yazilan += 1

            if sira % 100 == 0:
                baglanti.commit()
                print(f"  {sira}/{len(olaylar)} işlendi", flush=True)

        evren_ort = sum(
            1 for k in katsayilar.values() if k["beta_kaynak"] == "evren_ort"
        )
        depo.kontrol_noktasi_yaz(
            KONTROL_NOKTASI,
            son_islenen_tarih=endeks_son,
            notlar={
                "yazilan": yazilan,
                "pencere_basi": secenek.pencere_basi,
                "model": secenek.model,
                "capa": capa,
                "evren_ort": evren_ort,
            },
        )
        baglanti.commit()

    print("\n--- ozet ---")
    print(f"tepki yazilan : {yazilan}")
    print(f"t0 bulunamadi : {t0_yok}")
    if capa is not None:
        print(f"Vasicek capasi: {capa:.3f}")
        print(f"evren ort. β  : {evren_ort} bildirim (gecmis yetmedi)")
    for ad in PENCERELER:
        print(f"{ad} hesaplanamayan : {eksik[ad]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
