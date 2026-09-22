"""Tasfiyedeki 7 portföy şirketinin fon portföy raporlarını çeker.

Kullanım:  python scripts/fon_cek.py

17.09.2026'da SPK Tera, Pusula, Hedef, Atlas, A1, Pardus ve Bulls
portföy şirketlerinin 131 fonunu işleme kapattı; tasfiye ~6 ay sürecek,
yani bu fonların elindeki hisseler aylara yayılarak satılacak. Hangi
hissenin bu baskı altında olduğunu fonların kendi Portföy Dağılım
Raporları söylüyor.

Adımlar (hepsi bedava, KAP kimliksiz API):
  1. Fon bildirim listesi → data/ham/fon/liste/ (şirket listesinden AYRI
     uç nokta; 2.000 sınırına dayanan pencere günlere bölünür)
  2. 7 şirketin her fonu için krizden (09.09.2026) önceki SON rapor
  3. Raporun eki (PDF) → data/ham/fon/pdf/{index}.pdf

Nitelikli yatırımcıya satılan serbest fonlar rapor yükümlülüğünden muaf;
eksiz rapor "muaf" diye kaydedilir, uydurulmaz.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.istemci import KapIstemcisi  # noqa: E402

FON_KOKU = KOK / "data" / "ham" / "fon"
PDF_KLASORU = FON_KOKU / "pdf"
OZET = FON_KOKU / "secim.json"

BASLANGIC = date(2026, 6, 1)
BITIS = date(2026, 9, 22)
PENCERE_GUN = 3
KRIZ_BASI = datetime(2026, 9, 9)
SINIR = 2000

SIRKETLER = {
    "TERA": r"\bTERA PORTFÖY",
    "PUSULA": r"\bPUSULA PORTFÖY",
    "HEDEF": r"\bHEDEF PORTFÖY",
    "ATLAS": r"\bATLAS PORTFÖY",
    "A1": r"\bA1 (CAPITAL )?PORTFÖY",
    "PARDUS": r"\bPARDUS PORTFÖY",
    "BULLS": r"\bBULLS PORTFÖY",
}


def sirket_bul(baslik: str) -> str | None:
    return next((k for k, p in SIRKETLER.items() if re.search(p, baslik)), None)


def listeyi_cek(istemci: KapIstemcisi, arsiv: HamArsiv) -> list[dict]:
    kayitlar: dict[int, dict] = {}
    bas = BASLANGIC
    while bas <= BITIS:
        bit = min(bas + timedelta(days=PENCERE_GUN - 1), BITIS)
        gunler = [(bas, bit)]
        while gunler:
            b, e = gunler.pop()
            if arsiv.liste_var_mi(b, e):
                parca = arsiv.liste_oku(b, e)
            else:
                parca = istemci.fon_liste(b, e)
                if len(parca) >= SINIR and b < e:
                    # Sınıra dayandı: günlere böl, bu pencereyi kaydetme.
                    gunler += [(b + timedelta(days=i), b + timedelta(days=i))
                               for i in range((e - b).days + 1)]
                    continue
                if len(parca) >= SINIR:
                    print(f"  !! {b} tek günde {SINIR} sınırında — eksik olabilir")
                arsiv.liste_yaz(b, e, parca)
            for k in parca:
                kayitlar[k["disclosureIndex"]] = k
        bas = bit + timedelta(days=1)
    return list(kayitlar.values())


def zaman(k: dict) -> datetime:
    return datetime.strptime(k["publishDate"], "%d.%m.%Y %H:%M:%S")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arsiv = HamArsiv(FON_KOKU)
    istemci = KapIstemcisi(istek_araligi_sn=1.2)

    kayitlar = listeyi_cek(istemci, arsiv)
    print(f"fon bildirimi: {len(kayitlar)}", flush=True)

    # Her fon için krizden önceki son Portföy Dağılım Raporu.
    son: dict[str, dict] = {}
    for k in kayitlar:
        if k.get("subject") != "Portföy Dağılım Raporu" or zaman(k) >= KRIZ_BASI:
            continue
        sirket = sirket_bul(k.get("kapTitle") or "")
        if sirket is None:
            continue
        kod = k.get("fundCode") or k["kapTitle"]
        if kod not in son or zaman(k) > zaman(son[kod]):
            son[kod] = k | {"_sirket": sirket}
    print(f"7 şirketin raporlu fonu: {len(son)}", flush=True)

    PDF_KLASORU.mkdir(parents=True, exist_ok=True)
    secim = []
    for sira, (kod, k) in enumerate(sorted(son.items()), start=1):
        indeks = k["disclosureIndex"]
        pdf = PDF_KLASORU / f"{indeks}.pdf"
        durum = "var"
        if not pdf.exists():
            try:
                detay = arsiv.oku(indeks) if arsiv.var_mi(indeks) else istemci.detay(indeks)
                arsiv.yaz(indeks, detay)
                ekler = [e for e in detay.get("attachments") or []
                         if (e.get("fileExtension") or "").lower() == "pdf"]
                if not ekler:
                    durum = "muaf"
                else:
                    gecici = pdf.with_suffix(".tmp")
                    gecici.write_bytes(istemci.ek_indir(ekler[0]["objId"], indeks))
                    gecici.replace(pdf)
                    durum = "indirildi"
            except Exception as hata:  # tek rapor koşuyu durdurmasın
                durum = f"hata: {hata}"
        secim.append({"fon": kod, "sirket": k["_sirket"], "baslik": k["kapTitle"],
                      "index": indeks, "yayin": k["publishDate"], "durum": durum})
        if sira % 20 == 0:
            print(f"  {sira}/{len(son)}", flush=True)

    OZET.write_text(json.dumps(secim, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("durum:", Counter(s["durum"].split(":")[0] for s in secim))
    print("şirket × durum:", Counter((s["sirket"], s["durum"].split(":")[0]) for s in secim))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
