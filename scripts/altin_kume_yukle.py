"""Elle etiketlenmiş altın kümeyi doğrular ve veritabanına yazar (Adım 8).

Kullanım:
    python scripts/altin_kume_yukle.py --kuru    # yalnız doğrula
    python scripts/altin_kume_yukle.py           # doğrula + Supabase'e yaz

Doğrulama neden zorunlu: altın küme doğruluk ölçümünün referansı. Elle
yazılmış bir alıntının ham metinde birebir geçmediği fark edilmezse,
ölçüm modeli değil etiketi cezalandırır. Bu yüzden her etiket §6'nın
metin kapısından geçiriliyor — model çıktısı gibi.

Bilerek kapıya takılan iki kayıt var (`beklenen_kapi` alanı): A5'in
mükerrer kalem kuralı, aynı para biriminde iki ayrı gerçek sözleşme
olan bildirimleri de reddediyor. Bu bilinen ve kabul edilmiş bir
yanlış-red; küme bunu belgelemek için içeriyor.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.ayristirici import bildirim_ayristir  # noqa: E402
from kap_radar.cikarim import Karar, TutarCikarimi, metin_kapisi  # noqa: E402

VARSAYILAN_ARSIV = KOK / "data" / "ham"
VARSAYILAN_KUME = KOK / "data" / "altin_kume.json"

ALTIN_UPSERT = (
    "insert into public.altin_kume (kap_id, elle_dogrulanmis, etiketleyen) "
    "values (%(kap_id)s, %(veri)s, %(etiketleyen)s) "
    "on conflict (kap_id) do update set "
    "elle_dogrulanmis = excluded.elle_dogrulanmis, "
    "etiketleyen = excluded.etiketleyen, etiketlendi_at = now()"
)


def kapi_icin_cikarim(kayit: dict) -> TutarCikarimi:
    """Etiketi model çıktısı biçimine sokar.

    `hap_ozet` ve `guven` altın kümede tutulmuyor (doğrulanabilir alan
    değiller); kapının o dallarını tetiklemeyecek yer tutucular konuyor.
    """
    return TutarCikarimi(
        tutarlar=kayit["tutarlar"],
        tutar_gizli=kayit["tutar_gizli"],
        hap_ozet=["-", "-", "-"],
        guven="yuksek",
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="Altın kümeyi yükle")
    ayristirici.add_argument("--kume", type=Path, default=VARSAYILAN_KUME)
    ayristirici.add_argument("--arsiv", type=Path, default=VARSAYILAN_ARSIV)
    ayristirici.add_argument("--kuru", action="store_true")
    secenek = ayristirici.parse_args()

    kume = json.loads(secenek.kume.read_text(encoding="utf-8"))
    kayitlar = kume["kayitlar"]
    arsiv = HamArsiv(secenek.arsiv)

    metinler = {
        b.kap_id: b.ham_metin_tr
        for b in (bildirim_ayristir(arsiv.oku(i)) for i in arsiv.indeksler())
    }

    print(f"kume     : {secenek.kume.name} ({len(kayitlar)} bildirim)")

    gecen, beklenen_red, hatali = [], [], []
    tabaka = Counter()
    kalem = tip = 0

    for kayit in kayitlar:
        tabaka[kayit.get("tabaka", "?")] += 1
        kalem += len(kayit["tutarlar"])
        tip += sum(1 for t in kayit["tutarlar"] if t["tip"] == "toplam_sozlesme")

        metin = metinler.get(kayit["kap_id"])
        if metin is None:
            hatali.append((kayit["kap_index"], "arsivde yok"))
            continue

        sonuc = metin_kapisi(kapi_icin_cikarim(kayit), metin)
        beklenen = kayit.get("beklenen_kapi")

        if sonuc.karar is Karar.YAYINLA and not beklenen:
            gecen.append(kayit["kap_index"])
        elif beklenen and (sonuc.red_nedeni or "").startswith(beklenen):
            beklenen_red.append((kayit["kap_index"], sonuc.red_nedeni))
        else:
            hatali.append((kayit["kap_index"], sonuc.red_nedeni or "beklenen red gelmedi"))

    print("\n--- dogrulama ---")
    print(f"kapidan gecen : {len(gecen)}")
    print(f"beklenen red  : {len(beklenen_red)} -> {[i for i, _ in beklenen_red]}")
    print(f"HATALI ETIKET : {len(hatali)}")
    for indeks, neden in hatali:
        print(f"  {indeks}: {neden}")

    print("\n--- kume profili ---")
    print(f"tabakalar   : {dict(tabaka)}")
    print(f"tutar kalemi: {kalem} (bunlarin {tip} tanesi toplam_sozlesme)")
    print(f"tutarsiz    : {sum(1 for k in kayitlar if not k['tutarlar'])}")

    if hatali:
        print("\nHatalı etiketler düzeltilmeden yükleme yapılmaz.", file=sys.stderr)
        return 1

    if secenek.kuru:
        print("\nkuru koşu — veritabanına yazılmadı")
        return 0

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti, baglanti.cursor() as imlec:
        for kayit in kayitlar:
            imlec.execute(
                ALTIN_UPSERT,
                {
                    "kap_id": kayit["kap_id"],
                    "veri": Jsonb(
                        {
                            "tutarlar": kayit["tutarlar"],
                            "tutar_gizli": kayit["tutar_gizli"],
                            "tabaka": kayit.get("tabaka"),
                            "not": kayit.get("not"),
                            "beklenen_kapi": kayit.get("beklenen_kapi"),
                        }
                    ),
                    "etiketleyen": kume["etiketleyen"],
                },
            )
        baglanti.commit()

    print(f"\n{len(kayitlar)} etiket altin_kume tablosuna yazildi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
