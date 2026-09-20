"""Altın küme üzerinde tüm hattı uçtan uca koşturur (Adım 5–10 doğrulaması).

Kullanım:
    python scripts/skor_dogrula.py
    python scripts/skor_dogrula.py --ayrinti     # her bildirimi tek tek yaz

LLM'e hiç uğramıyor: tutarlar elle etiketlenmiş altın kümeden geliyor.
Ölçülen şey modelin doğruluğu değil, **zincirin kendisi** — TCMB kuru
(Adım 5), point-in-time TTM hasılat (Adım 7), doğrulama kapısı (Adım 9)
ve skor formülü (Adım 10) gerçek veriyle birbirine bağlanıyor mu.

Kapsama sayıları burada anlamlı: skorsuz kalan bildirim bir hata değil,
tasarım kararı (tutar ya da hasılat yoksa skor gösterilmez). Ama oranın
ne olduğu bilinmeli.
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

from kap_radar.ayarlar import dsn_bul  # noqa: E402
from kap_radar.cikarim import Karar, Tutar, tutarlilik_kapisi  # noqa: E402
from kap_radar.depo import Depo  # noqa: E402
from kap_radar.finansal import ttm_coz  # noqa: E402
from kap_radar.skor import SKORA_GIREN_TIPLER, buyukluk_skoru, net_tutar_tl  # noqa: E402

VARSAYILAN_KUME = KOK / "data" / "altin_kume.json"


def kur_cozucu(depo: Depo, tarih):
    """Bildirim tarihli TCMB alış kurunu veren kapanış.

    TRY için kur aranmıyor: TCMB bülteninde Türk Lirası satırı yok ve
    1 yazmak yerine sorgulamak her TL kalemini eksik kur sanardı.
    """

    def coz(para_birimi: str) -> Decimal | None:
        if para_birimi == "TRY":
            return Decimal("1")
        if para_birimi == "DIGER":
            return None
        sonuc = depo.kur_coz(tarih, para_birimi)
        return sonuc[1] if sonuc else None

    return coz


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayristirici = argparse.ArgumentParser(description="Altın kümede skor doğrulaması")
    ayristirici.add_argument("--kume", type=Path, default=VARSAYILAN_KUME)
    ayristirici.add_argument("--ayrinti", action="store_true")
    secenek = ayristirici.parse_args()

    dsn = dsn_bul()
    if dsn is None:
        print("DATABASE_URL yok ya da <PAROLA> yer tutucusu duruyor", file=sys.stderr)
        return 1

    kayitlar = json.loads(secenek.kume.read_text(encoding="utf-8"))["kayitlar"]
    sonuc = Counter()
    skorlar: list[Decimal] = []
    satirlar = []

    with psycopg.connect(dsn, connect_timeout=20) as baglanti:
        depo = Depo(baglanti)
        with baglanti.cursor() as imlec:
            imlec.execute(
                "select kap_id, ticker, yayin_zamani, guncelleme_mi, "
                "kap_alanlari->>'karsi_taraf' from public.bildirim "
                "where kap_id = any(%s)",
                ([k["kap_id"] for k in kayitlar],),
            )
            bildirimler = {s[0]: s for s in imlec.fetchall()}

        for kayit in kayitlar:
            bildirim = bildirimler.get(kayit["kap_id"])
            if bildirim is None:
                sonuc["bildirim yok"] += 1
                continue
            _, ticker, an, guncelleme_mi, karsi_taraf = bildirim

            tutarlar = [Tutar(**t) for t in kayit["tutarlar"]]
            kur = kur_cozucu(depo, an.date())
            net = net_tutar_tl(tutarlar, kur)
            # B3 mükerrer çevrim kontrolü kalem kalem TL karşılığı istiyor.
            tl_kalemler = [
                (t.tip, t.deger * kur(t.para_birimi))
                for t in tutarlar
                if t.tip in SKORA_GIREN_TIPLER and kur(t.para_birimi) is not None
            ]
            ttm = ttm_coz(depo.donem_hasilatlari(ticker), an)

            oran = None
            if net is not None and ttm and ttm.hasilat:
                oran = net / ttm.hasilat

            skor = buyukluk_skoru(
                net_tutar_tl=net,
                ttm_hasilat=ttm.hasilat if ttm else None,
                karsi_taraf_acik=bool(karsi_taraf),
                guncelleme_mi=bool(guncelleme_mi),
            )

            kapi = tutarlilik_kapisi(
                ciro_orani=oran,
                # Skora giren kalem yoksa çevrilecek bir şey de yok;
                # B2 o bildirimleri sebepsiz elle kuyruğa atmasın.
                kur_bulundu=net is not None or not any(
                    t.tip in SKORA_GIREN_TIPLER for t in tutarlar
                ),
                tl_kalemler=tl_kalemler,
            )

            if skor is not None:
                skorlar.append(skor)
            sonuc[_durum(net, ttm, skor, kapi.karar)] += 1
            satirlar.append((ticker, kayit["kap_index"], net, ttm, oran, skor, kapi))

    print(f"altin kume: {len(kayitlar)} bildirim\n")
    if secenek.ayrinti:
        for ticker, indeks, net, ttm, oran, skor, kapi in satirlar:
            print(
                f"{ticker:7} {indeks}  net={_bicim(net):>18}  "
                f"ttm={_bicim(ttm.hasilat if ttm else None):>18}  "
                f"oran={_yuzde(oran):>8}  skor={skor if skor is not None else '   -':>5}"
                f"  {kapi.red_nedeni or ''}"
            )
        print()

    print("--- durum dagilimi ---")
    for durum, adet in sonuc.most_common():
        print(f"  {durum:28} {adet}")

    if skorlar:
        sirali = sorted(skorlar)
        print("\n--- skor dagilimi ---")
        print(f"  skorlu bildirim : {len(sirali)}")
        print(f"  en dusuk / medyan / en yuksek : "
              f"{sirali[0]} / {sirali[len(sirali) // 2]} / {sirali[-1]}")
    return 0


def _durum(net, ttm, skor, karar) -> str:
    if karar is Karar.ELLE:
        return "elle kuyruga"
    if skor is not None:
        return "skorlu"
    if net is None:
        return "tutar yok -> skorsuz"
    if ttm is None:
        return "hasilat yok -> skorsuz"
    return "skorsuz (diger)"


def _bicim(deger) -> str:
    return f"{deger:,.0f}" if deger is not None else "-"


def _yuzde(oran) -> str:
    return f"%{oran * 100:.2f}" if oran is not None else "-"


if __name__ == "__main__":
    raise SystemExit(main())
