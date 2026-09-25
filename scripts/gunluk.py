"""Canlı koşu (Adım 15): son günlerin bildirimlerini uçtan uca işler.

Kullanım:
    python scripts/gunluk.py                 # LLM'siz: her şey, çıkarım hariç
    python scripts/gunluk.py --llm           # ücretli çıkarım dahil (~0,0001 USD/bildirim)
    python scripts/gunluk.py --llm --adet 5  # çıkarım üst sınırı

Yeni bir hat yazmıyor; backfill için yazılmış betikleri kısa aralıklarla
sırayla çağırıyor. Her biri idempotent ve kaldığı yerden devam ediyor,
bu yüzden aynı günü iki kez koşmak zararsız. Sıra bağımlılıklardan:

    liste+detay → DB → kur → finansal → fiyat → faktör → VBTS
    → çıkarım (LLM) → tepki → bağlam

Bir adım düşerse sonrakiler yine denenir (fiyat düşmesi çıkarımı
engellememeli) ama koşu sıfırdan farklı kodla biter; CI kırmızı görünür.

Fiyat DÜNE kadar çekiliyor: `Depo.fiyat_kaydet` var olan güne dokunmuyor.
Seans içinde gelen yarım kapanış yazılırsa kalıcı olurdu.

Arşiv (`data/ham/`) CI'da önbellekten geri yükleniyor. Önbellek yoksa
(ilk koşu ya da GitHub'ın 7 günlük tahliyesi) SOĞUK BAŞLANGIÇ: arşiv
önce tam aralıkla yeniden kuruluyor. Bu atlanırsa bağlam hesabı yalnız
son haftanın listesini görür ve veritabanındaki tahta/sıklık değerlerini
eksik sayımlarla ezer. Soğuk başlangıç KAP'a ~2 saat bedava istek.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import psycopg

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from kap_radar.ayarlar import dsn_bul  # noqa: E402

# Canlı koşunun geriye baktığı gün sayısı. Tek bir koşu kaçarsa (CI
# kesintisi, hafta sonu) sonraki koşu açığı kapatsın diye bir haftalık.
GERI_GUN = 7
# Yeni bir hissenin ilk bildirimi: piyasa modeli t0'dan önce 120 işlem
# günü istiyor, kısa aralıklı fiyat çekimi ona yetmez.
TAM_GECMIS_BASI = date(2024, 1, 1)
# Arşivin kurulduğu aralığın başları. Bildirimler 2024-09'dan; liste ve
# finansal raporlar bir yıl önceden (12 aylık sıklık sayımı ve TTM'in
# yıllık bacağı bildirimden ÖNCEKİ yılı istiyor).
BILDIRIM_BASI = date(2024, 9, 1)
LISTE_BASI = date(2023, 9, 1)
LISTE = KOK / "data" / "ham" / "liste"
# Soğuk başlangıç bütünüyle bitince yazılan işaret. Dosya adlarına bakmak
# yetmiyor: yarıda kesilen kurulum da ilk pencereyi yazmış olur ve sonraki
# koşu delikli arşivi tam sanardı. Önbellekle birlikte taşınıyor.
TAM_ISARETI = LISTE / ".tam"


def arsiv_sicak() -> bool:
    return TAM_ISARETI.exists()


def adim(ad: str, komut: list[str], hatalar: list[str]) -> None:
    print(f"\n=== {ad} ===", flush=True)
    bas = time.monotonic()
    sonuc = subprocess.run([sys.executable, *komut], cwd=KOK)
    sure = time.monotonic() - bas
    if sonuc.returncode != 0:
        hatalar.append(ad)
        print(f"--- {ad}: HATA (kod {sonuc.returncode}, {sure:.0f} sn)", flush=True)
    else:
        print(f"--- {ad}: tamam ({sure:.0f} sn)", flush=True)


def gecmissiz_hisseler() -> list[str]:
    """Bildirimi olup fiyat geçmişi piyasa modeline yetmeyen hisseler."""
    dsn = dsn_bul()
    if dsn is None:
        return []
    with psycopg.connect(dsn, connect_timeout=20) as baglanti, baglanti.cursor() as imlec:
        imlec.execute(
            """
            select b.ticker
            from (select distinct ticker from public.bildirim where ticker is not null) b
            left join (select ticker, min(tarih) ilk from public.fiyat_gunluk group by 1) f
              using (ticker)
            where f.ilk is null or f.ilk > %s
            order by 1
            """,
            (TAM_GECMIS_BASI + timedelta(days=30),),
        )
        return [s[0] for s in imlec.fetchall()]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--llm", action="store_true", help="ÜCRETLİ çıkarımı da koş")
    ap.add_argument("--adet", type=int, default=30, help="çıkarım üst sınırı")
    ap.add_argument("--geri-gun", type=int, default=GERI_GUN)
    secenek = ap.parse_args()

    bugun = date.today()
    bas = (bugun - timedelta(days=secenek.geri_gun)).isoformat()
    dun = (bugun - timedelta(days=1)).isoformat()
    hatalar: list[str] = []

    if not arsiv_sicak():
        print("SOĞUK BAŞLANGIÇ: liste arşivi eksik, tam aralık kuruluyor", flush=True)
        adim("soğuk: bildirim arşivi", ["scripts/backfill_calistir.py", "--baslangic",
                                         BILDIRIM_BASI.isoformat(), "--bitis", bas,
                                         "--pencere", "3"], hatalar)
        adim("soğuk: liste + finansal arşivi", ["scripts/finansal_cek.py", "--baslangic",
                                                 LISTE_BASI.isoformat(), "--bitis", bas], hatalar)
        if hatalar:
            # Yarım arşivle devam etmek bağlam değerlerini bozar; dur. Önbellek
            # yine kaydediliyor, sonraki koşu kaldığı yerden sürdürür.
            print("soğuk başlangıç tamamlanamadı, koşu durduruldu", flush=True)
            return 1
        TAM_ISARETI.write_text(f"{LISTE_BASI} {date.today()}\n")

    adim("KAP liste + detay", ["scripts/backfill_calistir.py", "--baslangic", bas,
                               "--bitis", bugun.isoformat(), "--pencere", "3"], hatalar)
    adim("bildirimler -> DB", ["scripts/yukle.py"], hatalar)
    adim("karşı taraf sınıflaması", ["scripts/karsi_taraf_isaretle.py", "--yaz"], hatalar)
    adim("TCMB kuru", ["scripts/kur_cek.py"], hatalar)
    adim("finansal raporlar", ["scripts/finansal_cek.py", "--baslangic", bas], hatalar)
    adim("finansal -> DB", ["scripts/finansal_yukle.py"], hatalar)

    yeni = gecmissiz_hisseler()
    if yeni:
        komut = ["scripts/fiyat_cek.py", "--baslangic", TAM_GECMIS_BASI.isoformat(),
                 "--bitis", dun, "--endeks-atla"]
        for t in yeni:
            komut += ["--ticker", t]
        adim(f"tam fiyat geçmişi ({len(yeni)} yeni hisse)", komut, hatalar)
    adim("fiyat + XU100", ["scripts/fiyat_cek.py", "--baslangic", bas, "--bitis", dun], hatalar)
    adim("eşit ağırlıklı faktör", ["scripts/faktor_kur.py", "--guncelle",
                                   str(secenek.geri_gun + 3), "--yaz"], hatalar)
    adim("VBTS detayları", ["scripts/vbts_cek.py"], hatalar)

    if secenek.llm:
        adim("çıkarım (LLM)", ["scripts/cikarim_kosu.py", "--kaynak", "kalan",
                               "--adet", str(secenek.adet), "--katman2", "--calistir"], hatalar)
    else:
        print("\n=== çıkarım atlandı (--llm verilmedi) ===")

    adim("tepki (CAR)", ["scripts/tepki_hesapla.py"], hatalar)
    adim("tahta + sıklık", ["scripts/baglam_hesapla.py"], hatalar)

    print("\n=== özet ===")
    if hatalar:
        print(f"düşen adımlar: {', '.join(hatalar)}")
        return 1
    print("bütün adımlar tamam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
