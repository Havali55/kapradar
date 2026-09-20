"""Çıkarımların altın kümeye karşı karşılaştırılması (spec §10).

Ölçüm koddan ayrı duruyor çünkü **yeniden ölçmek para harcamamalı**:
çıkarımlar `cikarim` tablosunda duruyor, prompt değiştiğinde ya da
karşılaştırma kuralı düzeldiğinde aynı satırlar yeniden puanlanabilir.

Karşılaştırma `Decimal` üzerinden: '2999015.00' ile '2999015' aynı
sayıdır. İlk koşuda metin kıyaslaması yüzünden 50 bildirimin 8'i
sebepsiz yanlış göründü ve modelin doğruluğu %66 sanıldı.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Iterable, Sequence

from kap_radar.cikarim import Tutar

__all__ = ["Sonuc", "kalem_kumesi", "karsilastir", "ozetle"]


class Sonuc(Enum):
    TAM = "tam"
    KISMI = "kismi"
    YANLIS = "yanlis"


# Bir kalemin kimliği: değer + para birimi + tip. `alinti` karşılaştırmaya
# girmiyor — aynı tutarı farklı cümleyle alıntılamak hata değil, kapının
# işi zaten alıntının gerçekliğini denetlemek.
Anahtar = tuple[Decimal, str, str]


def _deger(ham) -> Decimal | None:
    try:
        return Decimal(str(ham))
    except (InvalidOperation, TypeError):
        return None


def kalem_kumesi(kalemler: Iterable[Tutar | dict]) -> set[Anahtar]:
    """Tutar kalemlerini karşılaştırılabilir anahtar kümesine indirger."""
    kume: set[Anahtar] = set()
    for kalem in kalemler:
        if isinstance(kalem, Tutar):
            deger, para, tip = kalem.deger, kalem.para_birimi, kalem.tip
        else:
            deger = _deger(kalem.get("deger"))
            para, tip = kalem.get("para_birimi"), kalem.get("tip")
        if deger is not None:
            kume.add((deger, para, tip))
    return kume


def karsilastir(
    beklenen: Sequence[Tutar | dict], gelen: Sequence[Tutar | dict]
) -> Sonuc:
    """Tek bir bildirimin çıkarımını elle etiketiyle karşılaştırır."""
    b, g = kalem_kumesi(beklenen), kalem_kumesi(gelen)
    if b == g:
        return Sonuc.TAM
    return Sonuc.KISMI if b & g else Sonuc.YANLIS


def ozetle(sonuclar: Iterable[Sonuc]) -> dict[str, int]:
    sayac = {s.value: 0 for s in Sonuc}
    for sonuc in sonuclar:
        sayac[sonuc.value] += 1
    return sayac
