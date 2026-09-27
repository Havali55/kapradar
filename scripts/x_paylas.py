"""Yeni bildirimleri X'te paylaşır. Varsayılan KURU.

Kullanım:
    python scripts/x_paylas.py               # KURU: adaylar + tweet metinleri; göndermez, yazmaz
    python scripts/x_paylas.py --onizle 5    # son 5 bildirimin metni; süzgeçsiz, asla göndermez
    python scripts/x_paylas.py --dogrula     # anahtarlar çalışıyor mu (GET /2/users/me); tweet atmaz
    python scripts/x_paylas.py --gonder      # GERÇEK: paylaşır, x_paylasim tablosuna yazar

Günlük koşu (scripts/gunluk.py) bunu `--x-gonder` verilmedikçe kuru çağırır.

Aday kuralları `kap_radar.x_paylasim` içinde (başlangıç tarihi, yaş
sınırı, büyüklüğü bilinmeyenin atlanması). Her aday için sıra:
  1. Sitedeki sayfası 200 dönmüyorsa atlanır; kayıt yazılmaz, sonraki
     koşu yeniden dener. Tweet'in linki boşa çıkmasın.
  2. Satır "gonderiliyor" olarak yazılıp commit edilir.
  3. Tweet atılır, sonuç satıra yazılır.
İlk hatada koşu durur: anahtar ya da kota sorunu her adaya aynı hatayı verir.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import httpx  # noqa: E402
import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.x_paylasim import (  # noqa: E402
    AZAMI_YAS,
    MAKS_UZUNLUK,
    PAYLASIM_BASLANGICI,
    SITE_KOKU,
    XHatasi,
    XIstemci,
    adaylari_sec,
    anahtarlari_bul,
    tweet_metni,
    x_uzunlugu,
)

ISTANBUL = ZoneInfo("Europe/Istanbul")
METIN_ALANLARI = ("kap_id", "ticker", "ciro_orani", "karsi_taraf", "karsi_taraf_acik")
EKSIK_ANAHTAR = "X anahtarları eksik (.env ya da ortam: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)"


def link_durumu(web: httpx.Client, url: str) -> int:
    try:
        return web.get(url).status_code
    except httpx.HTTPError:
        return 0


def satir_bas(satir: dict, metin: str, ek: str = "") -> None:
    zaman = satir["yayin_zamani"].astimezone(ISTANBUL)
    print(f"\n{satir['ticker']}  {zaman:%d.%m.%Y %H:%M}  uzunluk {x_uzunlugu(metin)}/{MAKS_UZUNLUK}{ek}")
    print(f"  {metin}")


def dogrula() -> int:
    anahtarlar = anahtarlari_bul()
    if not anahtarlar:
        print(EKSIK_ANAHTAR)
        return 1
    x = XIstemci(anahtarlar)
    try:
        kullanici, duzey = x.kimlik()
        print(f"anahtarlar çalışıyor: @{kullanici} · erişim düzeyi: {duzey or 'bilinmiyor'}")
        # "read" düzeyindeki token'la gönderim 403 döner; izin sonradan
        # "Read and write" yapıldıysa token yeniden üretilmeli.
        if not duzey or "write" not in duzey:
            print(
                "YAZMA İZNİ YOK: portalda uygulama izni 'Read and write' yapılıp "
                "Access Token and Secret yeniden üretilmeli; bu anahtarla tweet atılamaz."
            )
            return 1
        return 0
    except XHatasi as h:
        print(f"anahtarlar REDDEDİLDİ: {h}")
        return 1
    finally:
        x.kapat()


def onizle(db: psycopg.Connection, adet: int) -> int:
    satirlar = db.execute(
        "select kap_id, ticker, ciro_orani, karsi_taraf, karsi_taraf_acik, yayin_zamani"
        " from public.akis where ciro_orani > 0 order by yayin_zamani desc limit %s",
        (adet,),
    ).fetchall()
    sutunlar = ("kap_id", "ticker", "ciro_orani", "karsi_taraf", "karsi_taraf_acik", "yayin_zamani")
    for satir in (dict(zip(sutunlar, s)) for s in satirlar):
        satir_bas(satir, tweet_metni(**{k: satir[k] for k in METIN_ALANLARI}))
    print("\nÖNİZLEME: başlangıç/yaş/tekrar süzgeci uygulanmadı, hiçbir şey gönderilmedi.")
    return 0


def paylas(db: psycopg.Connection, *, gonder: bool, adet: int) -> int:
    adaylar = adaylari_sec(db, simdi=datetime.now(timezone.utc), adet=adet)
    print(
        f"aday: {len(adaylar)}  (başlangıç {PAYLASIM_BASLANGICI:%d.%m.%Y}, "
        f"en fazla {AZAMI_YAS.days} günlük, koşu başına en fazla {adet})"
    )

    x = None
    if gonder and adaylar:
        anahtarlar = anahtarlari_bul()
        if not anahtarlar:
            print(EKSIK_ANAHTAR)
            return 1
        x = XIstemci(anahtarlar)

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as web:
            for aday in adaylar:
                metin = tweet_metni(**{k: aday[k] for k in METIN_ALANLARI})
                kod = link_durumu(web, f"{SITE_KOKU}/kap/{aday['kap_id']}")
                satir_bas(aday, metin, f"  link {kod}")
                if x_uzunlugu(metin) > MAKS_UZUNLUK or kod != 200:
                    print("  ATLANDI: metin çok uzun ya da sayfa açılmıyor; sonraki koşu yeniden bakar")
                    continue
                if x is None:
                    continue

                sahiplenildi = db.execute(
                    "insert into public.x_paylasim (kap_id, metin, durum)"
                    " values (%s, %s, 'gonderiliyor') on conflict (kap_id) do nothing returning kap_id",
                    (aday["kap_id"], metin),
                ).fetchone()
                db.commit()
                if not sahiplenildi:
                    print("  ATLANDI: başka bir koşu bu bildirimi zaten aldı")
                    continue

                try:
                    tweet_id = x.gonder(metin)
                except XHatasi as h:
                    db.execute(
                        "update public.x_paylasim set durum = 'hata', hata = %s, guncelleme = now()"
                        " where kap_id = %s",
                        (str(h), aday["kap_id"]),
                    )
                    db.commit()
                    print(f"  HATA: {h}\nkoşu durduruldu")
                    return 1
                except httpx.HTTPError as h:
                    # Cevap gelmedi: tweet atılmış da olabilir. Satır "gonderiliyor"da
                    # kalıyor, yani yeniden denenmeyecek; hesabı elle kontrol et.
                    db.execute(
                        "update public.x_paylasim set hata = %s, guncelleme = now() where kap_id = %s",
                        (f"belirsiz: {h!r}", aday["kap_id"]),
                    )
                    db.commit()
                    print(f"  BELİRSİZ: {h!r} — tweet atılmış olabilir, hesabı kontrol et\nkoşu durduruldu")
                    return 1

                db.execute(
                    "update public.x_paylasim set durum = 'gonderildi', tweet_id = %s, guncelleme = now()"
                    " where kap_id = %s",
                    (tweet_id, aday["kap_id"]),
                )
                db.commit()
                print(f"  GÖNDERİLDİ: https://x.com/i/status/{tweet_id}")
    finally:
        if x is not None:
            x.kapat()

    if not gonder:
        print("\nKURU KOŞU: hiçbir şey gönderilmedi, hiçbir şey yazılmadı. Göndermek için --gonder.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    kip = ap.add_mutually_exclusive_group()
    kip.add_argument("--gonder", action="store_true", help="GERÇEK paylaşım")
    kip.add_argument("--dogrula", action="store_true", help="anahtarları tweet atmadan sına")
    kip.add_argument("--onizle", type=int, metavar="N", help="son N bildirimin metni; göndermez")
    ap.add_argument("--adet", type=int, default=5, help="koşu başına en fazla paylaşım (varsayılan 5)")
    secenek = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    if secenek.dogrula:
        return dogrula()

    dsn = dsn_bul()
    if not dsn:
        print("DATABASE_URL yok")
        return 1
    with psycopg.connect(dsn) as db:
        if secenek.onizle:
            return onizle(db, secenek.onizle)
        return paylas(db, gonder=secenek.gonder, adet=secenek.adet)


if __name__ == "__main__":
    raise SystemExit(main())
