"""Söz ve gerçek: duyuru yoğunluğu ile gerçekleşen reel büyüme.

Tanım: docs/superpowers/specs/2026-09-27-site-v3-tasarim.md §5 ve
docs/arastirma/2026-09-27-soz-ve-gercek.md. Fonksiyonlar saf; veritabanı
okuması `scripts/analiz_soz_gercek.py`'de.

Site aynı hesabı `site/lib/soz.ts`'te yapıyor (görüntü istatistikleri
sitede hesaplanıyor, `panelleriHesapla` gibi). İki uygulama aynı
fikstürle sınanıyor: `tests/fixtures/soz_gercek.json`. Biri değişip
öteki unutulursa testlerden biri kırılır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from statistics import median
from typing import Mapping, Sequence

# Büyüme dönemi: raporların geldiği en yeni çeyrek. Bir dönemin kapsamı
# bir önceki çeyreğinkinin bu oranına ulaşmadıysa raporlama sezonu
# sürüyor; yarım kapsamla grup medyanı kimin erken raporladığına göre
# oynar.
KAPSAM_ORANI = 0.9

# "En çok duyuran grup belirgin önde" cümlesi ancak bu farkla kurulur:
# üst grubun medyanı diğer ikisinin büyüğünü 0,10 (10 puan) aşmalı.
ONDE_ESIGI = 0.10

GRUP_ADLARI = ("Az duyuran", "Orta", "Çok duyuran")

_CEYREK_SONU = {3: 31, 6: 30, 9: 30, 12: 31}


@dataclass(frozen=True)
class SozSatiri:
    ticker: str
    # Söz yılında duyurulan TL toplamı / o yılın cirosu.
    yogunluk: float
    # Büyüme dönemindeki reel ciro büyümesi (0,20 = %20).
    buyume: float


@dataclass(frozen=True)
class Grup:
    ad: str
    satirlar: tuple[SozSatiri, ...]
    medyan_buyume: float
    medyan_yogunluk: float


@dataclass(frozen=True)
class SozOzeti:
    n: int
    gruplar: tuple[Grup, Grup, Grup]
    rho: float
    t: float
    ust_grup_onde: bool


def onceki_ceyrek(d: date) -> date:
    """Bir çeyrek sonundan önceki çeyrek sonu."""
    ay, yil = d.month - 3, d.year
    if ay <= 0:
        ay, yil = ay + 12, yil - 1
    return date(yil, ay, _CEYREK_SONU[ay])


def buyume_donemi_sec(kapsam: Mapping[date, int]) -> date | None:
    """Kapsamı bir önceki çeyreğinkinin en az %90'ı olan en yeni çeyrek sonu.

    `kapsam`: dönem sonu → o dönem için büyümesi olan şirket sayısı.
    Çeyrek sonu olmayan dönemler (özel hesap yılı) aday değil.
    """
    ceyrekler = sorted(
        (d for d in kapsam if _CEYREK_SONU.get(d.month) == d.day), reverse=True
    )
    for d in ceyrekler:
        if kapsam[d] >= KAPSAM_ORANI * kapsam.get(onceki_ceyrek(d), 0):
            return d
    return None


def _siralar(degerler: Sequence[float]) -> list[float]:
    """1'den başlayan sıralar; eşit değerler sıralarının ortalamasını alır."""
    sira = sorted(range(len(degerler)), key=lambda i: degerler[i])
    sonuc = [0.0] * len(degerler)
    i = 0
    while i < len(sira):
        j = i
        while j + 1 < len(sira) and degerler[sira[j + 1]] == degerler[sira[i]]:
            j += 1
        for m in range(i, j + 1):
            sonuc[sira[m]] = (i + j) / 2 + 1
        i = j + 1
    return sonuc


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Sıralar üzerinden Pearson korelasyonu (eşitlikte ortalama sıra)."""
    rx, ry = _siralar(x), _siralar(y)
    n = len(rx)
    ox, oy = sum(rx) / n, sum(ry) / n
    pay = sum((a - ox) * (b - oy) for a, b in zip(rx, ry))
    payda = math.sqrt(
        sum((a - ox) ** 2 for a in rx) * sum((b - oy) ** 2 for b in ry)
    )
    return pay / payda


def t_istatistigi(rho: float, n: int) -> float:
    """H0: ρ = 0 için yaklaşık t, n − 2 serbestlik derecesi."""
    if rho * rho >= 1:
        return math.copysign(math.inf, rho)
    return rho * math.sqrt((n - 2) / (1 - rho * rho))


def ozetle(satirlar: Sequence[SozSatiri]) -> SozOzeti | None:
    """Üç eşit grup, grup medyanları ve Spearman sıra korelasyonu.

    Sıralama yoğunluğa göre, eşitlikte ticker'a göre (belirlenimci).
    n üçe bölünmüyorsa artan satırlar son gruba gider. Üç satırdan azla
    özet kurulmaz.
    """
    if len(satirlar) < 3:
        return None
    sirali = sorted(satirlar, key=lambda s: (s.yogunluk, s.ticker))
    n = len(sirali)
    k = n // 3
    dilimler = (sirali[:k], sirali[k : 2 * k], sirali[2 * k :])
    gruplar = tuple(
        Grup(
            ad=ad,
            satirlar=tuple(d),
            medyan_buyume=median(s.buyume for s in d),
            medyan_yogunluk=median(s.yogunluk for s in d),
        )
        for ad, d in zip(GRUP_ADLARI, dilimler)
    )
    rho = spearman([s.yogunluk for s in sirali], [s.buyume for s in sirali])
    alt_en_iyi = max(gruplar[0].medyan_buyume, gruplar[1].medyan_buyume)
    return SozOzeti(
        n=n,
        gruplar=gruplar,
        rho=rho,
        t=t_istatistigi(rho, n),
        ust_grup_onde=gruplar[2].medyan_buyume - alt_en_iyi > ONDE_ESIGI,
    )
