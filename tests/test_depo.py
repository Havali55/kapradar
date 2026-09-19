"""Veritabanı deposunun testleri.

İkiye ayrılıyor: satır eşlemesi saf fonksiyon olduğu için normal birim
testi; gerçek upsert davranışı ise canlı Postgres istiyor ve
DATABASE_URL yoksa atlanıyor.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date
from decimal import Decimal
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


@pytest.fixture
def sahte_bildirim(orge_bildirimi):
    """Yüklenmiş gerçek veriyle çakışmayan bir kopya.

    Backfill'in 613 bildirimi artık veritabanında duruyor; test kendi ön
    koşulunu kuramazsa "ilk yazma" iddiası anlamını yitirir. `mkk_uye_oid`
    de değişiyor: `sirket` tablosunda tekil ve gerçek ORGE satırıyla
    çakışırsa şirket satırı hiç açılmaz.
    """
    return replace(
        orge_bildirimi,
        kap_id="zztest-kap-id",
        kap_index=999_999_999,
        ticker="ZZTEST",
        sirket_unvani="DEPO TESTİ A.Ş.",
        mkk_uye_oid="oid-zztest",
    )


@canli_db
def test_ayni_bildirim_iki_kez_yazilmaz(depo, sahte_bildirim):
    """Backfill canlı poller'la çakışsa bile mükerrer kayıt oluşmamalı (spec §5)."""
    assert depo.bildirim_kaydet(sahte_bildirim) is True
    assert depo.bildirim_kaydet(sahte_bildirim) is False


@canli_db
def test_bildirim_yazilirken_sirket_satiri_acilir(depo, sahte_bildirim):
    """`bildirim.ticker` yabancı anahtar; şirket yoksa yazma düşer.

    Hasılat Adım 7'de dolacak, ama satırın kendisi ilk bildirimde açılır.
    """
    assert depo.sirket_var_mi("ZZTEST") is False

    depo.bildirim_kaydet(sahte_bildirim)

    assert depo.sirket_var_mi("ZZTEST") is True


@canli_db
def test_kur_ayni_gun_icin_iki_kez_yazilmaz(depo):
    """Kur çekici tekrar koşturulabilmeli; bülten yayınlandıktan sonra değişmez."""
    kurlar = {"USD": Decimal("0.1234"), "EUR": Decimal("0.5678")}

    assert depo.kur_kaydet(date(1999, 1, 8), kurlar) == 2
    assert depo.kur_kaydet(date(1999, 1, 8), kurlar) == 0


@canli_db
def test_kur_coz_hafta_sonunda_onceki_is_gununu_verir(depo):
    """Spec §8: bildirim tatil/hafta sonu gününde ise önceki iş günü kuru.

    Kural tek yerde yaşamalı; her çağıran kendi geri yürümesini yazarsa
    biri mutlaka bir gün kayar.
    """
    depo.kur_kaydet(date(1999, 1, 8), {"USD": Decimal("0.1234")})  # Cuma

    assert depo.kur_coz(date(1999, 1, 10), "USD") == (
        date(1999, 1, 8),
        Decimal("0.1234"),
    )


@canli_db
def test_kur_coz_uzak_gecmise_yurumez(depo):
    """Üç ay önceki kurla çevirmek sessizce yanlış bir rakam üretir.

    Bulunamadığında None dönüyor; §6'nın B2 kapısı bildirimi elle
    incelemeye düşürecek.
    """
    depo.kur_kaydet(date(1999, 1, 8), {"USD": Decimal("0.1234")})

    assert depo.kur_coz(date(1999, 3, 1), "USD") is None


@canli_db
def test_fiyat_serisi_yazilip_geri_okunur(depo):
    """CAR hesabı seriyi DB'den okuyor; yazılan ile okunan aynı olmalı."""
    kapanislar = {date(1999, 1, 8): Decimal("10.5"), date(1999, 1, 11): Decimal("11")}

    depo.fiyat_kaydet("ORGE", kapanislar, {date(1999, 1, 8): 1234})

    assert depo.fiyat_serisi("ORGE", date(1999, 1, 1), date(1999, 1, 31)) == kapanislar


@canli_db
def test_ayni_gunun_fiyati_iki_kez_yazilmaz(depo):
    """Fiyat batch'i her gün koşuyor; geçmiş günleri tekrar yazmamalı."""
    kapanislar = {date(1999, 1, 8): Decimal("10.5")}

    assert depo.fiyat_kaydet("ORGE", kapanislar, {}) == 1
    assert depo.fiyat_kaydet("ORGE", kapanislar, {}) == 0


@canli_db
def test_endeks_serisi_islem_takvimini_verir(depo):
    """İşlem günleri ayrı bir tatil tablosundan değil endeks serisinden geliyor."""
    depo.endeks_kaydet({date(1999, 1, 8): Decimal("1000"), date(1999, 1, 11): Decimal("1010")})

    seri = depo.endeks_serisi(date(1999, 1, 1), date(1999, 1, 31))

    assert sorted(seri) == [date(1999, 1, 8), date(1999, 1, 11)]


@canli_db
def test_tepki_yeniden_hesaplanirsa_guncellenir(depo):
    """Fiyat/pencere değişince tepki tazelenmeli — bildirim gibi dondurulmaz."""
    kap_id = "4028328ca09bee9001a0b53d7b914cac"  # yüklenmiş ORGE bildirimi

    depo.tepki_kaydet(kap_id, t0=date(2026, 9, 21), car_3g=Decimal("0.02"))
    depo.tepki_kaydet(kap_id, t0=date(2026, 9, 21), car_3g=Decimal("0.05"))

    assert depo.tepki_oku(kap_id)["car_3g"] == Decimal("0.05")


@canli_db
def test_kontrol_noktasi_yazilip_okunur(depo):
    """Yükleme nerede kaldı — koşu kesilirse buradan devam edilir (spec §9)."""
    depo.kontrol_noktasi_yaz("test_backfill", son_islenen_index=1665567)

    durum = depo.kontrol_noktasi_oku("test_backfill")

    assert durum["son_islenen_index"] == 1665567
