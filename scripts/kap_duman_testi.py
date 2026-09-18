"""Gerçek KAP'a karşı uçtan uca duman testi.

Birim testler sahte yanıtlarla koşuyor; bu script gerçek ağa çıkar ve
istemci + ayrıştırıcı zincirinin gerçekten çalıştığını gösterir.

Kullanım:  python scripts/kap_duman_testi.py [gun_sayisi]

Nazik davranır: varsayılan hız sınırıyla toplam 3-4 istek atar.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kap_radar.ayristirici import aciklama_metinleri, bildirim_ayristir  # noqa: E402
from kap_radar.istemci import KapIstemcisi  # noqa: E402

HEDEF_SABLON = "oda-12000"  # Yeni İş İlişkisi


def user_agent_oku() -> str | None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return None
    for satir in env.read_text(encoding="utf-8").splitlines():
        if satir.startswith("KAP_USER_AGENT="):
            return satir.split("=", 1)[1].strip()
    return None


def main() -> int:
    gun = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    bitis = date.today()
    baslangic = bitis - timedelta(days=gun - 1)

    user_agent = os.environ.get("KAP_USER_AGENT") or user_agent_oku()
    istemci = KapIstemcisi(**({"user_agent": user_agent} if user_agent else {}))

    try:
        print(f"[1] liste çekiliyor: {baslangic} .. {bitis}")
        kayitlar = istemci.liste(baslangic, bitis)
        print(f"    {len(kayitlar)} bildirim döndü")

        hedefler = [k for k in kayitlar if k.get("subject") == "Yeni İş İlişkisi"]
        print(f"    bunların {len(hedefler)} tanesi 'Yeni İş İlişkisi'")

        if not hedefler:
            print("    (bu pencerede hedef şablon yok — daha geniş aralık deneyin)")
            return 0

        secilen = hedefler[0]
        index = secilen["disclosureIndex"]
        print(f"\n[2] detay çekiliyor: {index} ({secilen.get('stockCodes')})")
        detay = istemci.detay(index)

        print("\n[3] ayrıştırılıyor")
        bildirim = bildirim_ayristir(detay)
        metin = aciklama_metinleri(detay["disclosureBody"][0])

        print(f"    kap_id       : {bildirim.kap_id}")
        print(f"    kap_index    : {bildirim.kap_index}")
        print(f"    ticker       : {bildirim.ticker}")
        print(f"    sablon_kodu  : {bildirim.sablon_kodu}")
        print(f"    yayin_zamani : {bildirim.yayin_zamani}")
        print(f"    guncelleme   : {bildirim.guncelleme_mi}")
        print(f"    onceki tarih : {bildirim.onceki_aciklama_tarihleri}")
        print(f"    karsi_taraf  : {bildirim.kap_alanlari['karsi_taraf']}")
        print(f"    niteligi     : {bildirim.kap_alanlari['karsi_taraf_niteligi']}")
        print(f"    baslangic    : {bildirim.kap_alanlari['baslangic']}")
        print(f"\n    TR metin ({len(metin.tr)} karakter):")
        print("    " + metin.tr[:300].replace("\n", "\n    "))

        if bildirim.sablon_kodu != HEDEF_SABLON:
            print(f"\nUYARI: beklenen şablon {HEDEF_SABLON}, gelen {bildirim.sablon_kodu}")
            return 1
        if "EUR " in metin.tr and " + VAT" in metin.tr:
            print("\nUYARI: TR metne İngilizce sızmış görünüyor")
            return 1

        print("\nDUMAN TESTI GECTI")
        return 0
    finally:
        istemci.kapat()


if __name__ == "__main__":
    raise SystemExit(main())
