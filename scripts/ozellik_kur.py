"""Skor araştırması için özellik matrisi üretir.

Kullanım:  python scripts/ozellik_kur.py

Çıktı: data/ozellikler.csv — her satır bir bildirim, her sütun skorun
adayı olan bir sinyal. Kaynaklar:
  - `bildirim` + `tepki` + `fiyat_gunluk` (veritabanı)
  - `data/ham/liste/*.json` — 12 ayın **tüm** KAP bildirimleri (85 bin)

Üçüncü kaynak bu araştırmanın belkemiği: BIST'in "temiz olmayan"
tarafı tahmin edilmiyor, KAP'ın kendi tedbir bildirimlerinden
ölçülüyor. Pay Bazında Devre Kesici (VBTS) bir hissenin volatilite
tedbirine düştüğünü söyler; 12 ayda 14.013 tane var ve dağılımı
tahtanın karakterini doğrudan veriyor.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.depo import Depo  # noqa: E402
from kap_radar.tepki import car_hesapla  # noqa: E402

LISTE_KLASORU = KOK / "data" / "ham" / "liste"
CIKTI = KOK / "data" / "ozellikler.csv"

VBTS_KONUSU = "Pay Bazında Devre Kesici Bildirimi"
ICERIDEN_KONUSU = "Pay Alım Satım Bildirimi"
GERI_ALIM_KONUSU = "Payların Geri Alınmasına İlişkin Bildirim"

# Spekülasyon yoğunluğu penceresi: bildirimden önceki 90 takvim günü.
GECMIS_PENCERE = 90
# Sızıntı/iz penceresi: bildirimin hemen öncesi.
YAKIN_PENCERE = 5


def env_oku(yol: Path) -> dict[str, str]:
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def kap_takvimi() -> dict[tuple[str, str], list[date]]:
    """(ticker, konu) -> o bildirimin düştüğü günler.

    Liste arşivi pencere pencere kaydedildiği için aynı bildirim birden
    çok dosyada görünebilir; `disclosureIndex` ile tekilleştiriliyor.
    """
    gorulen: set[int] = set()
    takvim: dict[tuple[str, str], list[date]] = defaultdict(list)

    for yol in sorted(LISTE_KLASORU.glob("*.json")):
        for kayit in json.loads(yol.read_text(encoding="utf-8")):
            indeks = kayit.get("disclosureIndex")
            if indeks in gorulen:
                continue
            gorulen.add(indeks)

            konu = (kayit.get("subject") or "").strip()
            ham_tarih = (kayit.get("publishDate") or "")[:10]
            if not ham_tarih:
                continue
            gun, ay, yil = ham_tarih.split(".")
            gun_tarihi = date(int(yil), int(ay), int(gun))

            # İki alan birden gerekiyor. Devre kesiciyi Borsa İstanbul
            # yayınlıyor, yani `stockCodes` boş ve etkilenen pay
            # `relatedStocks`ta duruyor. Pay Alım Satım'da ise ikisi
            # farklı şeyi gösteriyor: bildiren şirket ve işlem gören pay.
            kodlar = f"{kayit.get('stockCodes') or ''},{kayit.get('relatedStocks') or ''}"
            for ticker in {t.strip() for t in kodlar.split(",") if t.strip()}:
                takvim[(ticker, konu)].append(gun_tarihi)

    return takvim


def aralikta_say(gunler: list[date], bitis: date, gun_sayisi: int) -> int:
    alt = bitis - timedelta(days=gun_sayisi)
    return sum(1 for g in gunler if alt <= g <= bitis)


# --- kaba tutar çıkarımı -------------------------------------------------
# LLM çıkarımı Adım 12'de; buradaki regex yalnızca araştırma için bir
# büyüklük vekili üretiyor. Kapıdan geçmiş bir sayı değil, o yüzden
# hiçbir yerde yayınlanmaz.
_SAYI = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?"
_PARA_ESLEME = {
    "TL": "TRY", "TRY": "TRY", "₺": "TRY",
    "USD": "USD", "DOLAR": "USD", "$": "USD",
    "EUR": "EUR", "EURO": "EUR", "AVRO": "EUR", "€": "EUR",
}
TUTAR_KALIBI = re.compile(
    rf"({_SAYI})\s*(?:\+\s*KDV\s*)?(TL|TRY|USD|EUR|EURO|AVRO|ABD Dolar\w*|Dolar|₺|\$|€)",
    re.IGNORECASE,
)


def tutarlari_bul(metin: str) -> list[tuple[float, str]]:
    """Metindeki (değer, para birimi) çiftlerini kabaca çıkarır."""
    bulunan = []
    for ham_sayi, ham_para in TUTAR_KALIBI.findall(metin or ""):
        try:
            deger = float(ham_sayi.replace(".", "").replace(",", "."))
        except ValueError:
            continue
        anahtar = ham_para.upper().replace("ABD DOLARI", "USD").replace("ABD DOLAR", "USD")
        kod = _PARA_ESLEME.get(anahtar, "TRY" if "TL" in anahtar else None)
        if kod:
            bulunan.append((deger, kod))
    return bulunan


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dsn = env_oku(KOK / ".env")["DATABASE_URL"]

    print("KAP takvimi kuruluyor (85 bin bildirim)...", flush=True)
    takvim = kap_takvimi()
    print(f"  {len(takvim)} (ticker, konu) çifti\n", flush=True)

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute("select min(tarih), max(tarih) from public.endeks_gunluk")
            ilk, son = imlec.fetchone()
            imlec.execute(
                """
                select b.kap_id, b.ticker, b.yayin_zamani, b.guncelleme_mi,
                       b.duzeltme_mi, b.ham_metin_tr,
                       b.kap_alanlari->>'karsi_taraf'          as karsi_taraf,
                       b.kap_alanlari->>'karsi_taraf_niteligi' as nitelik,
                       b.kap_alanlari->>'sozlesme_kosullari'   as kosullar,
                       b.ek_sayisi,
                       t.car_1g, t.car_3g, t.car_5g, t.t0
                from public.bildirim b
                join public.tepki t on t.kap_id = b.kap_id
                where b.ticker is not null
                order by b.yayin_zamani
                """
            )
            bildirimler = imlec.fetchall()

        endeks = depo.endeks_serisi(ilk, son)
        seriler: dict[str, dict] = {}
        cirolar: dict[str, float] = {}

        with baglanti.cursor() as imlec:
            imlec.execute(
                "select ticker, "
                "percentile_cont(0.5) within group "
                "  (order by kapanis_duzeltilmis * hacim), "
                "percentile_cont(0.5) within group (order by kapanis_duzeltilmis) "
                "from public.fiyat_gunluk group by ticker"
            )
            for ticker, ciro, fiyat in imlec.fetchall():
                cirolar[ticker] = float(ciro or 0)

        satirlar = []
        for (
            kap_id, ticker, yayin, guncelleme, duzeltme, metin,
            karsi_taraf, nitelik, kosullar, ek_sayisi,
            car_1g, car_3g, car_5g, t0,
        ) in bildirimler:
            if ticker not in seriler:
                seriler[ticker] = depo.fiyat_serisi(ticker, ilk, son)
            seri = seriler[ticker]
            yayin_gunu = yayin.date()

            oncesi = car_hesapla(seri, endeks, t0, pencere=(-5, -1)) if t0 else None
            uzun_oncesi = car_hesapla(seri, endeks, t0, pencere=(-20, -6)) if t0 else None
            car_10g = car_hesapla(seri, endeks, t0, pencere=(0, 9)) if t0 else None
            car_20g = car_hesapla(seri, endeks, t0, pencere=(0, 19)) if t0 else None

            # Kaba tutar: metindeki en büyük kalem, bildirim tarihli
            # TCMB kuruyla TL'ye çevrilmiş. Skora değil araştırmaya girer.
            tutar_tl = 0.0
            for deger, para in tutarlari_bul(metin):
                if para == "TRY":
                    tutar_tl = max(tutar_tl, deger)
                    continue
                kur = depo.kur_coz(yayin_gunu, para)
                if kur:
                    tutar_tl = max(tutar_tl, deger * float(kur[1]))

            vbts = takvim.get((ticker, VBTS_KONUSU), [])
            iceriden = takvim.get((ticker, ICERIDEN_KONUSU), [])
            geri_alim = takvim.get((ticker, GERI_ALIM_KONUSU), [])

            satirlar.append(
                {
                    "kap_id": kap_id,
                    "ticker": ticker,
                    "tarih": yayin_gunu.isoformat(),
                    "t0": t0.isoformat() if t0 else "",
                    "gunluk_ciro": round(cirolar.get(ticker, 0)),
                    "guncelleme": int(bool(guncelleme)),
                    "duzeltme": int(bool(duzeltme)),
                    "karsi_taraf_acik": int(karsi_taraf is not None),
                    "nitelik": (nitelik or "").split("(")[0].strip(),
                    "kosul_acik": int(bool(kosullar)),
                    "ek_sayisi": ek_sayisi or 0,
                    "metin_uzunluk": len(metin or ""),
                    "tutar_var": int(tutar_tl > 0),
                    "tutar_tl": round(tutar_tl),
                    "tutar_ciro_kat": round(
                        tutar_tl / cirolar[ticker], 3
                    ) if cirolar.get(ticker) else "",
                    # Spekülasyon yoğunluğu: son 90 günde kaç kez tedbire düşmüş
                    "vbts_90g": aralikta_say(vbts, yayin_gunu, GECMIS_PENCERE),
                    "vbts_yakin": aralikta_say(vbts, yayin_gunu, YAKIN_PENCERE),
                    "iceriden_90g": aralikta_say(iceriden, yayin_gunu, GECMIS_PENCERE),
                    "iceriden_yakin": aralikta_say(iceriden, yayin_gunu, YAKIN_PENCERE),
                    "geri_alim_90g": aralikta_say(geri_alim, yayin_gunu, GECMIS_PENCERE),
                    "oncesi_5g": float(oncesi) if oncesi is not None else "",
                    "oncesi_20g": float(uzun_oncesi) if uzun_oncesi is not None else "",
                    "car_1g": float(car_1g) if car_1g is not None else "",
                    "car_3g": float(car_3g) if car_3g is not None else "",
                    "car_5g": float(car_5g) if car_5g is not None else "",
                    "car_10g": float(car_10g) if car_10g is not None else "",
                    "car_20g": float(car_20g) if car_20g is not None else "",
                }
            )

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with CIKTI.open("w", encoding="utf-8", newline="") as dosya:
        yazici = csv.DictWriter(dosya, fieldnames=list(satirlar[0]))
        yazici.writeheader()
        yazici.writerows(satirlar)

    print(f"{len(satirlar)} satır -> {CIKTI}")
    vbts_dolu = sum(1 for s in satirlar if s["vbts_90g"] > 0)
    print(f"  son 90 günde VBTS görmüş bildirim : {vbts_dolu}")
    print(f"  bildirimden 5 gün önce VBTS       : {sum(1 for s in satirlar if s['vbts_yakin'])}")
    print(f"  5 gün içinde içeriden işlem       : {sum(1 for s in satirlar if s['iceriden_yakin'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
