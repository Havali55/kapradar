"""Seçim öncesi rejim sınaması için ücretsiz arşiv katmanı (2020-01 → 2024-08).

Kullanım:
    python scripts/rejim_arsivi.py kap      # KAP bildirim listesi 2020-01-01 → 2023-08-31
    python scripts/rejim_arsivi.py bulten   # Borsa İstanbul günlük pay piyasası bültenleri
    python scripts/rejim_arsivi.py rapor    # yeni iş sayısı, çıkarım bütçesi, aylık işlem hacmi

LLM yok, ücret yok. İki kaynak da kimliksiz ve herkese açık:

  - KAP liste API'si (`istemci.py`: oturum ısıtması, Referer, dürüst
    User-Agent). Yalnız LİSTE çekilir: tarih, şirket, konu, özet, indeks.
    Bildirim detayı (tutarın geçtiği metin) ücretli katmanın girdisi;
    maliyeti `rapor` söylüyor, onay gelmeden çekilmez.
  - Borsa İstanbul günlük pay piyasası bülteni
    (borsaistanbul.com/data/thb/YYYY/AA/thbYYYYAAGG1.zip): her pay için
    resmî TL işlem hacmi. yfinance'in endeks hacmi kullanılamaz (2020'de
    endeks sadeleşmesiyle 60 katlık kırılma, pay adedi, TL değil).

Arşiv `data/ham_rejim/` altında, `data/ham/`'dan ayrı: canlı hattın bağlam
hesabı ve CI önbelleği o klasörü okuyor; 2020 listeleri oraya girerse
günlük koşunun sayımları ve önbellek boyutu değişirdi. Kaldığı yerden
devam eder: arşivdeki pencere ve bülten yeniden istenmez.

Rejim sınırları (TCMB PPK; kaynak docs/arastirma/2026-09-27-gecerlilik-degerlendirmesi.md):
  gevşek para 2019-07 → 2023-05 · sıkılaştırma 2023-06 → 2024-12 · kademeli indirim 2025-01 →
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import httpx  # noqa: E402

from kap_radar import tufe  # noqa: E402
from kap_radar.arsiv import HamArsiv  # noqa: E402
from kap_radar.ayarlar import env_oku  # noqa: E402
from kap_radar.backfill import (  # noqa: E402
    YENI_IS_ILISKISI,
    BackfillOzeti,
    haftalik_pencereler,
    pencere_kayitlari,
)
from kap_radar.http_temel import VARSAYILAN_USER_AGENT  # noqa: E402
from kap_radar.istemci import KapErisimHatasi, KapIstemcisi  # noqa: E402

REJIM_KOK = KOK / "data" / "ham_rejim"
CANLI_KOK = KOK / "data" / "ham"
KAP_BAS, KAP_SON = date(2020, 1, 1), date(2023, 8, 31)
# Canlı arşiv 2023-09'dan başlıyor; rejim sınamasının geri kalanı oradan.
RAPOR_SON = date(2024, 8, 31)
BULTEN_BAS = date(2020, 1, 2)
BULTEN_URL = "https://www.borsaistanbul.com/data/thb/{y}/{a:02d}/thb{y}{a:02d}{g:02d}1.zip"
BULTEN_ARALIK_SN = 0.5
REJIMLER = (
    ("gevşek para", date(2020, 1, 1), date(2023, 5, 31)),
    ("sıkılaştırma", date(2023, 6, 1), date(2024, 12, 31)),
    ("kademeli indirim", date(2025, 1, 1), date(2026, 12, 31)),
)
# Çıkarım bütçesi, veritabanındaki gerçek çıkarımlardan (cikarim.girdi_token,
# cikti_token; 2026-09-27): flash-lite 1.382 çıkarım, ortalama 1.418 girdi /
# 190 çıktı token; %3,5'i üst modele (3.8-flash, 1.494 / 257) yükseliyor.
# Birim maliyet, 2024-09 backfill'inin faturasından: 690 çıkarım 0,487 USD.
GIRDI_TOKEN, CIKTI_TOKEN, YUKSELME = 1418, 190, 0.035
USD_BILDIRIM = 0.487 / 690
ODA_GENEL = "Özel Durum Açıklaması (Genel)"
SOZLESME_DESENI = re.compile(r"sözleşme|ihale|sipariş|iş ilişkisi|anlaşma|kontrat", re.I)


# Uzun geriye dönük çekimde WAF'a karşı: günlük koşunun 500 ms'si burada
# fazla agresif çıktı (2026-09-27: 100 pencereden sonra blok). En az 2 sn,
# ve üç ardışık pencere hatasında koşu durur; blok soğuyunca aynı komut
# kaldığı yerden devam eder. Bloğa istek yağdırmak onu uzatır.
KAP_ASGARI_ARALIK_MS = 2000
ARDISIK_HATA_SINIRI = 3


def istemci_kur() -> KapIstemcisi:
    env = env_oku()
    aralik = max(int(env.get("KAP_ISTEK_ARALIGI_MS", "0")), KAP_ASGARI_ARALIK_MS)
    return KapIstemcisi(
        user_agent=env.get("KAP_USER_AGENT") or VARSAYILAN_USER_AGENT,
        istek_araligi_sn=aralik / 1000,
        maks_deneme=int(env.get("KAP_MAKS_YENIDEN_DENEME", "5")),
    )


# ------------------------------------------------------------------ KAP

def kap_cek() -> int:
    arsiv = HamArsiv(REJIM_KOK)
    ozet = BackfillOzeti()
    istemci = istemci_kur()
    pencereler = haftalik_pencereler(KAP_BAS, KAP_SON, 3)
    print(f"KAP listesi {KAP_BAS} → {KAP_SON}: {len(pencereler)} pencere, arşiv {REJIM_KOK}", flush=True)
    ardisik = 0
    try:
        for i, (bas, son) in enumerate(pencereler, 1):
            try:
                kayitlar = pencere_kayitlari(istemci, arsiv, bas, son, ozet, date.today())
                ardisik = 0
            except KapErisimHatasi as hata:
                ozet.hatali_pencereler.append((bas, son))
                print(f"  PENCERE HATASI {bas} — {son}: {hata}", flush=True)
                ardisik += 1
                if ardisik >= ARDISIK_HATA_SINIRI:
                    print(f"  {ardisik} ardışık hata: WAF bloğu. Koşu durdu; soğuduktan sonra "
                          "aynı komut kaldığı yerden devam eder.", flush=True)
                    break
                continue
            if i % 25 == 0 or i == len(pencereler):
                yeni = sum(1 for k in kayitlar if k.get("subject") == YENI_IS_ILISKISI)
                print(f"  {i}/{len(pencereler)} {bas}: {len(kayitlar)} bildirim, {yeni} yeni iş", flush=True)
    finally:
        istemci.kapat()
    if ozet.hatali_pencereler:
        print(f"ÇEKİLEMEYEN {len(ozet.hatali_pencereler)} pencere; aynı komut yalnız onları dener.")
    if ozet.tasan_pencereler:
        print(f"SINIRA DAYANAN pencereler: {ozet.tasan_pencereler}")
    return 1 if ozet.hatali_pencereler or ozet.tasan_pencereler else 0


def liste_kayitlari() -> list[tuple[datetime, dict]]:
    """Rejim + canlı arşivden 2020-01-01 → 2024-08-31 bütün bildirimler."""
    kayit: dict[int, dict] = {}
    for kok in (REJIM_KOK, CANLI_KOK):
        for yol in sorted((kok / "liste").glob("*.json")):
            for k in json.loads(yol.read_text(encoding="utf-8")):
                kayit[int(k["disclosureIndex"])] = k
    sonuc = []
    for k in kayit.values():
        z = datetime.strptime(k["publishDate"], "%d.%m.%Y %H:%M:%S")
        if KAP_BAS <= z.date() <= RAPOR_SON:
            sonuc.append((z, k))
    return sorted(sonuc, key=lambda s: s[0])


def yeni_is_kayitlari(kayitlar: list[tuple[datetime, dict]]) -> list[dict]:
    return [{"tarih": z, "ticker": (k.get("stockCodes") or "").strip(),
             "unvan": k.get("kapTitle") or "", "ozet": k.get("summary") or "",
             "indeks": int(k["disclosureIndex"])}
            for z, k in kayitlar if k.get("subject") == YENI_IS_ILISKISI]


# --------------------------------------------------------------- bülten

def is_gunleri(bas: date, son: date):
    g = bas
    while g <= son:
        if g.weekday() < 5:
            yield g
        g += timedelta(days=1)


def bulten_yolu(g: date) -> Path:
    return REJIM_KOK / "thb" / str(g.year) / f"thb{g:%Y%m%d}1.zip"


def bulten_cek() -> int:
    env = env_oku()
    ua = env.get("KAP_USER_AGENT") or VARSAYILAN_USER_AGENT
    dun = date.today() - timedelta(days=1)
    gunler = [g for g in is_gunleri(BULTEN_BAS, dun)
              if not bulten_yolu(g).exists() and not bulten_yolu(g).with_suffix(".yok").exists()]
    print(f"Bülten {BULTEN_BAS} → {dun}: {len(gunler)} gün eksik", flush=True)
    hata = 0
    with httpx.Client(headers={"User-Agent": ua}, timeout=30, follow_redirects=True) as c:
        for i, g in enumerate(gunler, 1):
            yol = bulten_yolu(g)
            yol.parent.mkdir(parents=True, exist_ok=True)
            try:
                r = c.get(BULTEN_URL.format(y=g.year, a=g.month, g=g.day))
            except httpx.HTTPError as e:
                hata += 1
                print(f"  {g}: {e}", flush=True)
                time.sleep(5)
                continue
            if r.status_code == 200 and r.content[:2] == b"PK":
                tmp = yol.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                tmp.replace(yol)
            elif r.status_code == 404:
                # Tatil ya da yayın yok; işaretlenmezse her koşu yeniden sorar.
                yol.with_suffix(".yok").touch()
            else:
                hata += 1
                print(f"  {g}: HTTP {r.status_code}", flush=True)
            if i % 100 == 0:
                print(f"  {i}/{len(gunler)} {g}", flush=True)
            time.sleep(BULTEN_ARALIK_SN)
    print(f"bitti; hata {hata} (aynı komut yalnız eksikleri dener)")
    return 1 if hata else 0


def gunluk_hacim(zip_yolu: Path) -> tuple[float, int]:
    """Bültenden pay (EQT) toplam TL işlem hacmi ve işlem gören pay sayısı."""
    z = zipfile.ZipFile(zip_yolu)
    ham = z.read(z.namelist()[0])
    try:
        metin = ham.decode("utf-8")
    except UnicodeDecodeError:
        metin = ham.decode("windows-1254")
    satirlar = csv.reader(io.StringIO(metin), delimiter=";")
    baslik = [b.strip() for b in next(satirlar)]
    next(satirlar)  # İngilizce başlık
    grup, hacim = baslik.index("ENSTRUMAN GRUBU"), baslik.index("TOPLAM ISLEM HACMI")
    toplam, adet = 0.0, 0
    for s in satirlar:
        if len(s) > hacim and s[grup].strip() == "EQT" and s[hacim].strip():
            toplam += float(s[hacim])
            adet += 1
    return toplam, adet


# ---------------------------------------------------------------- rapor

def rapor() -> int:
    # 1. Yeni iş bildirimleri ve çıkarım bütçesi
    tum = liste_kayitlari()
    kayitlar = yeni_is_kayitlari(tum)
    REJIM_KOK.mkdir(parents=True, exist_ok=True)
    with (REJIM_KOK / "yeni_is_2020_2024.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["tarih", "ticker", "unvan", "ozet", "indeks"])
        w.writeheader()
        for k in kayitlar:
            w.writerow({**k, "tarih": k["tarih"].isoformat()})
    yil = Counter(k["tarih"].year for k in kayitlar)
    rejim = Counter(next((ad for ad, b, s in REJIMLER if b <= k["tarih"].date() <= s), "?")
                    for k in kayitlar)
    kapsam = sorted({k["tarih"].date().replace(day=1) for k in kayitlar})
    print(f"YENİ İŞ İLİŞKİSİ {KAP_BAS} → {RAPOR_SON}: {len(kayitlar)} bildirim, "
          f"{len({k['ticker'] for k in kayitlar})} şirket kodu")
    print("  yıl   :", dict(sorted(yil.items())))
    print("  rejim :", dict(rejim))
    if kapsam:
        print(f"  arşiv kapsamı: {kapsam[0]:%Y-%m} → {kapsam[-1]:%Y-%m} ({len(kapsam)} ay)")
    n = len(kayitlar)
    girdi = n * GIRDI_TOKEN * (1 + YUKSELME)
    cikti = n * CIKTI_TOKEN * (1 + YUKSELME)
    print(f"  çıkarım bütçesi: ~{girdi/1e6:.2f} M girdi + ~{cikti/1e6:.2f} M çıktı token, "
          f"~{n * USD_BILDIRIM:.2f} USD (bildirim başına {USD_BILDIRIM:.5f} USD, 2024-09 faturası)")
    print("  not: detay çekimi (metin) ücretsiz ama yapılmadı; bütçe yalnız LLM çıkarımı.")

    # Şablon kullanımı yıllar içinde değişti: 2020'de yeni işlerin çoğu
    # "Özel Durum Açıklaması (Genel)" ile duyuruluyordu. Yalnız şablonla
    # kurulan bir karşılaştırma rejim farkını duyuru alışkanlığı farkıyla
    # karıştırır; ÖDA'daki sözleşme duyurularını da almak ek sınıflama ister.
    oda = [(z, k) for z, k in tum if k.get("subject") == ODA_GENEL]
    oda_soz = [(z, k) for z, k in oda if SOZLESME_DESENI.search(k.get("summary") or "")]
    kapsanan_ay = defaultdict(set)
    for z, _ in tum:
        kapsanan_ay[z.year].add(z.month)
    print()
    print(f"  {'yıl':<6}{'arşivli ay':>11}{'yeni iş':>9}{'ÖDA genel':>11}{'ÖDA özetinde sözleşme/ihale':>29}")
    for y in sorted(kapsanan_ay):
        print(f"  {y:<6}{len(kapsanan_ay[y]):>11}{sum(1 for k in kayitlar if k['tarih'].year == y):>9}"
              f"{sum(1 for z, _ in oda if z.year == y):>11}{sum(1 for z, _ in oda_soz if z.year == y):>29}")
    print(f"  bütçe B (ÖDA'daki sözleşme/ihale özetleri de sınıflanırsa): +{len(oda_soz)} bildirim, "
          f"~{len(oda_soz) * USD_BILDIRIM:.2f} USD; özet deseni kaba (toplu iş sözleşmesi gibi "
          "gürültü içerir), gerçek sayı sınıflamadan sonra belli olur.")

    # 2. Aylık işlem hacmi
    gunluk = {}
    for yol in sorted((REJIM_KOK / "thb").glob("*/*.zip")):
        g = datetime.strptime(yol.stem[3:11], "%Y%m%d").date()
        try:
            gunluk[g] = gunluk_hacim(yol)
        except (zipfile.BadZipFile, ValueError, StopIteration) as e:
            print(f"  okunamadı {yol.name}: {e}")
    if not gunluk:
        print("\nBülten arşivi boş: önce `bulten`.")
        return 0
    usd = _usd_kurlari(min(gunluk), max(gunluk))
    aylik = defaultdict(lambda: [0.0, 0, 0.0])  # TL, gün, USD
    for g, (tl, _) in gunluk.items():
        a = aylik[g.replace(day=1)]
        a[0] += tl
        a[1] += 1
        if g in usd:
            a[2] += tl / usd[g]
    son_ay = max(aylik)
    tufe_son = date(2026, 8, 31)
    with (REJIM_KOK / "aylik_hacim.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ay", "gun", "tl_toplam", "tl_gunluk", "reel_gunluk_2026_08", "usd_gunluk"])
        for ay in sorted(aylik):
            tl, gun, dl = aylik[ay]
            o = tufe.oran(ay, tufe_son)
            w.writerow([f"{ay:%Y-%m}", gun, round(tl), round(tl / gun),
                        round(tl / gun * float(o)) if o else "", round(dl / gun) if dl else ""])
    print(f"\nPAY PİYASASI İŞLEM HACMİ (bülten, {min(gunluk)} → {max(gunluk)}, {len(gunluk)} gün)")
    print(f"  {'dönem':<22}{'gün':>5}{'günlük TL (mr)':>16}{'reel, Ağu 2026 TL':>19}{'günlük USD (mn)':>17}")
    for ad, b, s in REJIMLER:
        gunler = [g for g in gunluk if b <= g <= s]
        if not gunler:
            continue
        tl = sum(gunluk[g][0] for g in gunler) / len(gunler)
        # TÜFE'si henüz yayımlanmamış aylar reel ortalamaya girmez; 0 sayılsa
        # ortalamayı sahte biçimde düşürürdü.
        reel_gunler = [(g, o) for g in gunler if (o := tufe.oran(g, tufe_son)) is not None]
        reel = sum(gunluk[g][0] * float(o) for g, o in reel_gunler) / max(1, len(reel_gunler))
        dl = [gunluk[g][0] / usd[g] for g in gunler if g in usd]
        print(f"  {ad:<22}{len(gunler):>5}{tl/1e9:>16.1f}{reel/1e9:>19.1f}"
              f"{(sum(dl)/len(dl))/1e6 if dl else float('nan'):>17.0f}")
    print(f"  (aylık tablo: {REJIM_KOK / 'aylik_hacim.csv'}; son ay {son_ay:%Y-%m} yarım olabilir)")
    return 0


def _usd_kurlari(bas: date, son: date) -> dict[date, float]:
    """USD/TRY günlük kapanış (yfinance, ücretsiz)."""
    import yfinance as yf
    d = yf.download("TRY=X", start=bas.isoformat(), end=(son + timedelta(days=1)).isoformat(),
                    progress=False, auto_adjust=False)
    d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
    s = d["Close"].dropna()
    kur = {g.date(): float(v) for g, v in s.items()}
    # Tatilde kur yoksa bir önceki gün.
    sonuc, son_kur = {}, None
    g = bas
    while g <= son:
        son_kur = kur.get(g, son_kur)
        if son_kur:
            sonuc[g] = son_kur
        g += timedelta(days=1)
    return sonuc


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("komut", choices=("kap", "bulten", "rapor"))
    komut = ap.parse_args().komut
    return {"kap": kap_cek, "bulten": bulten_cek, "rapor": rapor}[komut]()


if __name__ == "__main__":
    raise SystemExit(main())
