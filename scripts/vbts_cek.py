"""VBTS duyurularının detayını KAP'tan çeker (Modül B, gerçek veri).

Kullanım:  python scripts/vbts_cek.py

Liste arşivinde (`data/ham/liste/`) Borsa İstanbul'un "Pay Piyasasında
Volatilite Bazlı Tedbir Sistemi" duyuruları duruyor ama liste kaydı
yalnız hisseleri veriyor. Tedbirin TÜRÜ (açığa satış/kredi yasağı, brüt
takas, tek fiyat) ve SÜRESİ (başlangıç–bitiş seansı) detayın serbest
metninde. Bunlar olmadan "t0 anında hisse tedbir altında mıydı?"
sorusu cevaplanamaz.

Detaylar ayrı bir köke yazılıyor (`data/ham/vbts/detay/`): `data/ham/detay/`
Yeni İş İlişkisi yükleyicisinin kaynağı, oraya karışırsa onu kirletir.
Çekilmiş olan bir daha istenmez; kesilirse yeniden koşmak kaldığı yerden
devam eder. Ağ erişimi bedava (KAP kimliksiz API).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.istemci import KapIstemcisi  # noqa: E402

LISTE_KLASORU = KOK / "data" / "ham" / "liste"
VBTS_KOKU = KOK / "data" / "ham" / "vbts"
VBTS_OZETI = "Volatilite Bazlı Tedbir"


def vbts_indeksleri() -> list[int]:
    indeksler: set[int] = set()
    for dosya in sorted(LISTE_KLASORU.glob("*.json")):
        for kayit in json.loads(dosya.read_text(encoding="utf-8")):
            if VBTS_OZETI in (kayit.get("summary") or ""):
                indeksler.add(kayit["disclosureIndex"])
    return sorted(indeksler)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arsiv = HamArsiv(VBTS_KOKU)
    hepsi = vbts_indeksleri()
    eksik = [i for i in hepsi if not arsiv.var_mi(i)]
    print(f"VBTS duyurusu: {len(hepsi)}  arşivde: {len(hepsi) - len(eksik)}  "
          f"çekilecek: {len(eksik)}", flush=True)

    istemci = KapIstemcisi(istek_araligi_sn=1.2)
    hatali = []
    for sira, indeks in enumerate(eksik, start=1):
        try:
            arsiv.yaz(indeks, istemci.detay(indeks))
        except Exception as hata:  # tek bir duyuru koşuyu durdurmasın
            hatali.append(indeks)
            print(f"  {indeks}: {hata}", flush=True)
        if sira % 50 == 0:
            print(f"  {sira}/{len(eksik)}", flush=True)

    print(f"bitti. hatalı: {len(hatali)} {hatali[:10]}")
    return 1 if hatali else 0


if __name__ == "__main__":
    raise SystemExit(main())
