"""Kayıtlı çıkarımları altın kümeye karşı puanlar (spec §10, Adım 13).

Kullanım:
    python scripts/dogruluk_olc.py                    # son çıkarımlar
    python scripts/dogruluk_olc.py --prompt v2        # yalnız v2 prompt'u
    python scripts/dogruluk_olc.py --ayrinti

**Ağa çıkmaz, para harcamaz.** Kaynağı `cikarim` tablosu: prompt
değiştiğinde ya da karşılaştırma kuralı düzeldiğinde aynı satırlar
yeniden puanlanır. Ölçümü koşudan ayırmanın sebebi bu — 2026-09-20'de
karşılaştırma hatası yüzünden doğruluk %66 sanılmıştı, düzeltmek için
50 çağrıyı tekrarlamak gerekmedi.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.karsi_taraf import karsi_taraf_acik  # noqa: E402
from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.degerlendirme import degerlendir_bildirim  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.dogruluk import Sonuc, kalem_kumesi, karsilastir, ozetle  # noqa: E402

VARSAYILAN_KUME = KOK / "data" / "altin_kume.json"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="Altın kümeye göre doğruluk")
    ayristirici.add_argument("--kume", type=Path, default=VARSAYILAN_KUME)
    ayristirici.add_argument("--prompt", help="yalnız bu prompt sürümü")
    ayristirici.add_argument("--ayrinti", action="store_true")
    secenek = ayristirici.parse_args()

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    etiketler = {
        k["kap_id"]: k
        for k in json.loads(secenek.kume.read_text(encoding="utf-8"))["kayitlar"]
    }

    sonuclar: list[Sonuc] = []
    surum = Counter()
    kapi = Counter()
    ayrinti: list[str] = []
    skor_ayni = skor_farkli = 0
    skor_sapmasi: list[str] = []

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        with baglanti.cursor() as imlec:
            # Her bildirim için EN SON çıkarım: prompt düzeltilince eski
            # satır tarihsel kayıt olarak kalıyor ama ölçüme girmemeli.
            imlec.execute(
                "select distinct on (c.kap_id) c.kap_id, b.ticker, c.veri, "
                "       c.prompt_versiyon, c.model, b.ham_metin_tr, "
                "       b.yayin_zamani, b.guncelleme_mi, "
                "       b.kap_alanlari->>'karsi_taraf' "
                "from public.cikarim c join public.bildirim b using (kap_id) "
                # `%s::text` şart: Postgres tip çıkarımı NULL parametrede
                # başarısız oluyor (IndeterminateDatatype).
                "where c.kap_id = any(%s) "
                "and (%s::text is null or c.prompt_versiyon = %s::text) "
                "order by c.kap_id, c.olusturuldu_at desc, c.id desc",
                (list(etiketler), secenek.prompt, secenek.prompt),
            )
            satirlar = imlec.fetchall()

        if not satirlar:
            print("Ölçülecek çıkarım yok.")
            return 0

        depo = Depo(baglanti)
        for satir in satirlar:
            (
                kap_id,
                ticker,
                veri,
                prompt_versiyon,
                model,
                ham_metin,
                an,
                guncelleme_mi,
                karsi_taraf,
            ) = satir
            etiket = etiketler[kap_id]
            beklenen = etiket["tutarlar"]
            gelen = veri.get("tutarlar", [])
            sonuc = karsilastir(beklenen, gelen)
            sonuclar.append(sonuc)
            surum[prompt_versiyon] += 1

            # Kapının B aşaması ve skor burada yeniden koşuyor: saklanan
            # satır eski bir sürümle yazılmış olabilir ve ölçüm her
            # zaman BUGÜNKÜ kuralları yansıtmalı.
            def olc(cikarim):
                return degerlendir_bildirim(
                    depo,
                    cikarim=cikarim,
                    ticker=ticker,
                    an=an,
                    ham_metin_tr=ham_metin or "",
                    guncelleme_mi=bool(guncelleme_mi),
                    karsi_taraf_acik=karsi_taraf_acik(karsi_taraf),
                )

            karar = olc(veri)
            # Elle etiket aynı kapıdan geçiyor: kıyas modelin çıkarımıyla
            # insanınki arasında, model ile ham etiket arasında değil.
            elle = olc(etiket)
            kapi[
                "yayina_hazir" if karar.yayina_hazir
                else (karar.red_nedeni or "red").split(":")[0]
            ] += 1

            if karar.etki_skoru == elle.etki_skoru:
                skor_ayni += 1
            else:
                skor_farkli += 1
                skor_sapmasi.append(
                    f"  {ticker:7} {etiket['kap_index']}  "
                    f"elle={elle.etki_skoru}  model={karar.etki_skoru}  "
                    f"{karar.red_nedeni or ''}"
                )

            if sonuc is not Sonuc.TAM:
                b, g = kalem_kumesi(beklenen), kalem_kumesi(gelen)
                ayrinti.append(
                    f"  {ticker:7} {etiket['kap_index']} [{sonuc.value}]\n"
                    f"      eksik : {sorted(b - g) or '-'}\n"
                    f"      fazla : {sorted(g - b) or '-'}\n"
                    f"      kapi  : {karar.karar.value} {karar.red_nedeni or ''}\n"
                    f"      not   : {etiket.get('not', '')[:110]}"
                )

    sayac = ozetle(sonuclar)
    toplam = len(sonuclar)
    print(f"olculen  : {toplam} bildirim")
    print(f"prompt   : {dict(surum)}")
    print(f"model    : {satirlar[0][4]}")
    print("\n--- dogruluk ---")
    print(f"  tam dogru : {sayac['tam']}/{toplam} (%{100 * sayac['tam'] / toplam:.1f})")
    print(f"  kismi     : {sayac['kismi']}")
    print(f"  yanlis    : {sayac['yanlis']}")
    print("\n--- kapi ---")
    for ad, adet in kapi.most_common():
        print(f"  {ad:14} {adet}")

    # Asıl soru bu: yayınlanacak SAYI doğru mu? Kalem kümesi tutmasa da
    # skor aynı çıkabilir (fark skora girmeyen bir tipte olabilir), tam
    # tutan çıkarım da yanlış skor verebilir.
    print("\n--- skor (elle etikete gore) ---")
    print(f"  ayni      : {skor_ayni}/{toplam}")
    print(f"  farkli    : {skor_farkli}")

    if secenek.ayrinti and ayrinti:
        print("\n--- sapmalar ---")
        for satir in ayrinti:
            print(satir)
    if secenek.ayrinti and skor_sapmasi:
        print("\n--- skor sapmalari ---")
        for satir in skor_sapmasi:
            print(satir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
