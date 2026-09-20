"""Kayıtlı bir çıkarımı veritabanı bağlamına bağlar (spec §6 + §8).

`yayin.degerlendir` bilerek saf: ağ yok, veritabanı yok. Ama onu
çağırabilmek için iki şey veritabanından gelmeli — bildirim anına kadar
açıklanmış raporlardan çözülen TTM hasılat ve bildirim tarihli TCMB
kuru. Bu modül yalnız o bağlamı kuruyor.

Ayrı durmasının sebebi pratik: aynı zinciri hem ücretli koşu
(`scripts/cikarim_kosu.py`) hem bedava yeniden ölçüm
(`scripts/dogruluk_olc.py`) kuruyor. İki yerde yaşasaydı biri
düzeltilip diğeri unutulurdu — 2026-09-20'de karşılaştırma mantığında
tam bu oldu ve modelin doğruluğu bir koşu boyunca %66 sanıldı.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Callable, Mapping, Protocol, Sequence

from kap_radar.cikarim import TutarCikarimi
from kap_radar.finansal import DonemHasilat, ttm_coz
from kap_radar.yayin import Degerlendirme, degerlendir

__all__ = ["cikarimi_kur", "degerlendir_bildirim", "kur_cozucu"]


class DepoGibi(Protocol):
    """Zincirin veritabanından istediği her şey — iki okuma."""

    def donem_hasilatlari(self, ticker: str) -> Sequence[DonemHasilat]: ...

    def kur_coz(
        self, tarih: date, para_birimi: str
    ) -> tuple[date, Decimal] | None: ...


# Elle etiket (`data/altin_kume.json`) yalnız tutarları taşır: hap özet
# ve güven insandan istenmedi. Kapı yine de koşabilmeli, o yüzden şema
# dışı alanlar nötr değerle tamamlanıyor. `guven` özellikle "yuksek":
# eksikliği "dusuk" sayılsaydı A6 altın kümenin tamamını yükseltirdi.
_ETIKET_VARSAYILANLARI: Mapping = {
    "tutar_gizli": False,
    "hap_ozet": ["-", "-", "-"],
    "guven": "yuksek",
}


def cikarimi_kur(veri: TutarCikarimi | Mapping) -> TutarCikarimi:
    """Elle etiketi ya da `cikarim.veri` satırını şemaya çevirir."""
    if isinstance(veri, TutarCikarimi):
        return veri
    return TutarCikarimi(**{**_ETIKET_VARSAYILANLARI, **dict(veri)})


def kur_cozucu(depo: DepoGibi, tarih: date) -> Callable[[str], Decimal | None]:
    """Bir bildirimin tarihine sabitlenmiş kur kapanışı.

    Sonuç bildirim boyunca önbelleğe alınıyor: kapı aynı para birimini
    üç kez soruyor (net tutar, mükerrer denetimi, TL karşılığı) ve her
    soru bir veritabanı gidiş-dönüşü olurdu.

    TRY için kur aranmıyor — TCMB bülteninde Türk Lirası satırı yok ve
    sormak her TL kalemini 'kuru bulunamadı' sayıp B2'ye düşürürdü.
    """
    bellek: dict[str, Decimal | None] = {}

    def coz(para_birimi: str) -> Decimal | None:
        if para_birimi == "TRY":
            return Decimal("1")
        if para_birimi == "DIGER":
            return None
        if para_birimi not in bellek:
            sonuc = depo.kur_coz(tarih, para_birimi)
            bellek[para_birimi] = sonuc[1] if sonuc else None
        return bellek[para_birimi]

    return coz


def degerlendir_bildirim(
    depo: DepoGibi,
    *,
    cikarim: TutarCikarimi | Mapping,
    ticker: str,
    an: datetime,
    ham_metin_tr: str,
    guncelleme_mi: bool,
    karsi_taraf_acik: bool,
) -> Degerlendirme:
    """Bir bildirimin çıkarımını bugünkü kurallarla değerlendirir.

    `an` hem paydayı hem kuru belirliyor: o anda açıklanmamış rapor
    hesaba girmez (lookahead yasak, spec §8).
    """
    ttm = ttm_coz(depo.donem_hasilatlari(ticker), an)
    return degerlendir(
        cikarimi_kur(cikarim),
        ham_metin_tr=ham_metin_tr,
        ttm_hasilat=ttm.hasilat if ttm else None,
        kur_coz=kur_cozucu(depo, an.date()),
        karsi_taraf_acik=karsi_taraf_acik,
        guncelleme_mi=guncelleme_mi,
    )
