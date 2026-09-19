"""Veritabanı deposunun testleri.

İkiye ayrılıyor: satır eşlemesi saf fonksiyon olduğu için normal birim
testi; gerçek upsert davranışı ise canlı Postgres istiyor ve
DATABASE_URL yoksa atlanıyor.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import pytest

from kap_radar.ayristirici import bildirim_ayristir
from kap_radar.depo import BILDIRIM_SUTUNLARI, Depo, bildirim_satiri

FIXTURE = Path(__file__).parent / "fixtures"


@pytest.fixture
def orge_bildirimi():
    ham = json.loads(
        (FIXTURE / "detay_orge_1665567.json").read_text(encoding="utf-8")
    )
    return bildirim_ayristir(ham[0])


def test_satir_sema_sutunlariyla_birebir_eslesir(orge_bildirimi):
    """Eksik sütun NOT NULL ihlali, fazlası UndefinedColumn — ikisi de koşuyu keser."""
    satir = bildirim_satiri(orge_bildirimi)

    assert set(satir) == set(BILDIRIM_SUTUNLARI)


def test_kap_alanlarindaki_tarih_json_uyumlu_hale_gelir(orge_bildirimi):
    """`baslangic` bir `date`; ham hâliyle json.dumps'a verilirse TypeError.

    jsonb'ye gitmeden önce ISO metne indirgeniyor; Postgres tarafında
    tarih karşılaştırması gerekirse `(kap_alanlari->>'baslangic')::date`
    zaten çalışır.
    """
    satir = bildirim_satiri(orge_bildirimi)

    assert satir["kap_alanlari"]["baslangic"] == "2023-05-10"
    assert json.dumps(satir["kap_alanlari"])


def test_onceki_tarihler_date_listesi_olarak_kalir(orge_bildirimi):
    """`date[]` sütunu; psycopg listeyi kendisi uyarlıyor, metne çevrilmemeli."""
    satir = bildirim_satiri(orge_bildirimi)

    assert satir["onceki_aciklama_tarihleri"] == [
        date(2023, 5, 10),
        date(2023, 6, 14),
        date(2024, 1, 3),
        date(2025, 2, 7),
    ]


# --------------------------------------------------------------- canlı DB


def dsn_bul() -> str | None:
    """DATABASE_URL'i ortamdan ya da .env'den alır; yer tutucu varsa yok sayar."""
    dsn = os.environ.get("DATABASE_URL", "")
    env = Path(__file__).resolve().parent.parent / ".env"
    if not dsn and env.exists():
        for satir in env.read_text(encoding="utf-8").splitlines():
            if satir.strip().startswith("DATABASE_URL="):
                dsn = satir.split("=", 1)[1].strip()
    return dsn if dsn and "<PAROLA>" not in dsn else None


canli_db = pytest.mark.skipif(
    dsn_bul() is None, reason="DATABASE_URL yok ya da parola yer tutucusu duruyor"
)


@pytest.fixture
def depo():
    import psycopg

    with psycopg.connect(dsn_bul(), connect_timeout=20) as baglanti:
        yield Depo(baglanti)
        baglanti.rollback()


@canli_db
def test_ayni_bildirim_iki_kez_yazilmaz(depo, orge_bildirimi):
    """Backfill canlı poller'la çakışsa bile mükerrer kayıt oluşmamalı (spec §5)."""
    assert depo.bildirim_kaydet(orge_bildirimi) is True
    assert depo.bildirim_kaydet(orge_bildirimi) is False


@canli_db
def test_bildirim_yazilirken_sirket_satiri_acilir(depo, orge_bildirimi):
    """`bildirim.ticker` yabancı anahtar; şirket yoksa yazma düşer.

    Hasılat Adım 7'de dolacak, ama satırın kendisi ilk bildirimde açılır.
    """
    depo.bildirim_kaydet(orge_bildirimi)

    assert depo.sirket_var_mi("ORGE") is True


@canli_db
def test_kontrol_noktasi_yazilip_okunur(depo):
    """Yükleme nerede kaldı — koşu kesilirse buradan devam edilir (spec §9)."""
    depo.kontrol_noktasi_yaz("test_backfill", son_islenen_index=1665567)

    durum = depo.kontrol_noktasi_oku("test_backfill")

    assert durum["son_islenen_index"] == 1665567
