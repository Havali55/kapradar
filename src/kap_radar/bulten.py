"""Borsa İstanbul günlük pay piyasası bülteni ayrıştırıcısı.

Kaynak: borsaistanbul.com/data/thb/YYYY/AA/thbYYYYAAGG1.zip, içinde tek bir
`;` ayraçlı CSV. İlk satır Türkçe, ikincisi İngilizce başlık. Her pay için
resmî önceki kapanış, kapanış, işlem gören adet ve TL hacim veriyor;
borsadan sonradan çıkmış paylar da o günün bülteninde var.

Bilinmesi gerekenler (2026-09-28, 1.690 bültende doğrulandı):

- Başlığın başında bazen UTF-8 BOM var ("\\ufeffTARIH"). Eski bültenler
  cp1254 olabiliyor.
- Tarih çoğunlukla ISO ("2020-01-02"), 12 bültende (2020 Mayıs–Haziran)
  "21.05.2020". Sayılar hepsinde noktalı ondalık.
- Fiyatlar düzeltilmemiş: bedelsiz gününde "DEGISIM (%)" dahil her şey
  ham (CVKMD 2025-02-06 −%96,8, HRKET 2026-09-21 −%92,1). Sermaye işlemi
  çağıranın sorunu; burada yalnız okunuyor.
- Pay satırı: ENSTRUMAN GRUBU "EQT" ve işlem kodu ".E" ile bitiyor.
  Rüçhan, varant ve fon satırları aynı grupta başka soneklerle geliyor.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PAY_SONEKI = ".E"


@dataclass(frozen=True)
class BultenSatiri:
    tarih: date
    ticker: str
    onceki_kapanis: float
    kapanis: float
    adet: float
    hacim_tl: float

    @property
    def getiri(self) -> float | None:
        """Kapanıştan kapanışa ham getiri; işlem yoksa ya da önceki kapanış yoksa None.

        İşlem görmeyen günde bülten kapanışı 0 yazıyor (7.475 satır); getiri
        −%100 değil, tanımsız.
        """
        if self.onceki_kapanis <= 0 or self.kapanis <= 0 or self.adet <= 0:
            return None
        return self.kapanis / self.onceki_kapanis - 1


# Borsa İstanbul günlük fiyat marjı 13 Mart 2020'de ±%20'den ±%10'a indi
# (bültende %10,5–20 arası hareketler 2020-03-12'de 230, 2020-03-13'te 1).
# Marjı aşan kapanıştan kapanışa hareket normal işlemle oluşamaz: sermaye
# işlemi ya da veri hatası. Yuvarlama payı %0,5.
MARJ_DEGISIMI = date(2020, 3, 13)


def marj(gun: date) -> float:
    return 0.205 if gun < MARJ_DEGISIMI else 0.105


def metni_coz(ham: bytes) -> str:
    try:
        return ham.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ham.decode("cp1254")


def _sayi(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _tarih(s: str) -> date:
    s = s.strip()
    if "." in s:
        g, a, y = s.split(".")
        return date(int(y), int(a), int(g))
    return date.fromisoformat(s)


def satirlari_oku(metin: str) -> list[BultenSatiri]:
    """Bültenin pay satırları. Sayısı eksik ya da bozuk satır atlanır.

    Aynı pay bir günde birden çok satırda görünürse (pazar değişimi günü)
    işlem adedi büyük olan tutulur.
    """
    okuyucu = csv.reader(io.StringIO(metin), delimiter=";")
    baslik = [b.strip().lstrip("﻿") for b in next(okuyucu)]
    next(okuyucu, None)  # İngilizce başlık
    i = {ad: baslik.index(ad) for ad in (
        "TARIH", "ISLEM  KODU", "ENSTRUMAN GRUBU", "ONCEKI KAPANIS FIYATI",
        "KAPANIS FIYATI", "TOPLAM ISLEM ADEDI", "TOPLAM ISLEM HACMI")}
    son = max(i.values())
    secilen: dict[str, BultenSatiri] = {}
    for s in okuyucu:
        if len(s) <= son or s[i["ENSTRUMAN GRUBU"]].strip() != "EQT":
            continue
        kod = s[i["ISLEM  KODU"]].strip()
        if not kod.endswith(PAY_SONEKI):
            continue
        degerler = [_sayi(s[i[k]]) for k in (
            "ONCEKI KAPANIS FIYATI", "KAPANIS FIYATI", "TOPLAM ISLEM ADEDI", "TOPLAM ISLEM HACMI")]
        if any(d is None for d in degerler):
            continue
        onceki, kapanis, adet, hacim = degerler
        satir = BultenSatiri(_tarih(s[i["TARIH"]]), kod[: -len(PAY_SONEKI)],
                             onceki, kapanis, adet, hacim)
        eski = secilen.get(satir.ticker)
        if eski is None or satir.adet > eski.adet:
            secilen[satir.ticker] = satir
    return list(secilen.values())


def zip_oku(yol: Path) -> list[BultenSatiri]:
    with zipfile.ZipFile(yol) as z:
        return satirlari_oku(metni_coz(z.read(z.namelist()[0])))
