"""bildirim.karsi_taraf_acik sütununu sınıflandırıcıdan doldurur.

Kullanım:
    python scripts/karsi_taraf_isaretle.py          # KURU: ne değişecek
    python scripts/karsi_taraf_isaretle.py --yaz

Ağa çıkmaz. Sınıflandırma `kap_radar.karsi_taraf.karsi_taraf_acik`;
kural değişince bu betik yeniden koşulur ve yalnız sonucu değişen
satırları günceller. Değişen bildirimlerin skoru K çarpanı üzerinden
değişir: ardından `scripts/skor_yenile.py --yaz`.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.karsi_taraf import karsi_taraf_acik  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yaz", action="store_true")
    secenek = ap.parse_args()

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        with baglanti.cursor() as imlec:
            imlec.execute(
                "select kap_id, kap_alanlari ->> 'karsi_taraf', karsi_taraf_acik "
                "from public.bildirim"
            )
            satirlar = imlec.fetchall()

        degisen = []
        sayac: Counter = Counter()
        for kap_id, ad, eski in satirlar:
            yeni = karsi_taraf_acik(ad)
            sayac["açık" if yeni else "gizli/anonim"] += 1
            # Eski kural "alan boş değil"di; kaç bildirimin gerçekten
            # anonim olduğu ayrıca raporlanıyor.
            if (ad or "").strip() and not yeni:
                sayac["dolu ama anonim"] += 1
            if eski is not yeni:
                degisen.append({"kap_id": kap_id, "acik": yeni})

        print(f"bildirim       : {len(satirlar)}")
        for ad, n in sayac.most_common():
            print(f"  {ad:<16}: {n}")
        print(f"güncellenecek  : {len(degisen)}")

        if not secenek.yaz:
            print("KURU KOŞU — yazmak için --yaz")
            return 0

        with baglanti.cursor() as imlec:
            imlec.executemany(
                "update public.bildirim set karsi_taraf_acik = %(acik)s "
                "where kap_id = %(kap_id)s",
                degisen,
            )
        baglanti.commit()
        print(f"{len(degisen)} satır yazıldı")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
