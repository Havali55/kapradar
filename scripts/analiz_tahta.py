"""Tahta derinliği ve tutar açıklaması, tepkiyi nasıl değiştiriyor?

Kullanım:  python scripts/analiz_tahta.py

Adım 10'un skor ağırlıkları (w1/w2/w3) bu analizle kalibre edilecek;
amaç katsayıyı masa başında uydurmak yerine gerçek dağılıma bakmak.
Girdi tamamen veritabanı: 613 bildirim, 612 tepki, 27.581 kapanış.

İki uyarı okuyucuya:
  - Tutar bilgisi burada **regex tahmini**. LLM çıkarımı Adım 12'de
    devreye giriyor; buradaki "tutar var/yok" ön elemenin kaba hâli.
  - Gruplar arası fark standart hatayla birlikte okunmalı. Günlük
    dalgalanma %6-7, ortalamalar %1'in altında: küçük farklar gürültü.
"""

from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

# Türkçe binlik ayırıcılı sayı ya da "12,5 milyon" kalıbı.
_SAYI = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?\s*(?:milyon|milyar)"
_PARA = r"TL|TRY|USD|EUR|ABD Dolar|Dolar|Euro|Avro|Sterlin"
# Sayı ile para birimi birbirine yakın olmalı; yoksa tarih ve yüzdeler
# de "tutar" sayılır.
TUTAR_KALIBI = re.compile(
    rf"(?:{_SAYI})[^.\n]{{0,40}}?(?:{_PARA})|(?:{_PARA})[^.\n]{{0,40}}?(?:{_SAYI})",
    re.IGNORECASE,
)
GIZLI_KALIBI = re.compile(
    r"ticari sır|rekabet.{0,20}gizli|açıklanmama|paylaşılmama", re.IGNORECASE
)


def env_oku(yol: Path) -> dict[str, str]:
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def ozet(baslik: str, degerler: list[float]) -> str:
    """Ortalama + standart hata; tek başına ortalama yanıltıcı."""
    if not degerler:
        return f"{baslik:28} —"
    n = len(degerler)
    ort = statistics.fmean(degerler)
    std = statistics.stdev(degerler) if n > 1 else 0.0
    sh = std / (n**0.5) if n else 0.0
    med = statistics.median(degerler)
    t = ort / sh if sh else 0.0
    return (
        f"{baslik:28} n={n:4}  ort={ort*100:+6.2f}%  sh=±{sh*100:4.2f}  "
        f"t={t:+5.2f}  medyan={med*100:+6.2f}%"
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dsn = env_oku(KOK / ".env")["DATABASE_URL"]

    with psycopg.connect(dsn, connect_timeout=20) as baglanti, baglanti.cursor() as imlec:
        imlec.execute(
            """
            with ciro as (
              select ticker,
                     percentile_cont(0.5) within group
                       (order by kapanis_duzeltilmis * hacim) as medyan_ciro
              from public.fiyat_gunluk group by ticker
            ),
            grup as (
              select ticker, medyan_ciro, ntile(3) over (order by medyan_ciro) as dilim
              from ciro
            )
            select b.kap_id, b.ticker, g.dilim, g.medyan_ciro,
                   t.car_1g, t.car_3g, t.car_5g, b.guncelleme_mi, b.ham_metin_tr,
                   b.kap_alanlari->>'karsi_taraf' as karsi_taraf
            from public.bildirim b
            join public.tepki t on t.kap_id = b.kap_id
            join grup g on g.ticker = b.ticker
            """
        )
        satirlar = imlec.fetchall()

    kayitlar = []
    for kap_id, ticker, dilim, ciro, c1, c3, c5, guncelleme, metin, karsi in satirlar:
        metin = metin or ""
        kayitlar.append(
            {
                "kap_id": kap_id,
                "ticker": ticker,
                "dilim": dilim,
                "ciro": float(ciro or 0),
                "c1": float(c1) if c1 is not None else None,
                "c3": float(c3) if c3 is not None else None,
                "c5": float(c5) if c5 is not None else None,
                "guncelleme": guncelleme,
                "tutar_var": bool(TUTAR_KALIBI.search(metin)),
                "gizli": bool(GIZLI_KALIBI.search(metin)),
                "karsi_taraf_var": karsi is not None,
            }
        )

    def sec(kosul, alan="c3") -> list[float]:
        return [k[alan] for k in kayitlar if kosul(k) and k[alan] is not None]

    ADLAR = {1: "1 · Sığ tahta", 2: "2 · Orta tahta", 3: "3 · Derin tahta"}

    print("=" * 78)
    print("TAHTA DERİNLİĞİNE GÖRE ANORMAL GETİRİ")
    print("=" * 78)
    for dilim, ad in ADLAR.items():
        grup = [k for k in kayitlar if k["dilim"] == dilim]
        ciro_araligi = sorted(k["ciro"] for k in grup)
        print(
            f"\n{ad}  (medyan günlük ciro "
            f"{ciro_araligi[0]/1e6:.0f}–{ciro_araligi[-1]/1e6:.0f} mn TL)"
        )
        for alan, etiket in (("c1", "1 gün"), ("c3", "3 gün"), ("c5", "5 gün")):
            print("  " + ozet(etiket, sec(lambda k, d=dilim: k["dilim"] == d, alan)))

    print("\n" + "=" * 78)
    print("TUTAR AÇIKLANMIŞ MI? (regex tahmini — LLM değil)")
    print("=" * 78)
    for alan, etiket in (("c1", "1 gün"), ("c3", "3 gün"), ("c5", "5 gün")):
        print("  " + ozet(f"tutar VAR · {etiket}", sec(lambda k: k["tutar_var"], alan)))
        print("  " + ozet(f"tutar YOK · {etiket}", sec(lambda k: not k["tutar_var"], alan)))
    print(
        f"\n  tutar var: {sum(k['tutar_var'] for k in kayitlar)} · "
        f"yok: {sum(not k['tutar_var'] for k in kayitlar)} · "
        f"gizli ifadesi geçen: {sum(k['gizli'] for k in kayitlar)}"
    )

    print("\n" + "=" * 78)
    print("DİĞER KIRILIMLAR")
    print("=" * 78)
    print("  " + ozet("güncelleme bildirimi", sec(lambda k: k["guncelleme"])))
    print("  " + ozet("ilk açıklama", sec(lambda k: not k["guncelleme"])))
    print("  " + ozet("karşı taraf açık", sec(lambda k: k["karsi_taraf_var"])))
    print("  " + ozet("karşı taraf gizli", sec(lambda k: not k["karsi_taraf_var"])))

    print("\n" + "=" * 78)
    print("GERİ VERME (1. günden 3. güne)")
    print("=" * 78)
    for dilim, ad in ADLAR.items():
        fark = [
            k["c3"] - k["c1"]
            for k in kayitlar
            if k["dilim"] == dilim and k["c1"] is not None and k["c3"] is not None
        ]
        print("  " + ozet(ad, fark))

    onay_oncesi(kayitlar, dsn)
    return 0


def onay_oncesi(kayitlar: list[dict], dsn: str) -> None:
    """Bildirimden ÖNCEKİ beş işlem gününün anormal getirisi.

    Olay çalışmasının en kolay kendini kandırdığı yer burası: zaten
    çökmekte olan bir hisseye bildirim denk gelirse CAR bunu bildirimin
    marifeti sanar. Aynı şekilde bildirimden önce koşan bir tahta,
    haberin sızdığını gösterir — ikisi de skorun öğrenmesi gereken şey.
    """
    from kap_radar.depo import Depo
    from kap_radar.tepki import car_hesapla, t0_bul

    print("\n" + "=" * 78)
    print("BİLDİRİM ÖNCESİ SÜRÜKLENME (t0-5 … t0-1)")
    print("=" * 78)

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute("select min(tarih), max(tarih) from public.endeks_gunluk")
            ilk, son = imlec.fetchone()
            imlec.execute(
                "select b.kap_id, b.ticker, b.yayin_zamani from public.bildirim b "
                "join public.tepki t on t.kap_id = b.kap_id where b.ticker is not null"
            )
            satirlar = imlec.fetchall()

        endeks = depo.endeks_serisi(ilk, son)
        seriler: dict[str, dict] = {}
        oncesi: dict[str, float] = {}

        for kap_id, ticker, yayin in satirlar:
            t0 = t0_bul(yayin, endeks)
            if t0 is None:
                continue
            if ticker not in seriler:
                seriler[ticker] = depo.fiyat_serisi(ticker, ilk, son)
            car = car_hesapla(seriler[ticker], endeks, t0, pencere=(-5, -1))
            if car is not None:
                oncesi[kap_id] = float(car)

    kap_ile = {k["ticker"]: k for k in kayitlar}  # yalnızca alan adları için
    del kap_ile

    eslesen = [
        (oncesi[k["kap_id"]], k["c3"])
        for k in kayitlar
        if k.get("kap_id") in oncesi and k["c3"] is not None
    ]
    if not eslesen:
        print("  eşleşen kayıt yok")
        return

    print("  " + ozet("tüm bildirimler · öncesi", [o for o, _ in eslesen]))

    sirali = sorted(eslesen, key=lambda x: x[1])
    dilim = max(len(sirali) // 10, 1)
    print("  " + ozet("en kötü %10 · öncesi", [o for o, _ in sirali[:dilim]]))
    print("  " + ozet("en iyi %10 · öncesi", [o for o, _ in sirali[-dilim:]]))


if __name__ == "__main__":
    raise SystemExit(main())
