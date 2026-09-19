"""Ham KAP yanıtlarının disk arşivi.

Backfill'in kontrol noktası burası. Bir bildirimin ham detayı bir kez
diske indikten sonra KAP'tan bir daha istenmez: çekim yarıda kalırsa
ikinci koşu kaldığı yerden devam eder (spec §13, risk 2). Aynı şey liste
pencereleri için de geçerli — çekilmiş bir hafta yeniden sorulmaz.

Ayrıştırma burada yapılmaz; arşiv yalnızca KAP'ın verdiğini olduğu gibi
saklar. Şema veya ayrıştırıcı değişirse arşivden yeniden üretilir, ağa
çıkılmaz.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

DETAY_KLASORU = "detay"
LISTE_KLASORU = "liste"


class HamArsiv:
    """KAP'ın ham JSON yanıtlarını disk üzerinde saklar."""

    def __init__(self, kok: Path) -> None:
        self._kok = Path(kok)

    # ------------------------------------------------------------- detay

    def detay_yolu(self, kap_index: int) -> Path:
        return self._kok / DETAY_KLASORU / f"{kap_index}.json"

    def var_mi(self, kap_index: int) -> bool:
        return self.detay_yolu(kap_index).exists()

    def yaz(self, kap_index: int, detay: dict) -> Path:
        return self._kaydet(self.detay_yolu(kap_index), detay)

    def oku(self, kap_index: int) -> dict:
        return json.loads(self.detay_yolu(kap_index).read_text(encoding="utf-8"))

    def indeksler(self) -> list[int]:
        klasor = self._kok / DETAY_KLASORU
        if not klasor.exists():
            return []
        return sorted(int(yol.stem) for yol in klasor.glob("*.json"))

    # ------------------------------------------------------------- liste

    def liste_yolu(self, baslangic: date, bitis: date) -> Path:
        ad = f"{baslangic.isoformat()}_{bitis.isoformat()}.json"
        return self._kok / LISTE_KLASORU / ad

    def liste_var_mi(self, baslangic: date, bitis: date) -> bool:
        return self.liste_yolu(baslangic, bitis).exists()

    def liste_yaz(self, baslangic: date, bitis: date, kayitlar: list[dict]) -> Path:
        return self._kaydet(self.liste_yolu(baslangic, bitis), kayitlar)

    def liste_oku(self, baslangic: date, bitis: date) -> list[dict]:
        return json.loads(
            self.liste_yolu(baslangic, bitis).read_text(encoding="utf-8")
        )

    # --------------------------------------------------------------- kur

    # Yayın olmayan gün de bilgi: işaretlenmezse her koşu 100'den fazla
    # tatil gününü TCMB'ye yeniden sorar.
    KUR_KLASORU = "kur"
    YOK_UZANTISI = ".yok"

    def kur_yolu(self, tarih: date) -> Path:
        return self._kok / self.KUR_KLASORU / f"{tarih.isoformat()}.xml"

    def _kur_yok_yolu(self, tarih: date) -> Path:
        return self.kur_yolu(tarih).with_suffix(self.YOK_UZANTISI)

    def kur_var_mi(self, tarih: date) -> bool:
        """O gün için soru sorulmuş mu — yanıt bülten de olabilir yokluk da."""
        return self.kur_yolu(tarih).exists() or self._kur_yok_yolu(tarih).exists()

    def kur_yaz(self, tarih: date, xml: str) -> Path:
        yol = self.kur_yolu(tarih)
        yol.parent.mkdir(parents=True, exist_ok=True)
        gecici = yol.with_suffix(".xml.tmp")
        gecici.write_text(xml, encoding="utf-8")
        os.replace(gecici, yol)
        return yol

    def kur_yok_isaretle(self, tarih: date) -> Path:
        yol = self._kur_yok_yolu(tarih)
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text("", encoding="utf-8")
        return yol

    def kur_oku(self, tarih: date) -> str | None:
        """Bülteni döndürür; o gün yayın yoksa None."""
        yol = self.kur_yolu(tarih)
        if not yol.exists():
            return None
        return yol.read_text(encoding="utf-8")

    def kur_gunleri(self) -> list[date]:
        """Arşivde bülteni olan günler, sırayla."""
        klasor = self._kok / self.KUR_KLASORU
        if not klasor.exists():
            return []
        return sorted(date.fromisoformat(yol.stem) for yol in klasor.glob("*.xml"))

    # ------------------------------------------------------------- ortak

    def _kaydet(self, yol: Path, veri: object) -> Path:
        """Ya tam yazar ya hiç yazmaz.

        Yarım kalmış bir JSON dosyası `var_mi` tarafından "çekilmiş"
        sayılırdı ve o bildirim sonsuza dek eksik kalırdı. Bu yüzden önce
        tamamı serileştirilir, sonra geçici dosya üzerinden yerine konur;
        `os.replace` aynı disk bölümünde atomiktir.
        """
        metin = json.dumps(veri, ensure_ascii=False)
        yol.parent.mkdir(parents=True, exist_ok=True)
        gecici = yol.with_suffix(".json.tmp")
        gecici.write_text(metin, encoding="utf-8")
        os.replace(gecici, yol)
        return yol
