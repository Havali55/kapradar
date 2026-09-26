"""Elle kararları (data/elle_duzeltmeler.json) veritabanına uygular.

Kullanım:
    python scripts/elle_duzelt.py          # KURU: ne değişecek, yazmaz
    python scripts/elle_duzelt.py --yaz    # uygular

LLM çağrısı YOK. Her karar için:
  1. bildirimin makine çıkarımı (model != 'elle' olan en son satır) alınır,
  2. karar uygulanır (`elle.elle_veri`),
  3. bugünkü zincirden geçirilir — anlam kapısı atlanır (insan cevapladı),
     aritmetik kapıları koşar; geçmeyen karar yazılmaz,
  4. `cikarim`'a model='elle', katman=3 satırı EKLENİR (tablo append-only;
     LLM satırı silinmez, `akis` en son satırı okur),
  5. `elle_duzeltme`'ye karar ve gerekçe yazılır; site gerekçeyi gösterir.

Tekrar koşmak zararsız: çıkarımı ve gerekçesi değişmemiş karar atlanır.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.cikarim import SEMA_VERSIYON, CikarimMeta  # noqa: E402
from kap_radar.degerlendirme import (  # noqa: E402
    ELLE_MODELI,
    cikarimi_kur,
    degerlendir_bildirim,
)
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.elle import elle_veri, kararlari_oku  # noqa: E402
from kap_radar.karsi_taraf import karsi_taraf_acik  # noqa: E402

DOSYA = KOK / "data" / "elle_duzeltmeler.json"
META = CikarimMeta(
    model=ELLE_MODELI, katman=3, prompt_versiyon="elle", sema_versiyon=SEMA_VERSIYON
)

BILDIRIM = """
select ticker, yayin_zamani, ham_metin_tr, guncelleme_mi,
       kap_alanlari->>'karsi_taraf', kap_alanlari->>'karsi_taraf_niteligi'
from public.bildirim where kap_id = %s
"""
# Makine çıkarımı: elle satırın tabanı. Elle satır üstüne elle satır
# kurulmaz; karar değişirse hep LLM'in orijinaline uygulanır.
MAKINE = """
select veri, ciro_orani from public.cikarim
where kap_id = %s and model <> %s order by id desc limit 1
"""
SON = "select model, veri from public.cikarim where kap_id = %s order by id desc limit 1"
ELLE_KAYIT = """
insert into public.elle_duzeltme (kap_id, karar, neden, cikarim_id)
values (%s, %s, %s, %s)
on conflict (kap_id) do update set karar = excluded.karar,
  neden = excluded.neden, cikarim_id = excluded.cikarim_id, uygulandi_at = now()
"""


def yuzde(oran) -> str:
    return "skorsuz" if oran is None else f"%{float(oran) * 100:.2f}"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yaz", action="store_true", help="veritabanına uygula")
    secenek = ap.parse_args()

    kararlar = kararlari_oku(DOSYA)
    print(f"karar dosyası : {len(kararlar)} karar ({DOSYA.name})")
    print(f"kip           : {'YAZ' if secenek.yaz else 'KURU (yazmaz)'}\n")

    sayac: Counter = Counter()
    with psycopg.connect(dsn_bul(), connect_timeout=30) as baglanti:
        depo = Depo(baglanti)
        for k in kararlar:
            with baglanti.cursor() as imlec:
                imlec.execute(BILDIRIM, (k.kap_id,))
                bildirim = imlec.fetchone()
                imlec.execute(MAKINE, (k.kap_id, ELLE_MODELI))
                makine = imlec.fetchone()
                imlec.execute(SON, (k.kap_id,))
                son = imlec.fetchone()
                imlec.execute(
                    "select karar, neden from public.elle_duzeltme where kap_id = %s",
                    (k.kap_id,),
                )
                kayitli = imlec.fetchone()

            if bildirim is None or makine is None:
                print(f"  !! {k.ticker} {k.kap_id}: bildirim ya da çıkarım yok")
                sayac["hata"] += 1
                continue
            ticker, an, metin, guncelleme_mi, karsi_taraf, nitelik = bildirim
            if ticker != k.ticker:
                # Yanlış kap_id kopyalandıysa başka şirketin sayısı değişirdi.
                print(f"  !! {k.kap_id}: dosyada {k.ticker}, veritabanında {ticker}")
                sayac["hata"] += 1
                continue

            cikarim = cikarimi_kur(elle_veri(k, makine[0]))
            sonuc = degerlendir_bildirim(
                depo,
                cikarim=cikarim,
                ticker=ticker,
                an=an,
                ham_metin_tr=metin or "",
                guncelleme_mi=bool(guncelleme_mi),
                karsi_taraf_acik=karsi_taraf_acik(karsi_taraf),
                karsi_taraf_niteligi=nitelik,
                insan_denetimli=True,
            )
            satir = (
                f"  {ticker:6}{an.date()} {k.karar:8} "
                f"{yuzde(makine[1]):>9} -> {yuzde(sonuc.ciro_orani):<9}"
            )
            if not sonuc.yayina_hazir:
                print(f"{satir} !! kapıdan geçmedi: {sonuc.red_nedeni}")
                sayac["hata"] += 1
                continue

            veri_ayni = (
                son[0] == ELLE_MODELI
                and son[1] == cikarim.model_dump(mode="json")
            )
            neden_ayni = kayitli == (k.karar, k.neden)
            if veri_ayni and neden_ayni:
                sayac["degismedi"] += 1
                continue
            print(satir + ("" if not veri_ayni else " (yalnız gerekçe)"))
            sayac[k.karar] += 1

            if not secenek.yaz:
                continue
            cikarim_id = None
            if not veri_ayni:
                cikarim_id = depo.cikarim_kaydet(
                    k.kap_id,
                    cikarim=cikarim,
                    meta=META,
                    yayina_hazir=True,
                    net_tutar_tl=sonuc.net_tutar_tl,
                    ciro_orani=sonuc.ciro_orani,
                    etki_skoru=sonuc.etki_skoru,
                )
            with baglanti.cursor() as imlec:
                if cikarim_id is None:
                    imlec.execute(SON.replace("model, veri", "id"), (k.kap_id,))
                    cikarim_id = imlec.fetchone()[0]
                imlec.execute(ELLE_KAYIT, (k.kap_id, k.karar, k.neden, cikarim_id))

        with baglanti.cursor() as imlec:
            imlec.execute("select kap_id from public.elle_duzeltme")
            kayitlilar = {r[0] for r in imlec.fetchall()}
        artik = kayitlilar - {k.kap_id for k in kararlar}
        if artik:
            # Dosyadan silinen karar veritabanında kendiliğinden geri
            # alınmaz: elle satır hâlâ en son çıkarım. Sessiz kalmamalı.
            print(f"\n!! dosyada olmayan {len(artik)} kayıt var: {sorted(artik)}")

        if secenek.yaz:
            baglanti.commit()

    print(f"\nözet: {dict(sayac)}")
    if not secenek.yaz:
        print("KURU KOŞU — hiçbir şey yazılmadı. Uygulamak için --yaz.")
    return 1 if sayac["hata"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
