"""Bildirimleri LLM'den geçirip doğrulama kapısına sokar (Adım 12–14).

Kullanım:
    python scripts/cikarim_kosu.py --adet 20                # KURU: ne olacağını yaz
    python scripts/cikarim_kosu.py --adet 20 --calistir     # gerçek çağrı, para harcar
    python scripts/cikarim_kosu.py --kaynak altin --adet 50 --katman2 --calistir
    python scripts/cikarim_kosu.py --kaynak kalan --adet 200 --katman2 --calistir

**Varsayılan kuru koşudur.** `--calistir` verilmeden tek bir ücretli
çağrı yapılmaz; kazara harcama mümkün değil. Kuru koşu ölçülmüş
karakter sayılarından maliyet tahmini basar.

`--kaynak altin` seçilirse çıkarımlar elle etiketlenmiş altın kümeyle
karşılaştırılır (Adım 13): doğruluk ölçümünün referansı orası.

`--kaynak kalan` yalnızca **hiç çıkarımı olmayan** bildirimleri seçer;
yarıda kesilen koşuyu para harcamadan sürdürmenin tek doğru yolu budur.
`--kaynak ilk` kaldığı yeri bilmez, yeniden koşarsa çıkarılmış olanları
ikinci kez ücretlendirir. Offset ile de yapılmaz: eksikler bitişik
olmak zorunda değil (pilot koşusu kuyruğun ortasında delik bırakmıştı).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.karsi_taraf import karsi_taraf_acik  # noqa: E402
from kap_radar.ayarlar import dsn_bul, env_oku  # noqa: E402
from kap_radar.cikarim import katmanli_cikar, prompt_kur  # noqa: E402
from kap_radar.degerlendirme import degerlendir_bildirim  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.dogruluk import karsilastir, ozetle  # noqa: E402
from kap_radar.gemini import GeminiCikarici, GeminiHatasi  # noqa: E402

VARSAYILAN_KUME = KOK / "data" / "altin_kume.json"

# USD / 1M token (Eylül 2026). 3.8 Flash'ın tanıtım fiyatı 31.12.2026'da
# bitiyor ve ikiye katlanıyor; tablo o zaman güncellenmeli.
FIYATLAR: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-3.1-flash-lite": (Decimal("0.25"), Decimal("1.50")),
    "gemini-3.8-flash": (Decimal("0.75"), Decimal("3.75")),
}

# Türkçe metinde ölçülen yaklaşık oran; yalnız KURU koşu tahmininde
# kullanılıyor. Gerçek koşuda sağlayıcının bildirdiği sayı yazılıyor.
KARAKTER_BASINA_TOKEN = Decimal("3")

# Bildirim başına ortalama çıktı tokeni (2026-09-20 pilotunda ölçüldü).
ORTALAMA_CIKTI_TOKEN = 184


ALANLAR = (
    "kap_id, ticker, ham_metin_tr, yayin_zamani, guncelleme_mi, "
    "kap_alanlari->>'karsi_taraf' as karsi_taraf"
)


def bildirimleri_sec(baglanti, kaynak: str, adet: int) -> list[tuple]:
    """Kapı ve §8 hesabı için gereken her alanı birlikte getirir."""
    with baglanti.cursor() as imlec:
        if kaynak == "altin":
            kap_idler = [
                k["kap_id"]
                for k in json.loads(VARSAYILAN_KUME.read_text(encoding="utf-8"))[
                    "kayitlar"
                ]
            ]
            imlec.execute(
                f"select {ALANLAR} from public.bildirim "
                "where kap_id = any(%s) order by yayin_zamani limit %s",
                (kap_idler, adet),
            )
        elif kaynak == "kalan":
            # Çıkarımı olmayanlar. Yarıda kesilen koşuyu sürdürmenin tek
            # güvenli yolu: seçim DB'nin gerçek durumuna bakıyor, sayaca
            # değil. Zaten çıkarılmış bir bildirim ikinci kez ücretli
            # çağrılamaz.
            imlec.execute(
                f"select {ALANLAR} from public.bildirim b "
                "where ham_metin_tr is not null and ham_metin_tr <> '' "
                "and not exists ("
                "  select 1 from public.cikarim c where c.kap_id = b.kap_id"
                ") order by yayin_zamani limit %s",
                (adet,),
            )
        else:
            # Deterministik: aynı komut aynı bildirimleri seçsin ki iki
            # koşu karşılaştırılabilir olsun.
            imlec.execute(
                f"select {ALANLAR} from public.bildirim "
                "where ham_metin_tr is not null and ham_metin_tr <> '' "
                "order by yayin_zamani limit %s",
                (adet,),
            )
        return imlec.fetchall()


def maliyet(model: str, girdi: int, cikti: int) -> Decimal:
    girdi_fiyat, cikti_fiyat = FIYATLAR.get(model, (Decimal("0"), Decimal("0")))
    return (
        Decimal(girdi) * girdi_fiyat + Decimal(cikti) * cikti_fiyat
    ) / Decimal("1000000")


def kuru_kosu(bildirimler: list[tuple], model: str) -> None:
    """Hiç çağrı yapmadan maliyeti tahmin eder."""
    karakter = sum(len(prompt_kur(b[2] or "")) for b in bildirimler)
    girdi = int(Decimal(karakter) / KARAKTER_BASINA_TOKEN)
    # Pilot koşusunda ölçülen gerçek ortalama. İlk tahmin 110'du ve
    # maliyeti %20 düşük gösterdi.
    cikti = len(bildirimler) * ORTALAMA_CIKTI_TOKEN

    print("\n--- KURU KOSU (hicbir cagri yapilmadi) ---")
    print(f"bildirim      : {len(bildirimler)}")
    print(f"prompt karakteri: {karakter:,}")
    print(f"tahmini girdi : {girdi:,} token")
    print(f"tahmini cikti : {cikti:,} token")
    print(f"tahmini tutar : ${maliyet(model, girdi, cikti):.4f}  ({model})")
    print("\nGercekten kosmak icin --calistir ekle.")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="LLM çıkarım koşusu")
    ayristirici.add_argument(
        "--kaynak", choices=("altin", "ilk", "kalan"), default="ilk"
    )
    ayristirici.add_argument("--adet", type=int, default=20)
    ayristirici.add_argument("--katman2", action="store_true")
    ayristirici.add_argument(
        "--calistir",
        action="store_true",
        help="ÜCRETLİ çağrı yapar. Verilmezse yalnızca tahmin basılır.",
    )
    secenek = ayristirici.parse_args()

    env = env_oku(KOK / ".env")
    anahtar = env.get("GEMINI_API_KEY", "")
    katman1_model = env.get("GEMINI_KATMAN1_MODEL", "gemini-3.1-flash-lite")
    katman2_model = env.get("GEMINI_KATMAN2_MODEL", "gemini-3.8-flash")

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        bildirimler = bildirimleri_sec(baglanti, secenek.kaynak, secenek.adet)
        print(f"kaynak   : {secenek.kaynak} ({len(bildirimler)} bildirim)")
        print(f"katman 1 : {katman1_model}")
        print(f"katman 2 : {katman2_model if secenek.katman2 else '(kapalı)'}")

        if not secenek.calistir:
            kuru_kosu(bildirimler, katman1_model)
            return 0

        if not anahtar or "<" in anahtar:
            print("GEMINI_API_KEY boş ya da yer tutucu", file=sys.stderr)
            return 1

        cikaricilar = [
            GeminiCikarici(api_anahtari=anahtar, model=katman1_model, katman=1)
        ]
        if secenek.katman2:
            cikaricilar.append(
                GeminiCikarici(api_anahtari=anahtar, model=katman2_model, katman=2)
            )

        depo = Depo(baglanti)
        kararlar: Counter = Counter()
        redler: Counter = Counter()
        token: Counter = Counter()
        cikarimlar: dict[str, object] = {}
        hatalar: list[str] = []

        try:
            for sira, satir in enumerate(bildirimler, start=1):
                kap_id, ticker, metin, an, guncelleme_mi, karsi_taraf = satir
                try:
                    sonuc = katmanli_cikar(metin, cikaricilar)
                except GeminiHatasi as hata:
                    hatalar.append(f"{ticker} {kap_id[:8]}: {hata}")
                    continue

                if sonuc.meta:
                    token[f"{sonuc.meta.model}|girdi"] += sonuc.meta.girdi_token or 0
                    token[f"{sonuc.meta.model}|cikti"] += sonuc.meta.cikti_token or 0

                if sonuc.cikarim is None or sonuc.meta is None:
                    continue

                # Aşama B, §8 hesapları koştuktan sonra. Koşucu bunu
                # atlarsa B1–B3 hiç devreye girmez ve CWENE 1502725 gibi
                # mükerrer çevrimler yayına çıkar. Zincirin tamamı
                # `degerlendirme.degerlendir_bildirim` içinde: ölçüm
                # betiği de aynı kodu çağırıyor.
                karar = degerlendir_bildirim(
                    depo,
                    cikarim=sonuc.cikarim,
                    ticker=ticker,
                    an=an,
                    ham_metin_tr=metin,
                    guncelleme_mi=bool(guncelleme_mi),
                    karsi_taraf_acik=karsi_taraf_acik(karsi_taraf),
                )

                kararlar[karar.karar.value] += 1
                if karar.red_nedeni:
                    redler[karar.red_nedeni.split(":")[0]] += 1

                depo.cikarim_kaydet(
                    kap_id,
                    cikarim=sonuc.cikarim,
                    meta=sonuc.meta,
                    yayina_hazir=karar.yayina_hazir,
                    red_nedeni=karar.red_nedeni,
                    net_tutar_tl=karar.net_tutar_tl,
                    ciro_orani=karar.ciro_orani,
                    etki_skoru=karar.etki_skoru,
                )
                cikarimlar[kap_id] = sonuc.cikarim
                print(
                    f"  {sira}/{len(bildirimler)} {ticker:7} "
                    f"{karar.karar.value:8} skor={karar.etki_skoru or '-':>5} "
                    f"{karar.red_nedeni or ''}",
                    flush=True,
                )
                # Her satırda commit. 20'de bir commit 2026-09-20'de
                # 18 ücretli çağrıyı çöpe attı: süreç düştüğünde açık
                # işlem geri alındı, para harcanmış ama satır yoktu.
                # Commit'in maliyeti LLM çağrısının yanında görünmez.
                baglanti.commit()
            baglanti.commit()
        finally:
            for c in cikaricilar:
                c.kapat()

    _ozet(kararlar, redler, token, hatalar)
    if secenek.kaynak == "altin":
        _dogruluk(cikarimlar)
    return 0


def _ozet(kararlar, redler, token, hatalar) -> None:
    print("\n--- kapi kararlari ---")
    for karar, adet in kararlar.most_common():
        print(f"  {karar:10} {adet}")
    if redler:
        print("\n--- red nedenleri ---")
        for neden, adet in redler.most_common():
            print(f"  {neden:6} {adet}")
    if hatalar:
        print(f"\n--- HATA ({len(hatalar)}) ---")
        for h in hatalar[:10]:
            print(f"  {h}")

    print("\n--- gercek token ve maliyet ---")
    toplam = Decimal("0")
    for model in sorted({a.split("|")[0] for a in token}):
        girdi = token[f"{model}|girdi"]
        cikti = token[f"{model}|cikti"]
        tutar = maliyet(model, girdi, cikti)
        toplam += tutar
        print(f"  {model:24} girdi={girdi:>8,} cikti={cikti:>7,}  ${tutar:.4f}")
    print(f"  {'TOPLAM':24} {'':>22}  ${toplam:.4f}")


def _dogruluk(cikarimlar: dict) -> None:
    """Çıkarımları elle etiketlenmiş altın kümeyle karşılaştırır (Adım 13).

    Karşılaştırma `kap_radar.dogruluk` içinde: aynı mantık serbest bir
    yeniden ölçüm betiğinden de çağrılıyor ve iki yerde yaşarsa biri
    düzeltilip diğeri unutulur (2026-09-20'de tam bu oldu).
    """
    kume = {
        k["kap_id"]: k
        for k in json.loads(VARSAYILAN_KUME.read_text(encoding="utf-8"))["kayitlar"]
    }
    sonuclar = [
        karsilastir(kume[kap_id]["tutarlar"], cikarim.tutarlar)
        for kap_id, cikarim in cikarimlar.items()
        if kap_id in kume
    ]
    if not sonuclar:
        return

    sayac = ozetle(sonuclar)
    toplam = len(sonuclar)
    print("\n--- altin kumeye gore dogruluk ---")
    print(f"  tam dogru : {sayac['tam']}/{toplam} (%{100 * sayac['tam'] / toplam:.1f})")
    print(f"  kismi     : {sayac['kismi']}")
    print(f"  yanlis    : {sayac['yanlis']}")
    print("  ayrinti icin: python scripts/dogruluk_olc.py --ayrinti")


if __name__ == "__main__":
    raise SystemExit(main())
