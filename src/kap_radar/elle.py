"""Elle kararlar: kapının şüpheli bulduğu çıkarımlara insanın cevabı.

Anlam kapısı (B4–B6, `cikarim.anlam_kapisi`) bildirimi elle kuyruğa
atıyor. Kuyruğu boşaltan şey `data/elle_duzeltmeler.json`: her bildirim
için bir karar ve gerekçesi. Dosya repoda duruyor, çünkü bir büyüklüğün
neden değiştiği git geçmişinden okunabilmeli; veritabanında sessizce
düzeltilen sayı savunulamaz.

Üç karar var:
  onayla  : LLM çıkarımı doğru, kapı yanlış alarm verdi (FORTE kendini
            "tedarikçi" yazmış ama ihaleyi kazanan satıcı).
  skorsuz : tutar metinde var ama şirketin geliri değil (ASTOR'un
            alımı, TOASO'nun yatırımı). Bildirim büyüklüksüz yayınlanır.
  duzelt  : belirli kalemlerin tipi değişir (FORTE'nin artıştan sonraki
            yeni toplamı `toplam_sozlesme` olur, skora girmez).

Her karar isteğe bağlı olarak özeti de değiştirebilir (A7: modelin
uydurduğu yıl).

Saf modül; veritabanına `scripts/elle_duzelt.py` yazar.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

__all__ = ["ElleKarar", "KARARLAR", "elle_veri", "kararlari_oku"]

KARARLAR = ("onayla", "skorsuz", "duzelt")
_TIPLER = ("ilave_siparis", "fiyat_farki", "toplam_sozlesme", "tek_seferlik")


@dataclass(frozen=True)
class ElleKarar:
    kap_id: str
    ticker: str
    karar: str
    neden: str
    # Kalem değeri (ondalık yazımdan bağımsız) → yeni tip.
    yeni_tipler: Mapping[str, str] = field(default_factory=dict)
    hap_ozet: tuple[str, ...] | None = None


def _dogrula(k: ElleKarar) -> None:
    if k.karar not in KARARLAR:
        raise ValueError(f"{k.kap_id}: karar {k.karar!r} tanımsız, {KARARLAR}")
    if not k.neden.strip():
        raise ValueError(f"{k.kap_id}: neden boş — gerekçesiz karar yazılmaz")
    if k.karar == "duzelt" and not k.yeni_tipler:
        raise ValueError(f"{k.kap_id}: duzelt kararı yeni_tipler ister")
    for deger, tip in k.yeni_tipler.items():
        if tip not in _TIPLER:
            raise ValueError(f"{k.kap_id}: tip {tip!r} tanımsız")
        try:
            Decimal(deger)
        except InvalidOperation:
            raise ValueError(f"{k.kap_id}: değer {deger!r} sayı değil") from None
    if k.hap_ozet is not None and len(k.hap_ozet) != 3:
        raise ValueError(f"{k.kap_id}: hap_ozet tam 3 madde olmalı")


def kararlari_oku(yol: Path) -> list[ElleKarar]:
    ham = json.loads(Path(yol).read_text(encoding="utf-8"))
    kararlar = []
    gorulen: set[str] = set()
    for kayit in ham["kararlar"]:
        ozet = kayit.get("hap_ozet")
        k = ElleKarar(
            kap_id=kayit["kap_id"],
            ticker=kayit["ticker"],
            karar=kayit["karar"],
            neden=kayit["neden"],
            yeni_tipler=dict(kayit.get("yeni_tipler") or {}),
            hap_ozet=tuple(ozet) if ozet is not None else None,
        )
        _dogrula(k)
        if k.kap_id in gorulen:
            raise ValueError(f"{k.kap_id}: aynı bildirime iki karar")
        gorulen.add(k.kap_id)
        kararlar.append(k)
    return kararlar


def elle_veri(karar: ElleKarar, taban: Mapping) -> dict:
    """LLM çıkarımından (`cikarim.veri`) elle kararın uygulandığı yeni veri."""
    veri = copy.deepcopy(dict(taban))
    if karar.karar == "skorsuz":
        veri["tutarlar"] = []
    elif karar.karar == "duzelt":
        kalanlar = {Decimal(d): tip for d, tip in karar.yeni_tipler.items()}
        for kalem in veri["tutarlar"]:
            yeni = kalanlar.pop(Decimal(str(kalem["deger"])), None)
            if yeni is not None:
                kalem["tip"] = yeni
        if kalanlar:
            eksik = ", ".join(format(d, "f") for d in kalanlar)
            raise ValueError(f"{karar.kap_id}: çıkarımda kalem yok: {eksik}")
    if karar.hap_ozet is not None:
        veri["hap_ozet"] = list(karar.hap_ozet)
    return veri
