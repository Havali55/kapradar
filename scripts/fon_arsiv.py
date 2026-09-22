"""Tüm piyasanın fon portföy raporlarını arşivler (bağlam katmanı F1).

Kullanım:
    python scripts/fon_arsiv.py                  # 2025-08'den bugüne
    python scripts/fon_arsiv.py --baslangic 2026-06-01

`fon_cek.py` yalnız tasfiyedeki 7 şirketin kriz öncesi son raporunu
alıyordu. Bu betik hisse tutabilecek her fonun her ayki raporunu alıyor:
hisse × dönem fon sahipliği haritası buradan kurulur (fon_yukle.py).

Seçim:
  - Konu "Portföy Dağılım Raporu"
  - Hisse tutamayan fon türleri dışarıda (para piyasası, borçlanma
    araçları, altın, kira sertifikası…) — başlıktan
  - Fon başına ayda TEK rapor (ayın son yayınlananı); haftalık raporlar
    aynı ayda tekrar ediyor
  - EN YENİDEN ESKİYE: kesilirse elde sitenin ihtiyacı olan son dönem kalır

Kaldığı yerden devam eder: PDF'i ya da `.muaf` işareti olan rapor bir
daha istenmez. Ağ erişimi bedava (KAP kimliksiz API).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, str(KOK / "scripts"))

from fon_cek import FON_KOKU, PDF_KLASORU, listeyi_cek, zaman  # noqa: E402

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.istemci import KapIstemcisi  # noqa: E402

HISSE_TUTAMAZ = re.compile(
    r"PARA PİYASASI|BORÇLANMA ARAÇ|KİRA SERTİFİKA|ALTIN|GÜMÜŞ|KIYMETLİ MADEN|"
    r"EUROBOND|KISA VADELİ|LİKİT|TAHVİL|BONO|EMEKLİLİK|KATKI",
    re.I,
)


def secilecekler(kayitlar: list[dict]) -> list[dict]:
    ay_son: dict[tuple, dict] = {}
    for k in kayitlar:
        if k.get("subject") != "Portföy Dağılım Raporu":
            continue
        if HISSE_TUTAMAZ.search(k.get("kapTitle") or ""):
            continue
        z = zaman(k)
        anahtar = (k.get("fundCode") or k["kapTitle"], z.year, z.month)
        if anahtar not in ay_son or z > zaman(ay_son[anahtar]):
            ay_son[anahtar] = k
    return sorted(ay_son.values(), key=zaman, reverse=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baslangic", type=date.fromisoformat, default=date(2025, 8, 1))
    ap.add_argument(
        "--en-eski",
        type=date.fromisoformat,
        help="yalnız bu tarihten sonra yayınlanan raporları indir (ör. son ay)",
    )
    secenek = ap.parse_args()

    arsiv = HamArsiv(FON_KOKU)
    # 1,2 sn'de WAF bağlantıyı kesmeye başladı (2026-09-22); daha nazik.
    istemci = KapIstemcisi(istek_araligi_sn=2.0)
    kayitlar = listeyi_cek(istemci, arsiv, secenek.baslangic, date.today())
    secim = secilecekler(kayitlar)
    if secenek.en_eski:
        secim = [k for k in secim if zaman(k).date() >= secenek.en_eski]
    PDF_KLASORU.mkdir(parents=True, exist_ok=True)

    def bitti(k: dict) -> bool:
        p = PDF_KLASORU / f"{k['disclosureIndex']}.pdf"
        return p.exists() or p.with_suffix(".muaf").exists()

    eksik = [k for k in secim if not bitti(k)]
    print(f"fon bildirimi {len(kayitlar)} · seçilen rapor {len(secim)} · "
          f"çekilecek {len(eksik)}", flush=True)

    hata = 0
    for sira, k in enumerate(eksik, start=1):
        indeks = k["disclosureIndex"]
        pdf = PDF_KLASORU / f"{indeks}.pdf"
        try:
            detay = arsiv.oku(indeks) if arsiv.var_mi(indeks) else istemci.detay(indeks)
            arsiv.yaz(indeks, detay)
            ekler = [e for e in detay.get("attachments") or []
                     if (e.get("fileExtension") or "").lower() == "pdf"]
            if not ekler:
                pdf.with_suffix(".muaf").write_text("", encoding="utf-8")
            else:
                gecici = pdf.with_suffix(".tmp")
                gecici.write_bytes(istemci.ek_indir(ekler[0]["objId"], indeks))
                gecici.replace(pdf)
        except Exception as h:  # tek rapor koşuyu durdurmasın
            hata += 1
            print(f"  {indeks}: {h}", flush=True)
        if sira % 100 == 0:
            print(f"  {sira}/{len(eksik)}  ({k['publishDate'][:10]})  "
                  f"{datetime.now():%H:%M}", flush=True)

    print(f"bitti. hata: {hata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
