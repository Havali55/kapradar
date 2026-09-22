"""Kayıtlı çıkarımları yeniden skorlar — LLM çağrısı YOK, ücretsiz.

Kullanım:
    python scripts/skor_yenile.py            # KURU: ne değişecek, yazmaz
    python scripts/skor_yenile.py --yaz      # değişiklikleri uygular

Skor formülünün ayarları (`skor.Agirliklar`) değiştiğinde `cikarim`
tablosundaki türetilmiş sayılar eskir. Bu betik onları kayıtlı
`cikarim.veri` alanından yeniden hesaplar: model bir daha çağrılmaz,
çünkü metinden okunan tutarlar zaten saklı. Adım 14'ün 613 bildirimi
yeniden çıkarılsaydı ~0,06 USD tutardı; burada maliyet sıfır.

Türetilmiş sayı yerinde GÜNCELLENİYOR, yeni satır eklenmiyor.
`cikarim_kaydet` bilerek hep ekler — o bir LLM çıkarımının kaydı ve
dondurulur. Buradaki üç sayı (net tutar, ciro oranı, skor) ise o
çıkarımdan türetilmiş; `tepki` tablosu gibi güncellenir, yoksa her ayar
değişikliği 613 sahte "çıkarım" daha üretirdi.

Kapı kararının (`yayina_hazir` / `red_nedeni`) DEĞİŞMEMESİ beklenir:
taban/tavan yalnız skorun sayısal değerini etkiler, A1–A6 ve B1–B3
kapıları oranı eşiğe vurmaz. Değişen olursa betik bunu ayrıca ve
gürültülü biçimde raporlar — sessizce geçmesi, formül değişikliğinin
yayın kararını kaydırdığını fark etmemek demek olurdu.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

import psycopg  # noqa: E402

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.degerlendirme import degerlendir_bildirim  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.skor import MEGA_ESIGI, ONEMLI_ESIGI, kademe  # noqa: E402

ALANLAR = """
       c.id, c.kap_id, b.ticker, b.ham_metin_tr, b.yayin_zamani,
       b.guncelleme_mi, b.kap_alanlari->>'karsi_taraf' as karsi_taraf,
       c.veri, c.net_tutar_tl, c.ciro_orani, c.etki_skoru,
       c.yayina_hazir, c.red_nedeni
"""

# Varsayılan: yalnız her bildirimin EN SON çıkarımı. `public.akis`
# görünümü de tam olarak bunu okuyor (`distinct on (kap_id) ... order by
# id desc`), yani sitenin gösterdiği satır bu.
#
# Eski satırlar bilerek donmuş bırakılıyor. 2026-09-20 pilotunda kapı
# devreye girmeden önce yazılmış v2/erken-v3 satırları var: skorsuz ama
# `yayina_hazir=true` görünüyorlar, çünkü o an §8 zinciri hiç
# koşmamıştı. Bugünkü kurallarla yeniden değerlendirilirlerse dördü
# reddedilmiş duruma düşer — ama onlar bir geçmiş kaydı, o günkü koşunun
# ne yaptığının kanıtı. Üzerlerine yazmak denetim izini siler.
SEC_SON = f"""
select distinct on (c.kap_id) {ALANLAR}
from public.cikarim c
join public.bildirim b using (kap_id)
order by c.kap_id, c.id desc
"""

SEC_TUM = f"""
select {ALANLAR}
from public.cikarim c
join public.bildirim b using (kap_id)
order by b.yayin_zamani, c.id
"""

GUNCELLE = """
update public.cikarim
   set net_tutar_tl = %(net_tutar_tl)s,
       ciro_orani   = %(ciro_orani)s,
       etki_skoru   = %(etki_skoru)s
 where id = %(id)s
"""


# Eski skorları eski eşikleriyle kovalamak için. Karşılaştırma ancak
# her skor kendi döneminin etiketiyle sayılırsa anlamlı: yeni eşikleri
# eski skorlara uygularsak "mega 60 → 55" yerine uydurma bir "32 → 55"
# çıkar ve değişiklik olduğundan büyük görünür.
ONCEKI_MEGA = Decimal("3.0")
ONCEKI_ONEMLI = Decimal("2.0")


def _kademe_esikli(
    skor: Decimal | None, mega: Decimal, onemli: Decimal
) -> str | None:
    if skor is None:
        return None
    if skor >= mega:
        return "mega"
    if skor >= onemli:
        return "onemli"
    return "rutin"


def _dagilim(
    skorlar: list[Decimal | None], mega: Decimal, onemli: Decimal
) -> Counter:
    sayac: Counter = Counter()
    for s in skorlar:
        sayac[_kademe_esikli(s, mega, onemli) or "skorsuz"] += 1
        if s is not None and s == 0:
            sayac["_sifir"] += 1
    return sayac


def _medyan(skorlar: list[Decimal | None]) -> Decimal | None:
    dolu = sorted(s for s in skorlar if s is not None)
    if not dolu:
        return None
    return dolu[len(dolu) // 2]


def _yazdir_dagilim(
    baslik: str, skorlar: list[Decimal | None], mega: Decimal, onemli: Decimal
) -> None:
    d = _dagilim(skorlar, mega, onemli)
    orta = _medyan(skorlar)
    print(
        f"  {baslik:22} mega={d['mega']:4} onemli={d['onemli']:4} "
        f"rutin={d['rutin']:4} skorsuz={d['skorsuz']:4} "
        f"sifir={d['_sifir']:3} medyan={orta if orta is not None else '-'}"
    )


def main(argv: list[str] | None = None) -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--yaz",
        action="store_true",
        help="değişiklikleri veritabanına uygula (varsayılan: kuru koşu)",
    )
    ayristirici.add_argument(
        "--ayrinti",
        action="store_true",
        help="skoru değişen her satırı tek tek bas",
    )
    ayristirici.add_argument(
        "--tum",
        action="store_true",
        help=(
            "her çıkarım satırını yeniden skorla (varsayılan: yalnız her "
            "bildirimin en sonuncusu — sitenin okuduğu satır)"
        ),
    )
    secenek = ayristirici.parse_args(argv)

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok", file=sys.stderr)
        return 1

    print(f"kademe esikleri: mega>={MEGA_ESIGI}  onemli>={ONEMLI_ESIGI}")
    print(f"kapsam         : {'TUM satirlar' if secenek.tum else 'her bildirimin son cikarimi'}")
    print(f"kip            : {'YAZ' if secenek.yaz else 'KURU (yazmaz)'}\n")

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute(SEC_TUM if secenek.tum else SEC_SON)
            satirlar = imlec.fetchall()

        eski_skorlar: list[Decimal | None] = []
        yeni_skorlar: list[Decimal | None] = []
        guncellenecek: list[dict] = []
        kapi_degisenler: list[str] = []
        kademe_degisenler = 0
        skor_kazanan = 0

        for satir in satirlar:
            (
                cikarim_id,
                kap_id,
                ticker,
                metin,
                an,
                guncelleme_mi,
                karsi_taraf,
                veri,
                eski_tutar,
                eski_oran,
                eski_skor,
                eski_hazir,
                eski_red,
            ) = satir

            karar = degerlendir_bildirim(
                depo,
                cikarim=veri,
                ticker=ticker,
                an=an,
                ham_metin_tr=metin or "",
                guncelleme_mi=bool(guncelleme_mi),
                karsi_taraf_acik=bool(karsi_taraf),
            )

            eski_skorlar.append(eski_skor)
            yeni_skorlar.append(karar.etki_skoru)

            # Kapı kararı değişmemeli. Değiştiyse formül değişikliği
            # yayın kararını kaydırmış demektir — sessiz geçilemez.
            if bool(eski_hazir) != bool(karar.yayina_hazir) or (
                (eski_red or None) != (karar.red_nedeni or None)
            ):
                kapi_degisenler.append(
                    f"{ticker} {kap_id[:8]}: "
                    f"hazir {eski_hazir}->{karar.yayina_hazir} "
                    f"red {eski_red!r}->{karar.red_nedeni!r}"
                )

            # Her skor kendi döneminin eşiğiyle etiketleniyor: asıl
            # soru "kullanıcının gördüğü etiket değişti mi", "sayı
            # değişti mi" değil.
            if _kademe_esikli(eski_skor, ONCEKI_MEGA, ONCEKI_ONEMLI) != kademe(
                karar.etki_skoru
            ):
                kademe_degisenler += 1

            if eski_skor is None and karar.etki_skoru is not None:
                skor_kazanan += 1
                print(
                    f"  + {ticker:7} {kap_id[:8]} skorsuzken {karar.etki_skoru} "
                    "aldi (arada finansal rapor yuklenmis olmali)"
                )

            if eski_skor != karar.etki_skoru or eski_oran != karar.ciro_orani:
                guncellenecek.append(
                    {
                        "id": cikarim_id,
                        "net_tutar_tl": karar.net_tutar_tl,
                        "ciro_orani": karar.ciro_orani,
                        "etki_skoru": karar.etki_skoru,
                    }
                )
                if secenek.ayrinti:
                    print(
                        f"  {ticker:7} {kap_id[:8]} "
                        f"skor {eski_skor if eski_skor is not None else '-':>5} -> "
                        f"{karar.etki_skoru if karar.etki_skoru is not None else '-':>5}"
                        f"  kademe {kademe(eski_skor)} -> {kademe(karar.etki_skoru)}"
                    )

        print(f"cikarim satiri : {len(satirlar)}")
        _yazdir_dagilim(
            f"ESKI (esik {ONCEKI_MEGA}/{ONCEKI_ONEMLI})",
            eski_skorlar,
            ONCEKI_MEGA,
            ONCEKI_ONEMLI,
        )
        _yazdir_dagilim(
            f"YENI (esik {MEGA_ESIGI}/{ONEMLI_ESIGI})",
            yeni_skorlar,
            MEGA_ESIGI,
            ONEMLI_ESIGI,
        )
        print(f"\nskoru degisen  : {len(guncellenecek)}")
        print(f"kademesi degisen: {kademe_degisenler}  (her skor kendi esigiyle)")
        print(f"skorsuzken skorlanan: {skor_kazanan}")

        if kapi_degisenler:
            print(
                f"\n!!! KAPI KARARI DEGISEN {len(kapi_degisenler)} SATIR — "
                "beklenmiyordu, incele:",
                file=sys.stderr,
            )
            for s in kapi_degisenler[:20]:
                print(f"  {s}", file=sys.stderr)
            if not secenek.yaz:
                print(
                    "\nKuru kosu: once bu sapmalar aciklanmali.", file=sys.stderr
                )
        else:
            print("kapi karari    : degismedi (beklenen)")

        if not secenek.yaz:
            print("\nKURU KOSU — hicbir sey yazilmadi. Uygulamak icin --yaz.")
            return 0

        with baglanti.cursor() as imlec:
            imlec.executemany(GUNCELLE, guncellenecek)
        baglanti.commit()
        print(f"\n{len(guncellenecek)} satir guncellendi.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
