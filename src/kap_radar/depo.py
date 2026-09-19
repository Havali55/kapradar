"""Ayrıştırılmış bildirimlerin Postgres'e yazılması.

Idempotency tek satırla çözülüyor (spec §5): `bildirim` upsert'i
`on conflict do nothing`. Backfill ikinci kez koşsa, poller'la çakışsa
ya da çekim yarıda kalsa mükerrer kayıt oluşmaz.

Bu modül ayrıştırma yapmaz; `ayristirici.Bildirim` ne ürettiyse satır
odur. Şema bilgisi tek yerde kalsın diye sütun listesi de burada.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from psycopg.types.json import Jsonb

from kap_radar.ayristirici import Bildirim

BILDIRIM_SUTUNLARI: tuple[str, ...] = (
    "kap_id",
    "kap_index",
    "ticker",
    "sirket_unvani",
    "mkk_uye_oid",
    "sablon_kodu",
    "sablon_adi",
    "yayin_zamani",
    "ozet",
    "ham_govde_html",
    "ham_metin_tr",
    "ham_metin_en",
    "kaynak_url",
    "ek_sayisi",
    "guncelleme_mi",
    "duzeltme_mi",
    "onceki_aciklama_tarihleri",
    "ilgili_kap_id",
    "kap_alanlari",
)

# `on conflict do nothing` hedefsiz bırakıldı: kap_id'nin yanında
# kap_index de tekil. Hedef verilirse ikinci kısıt ihlali yakalanmaz ve
# yükleme ortasında patlar.
BILDIRIM_UPSERT = (
    f"insert into public.bildirim ({', '.join(BILDIRIM_SUTUNLARI)}) "
    f"values ({', '.join('%(' + s + ')s' for s in BILDIRIM_SUTUNLARI)}) "
    "on conflict do nothing returning kap_id"
)

# Şirket satırı ilk bildirimde açılır; hasılat Adım 7'de dolar.
SIRKET_UPSERT = (
    "insert into public.sirket (ticker, unvan, mkk_uye_oid) "
    "values (%(ticker)s, %(unvan)s, %(mkk_uye_oid)s) on conflict do nothing"
)

KONTROL_NOKTASI_UPSERT = (
    "insert into public.cekim_durumu "
    "(anahtar, son_islenen_tarih, son_islenen_index, notlar, guncellendi_at) "
    "values (%(anahtar)s, %(tarih)s, %(indeks)s, %(notlar)s, now()) "
    "on conflict (anahtar) do update set "
    "son_islenen_tarih = excluded.son_islenen_tarih, "
    "son_islenen_index = excluded.son_islenen_index, "
    "notlar = excluded.notlar, guncellendi_at = now()"
)


def _json_uyumlu(deger: Any) -> Any:
    """jsonb'ye gidecek yapıdaki tarihleri ISO metne indirger.

    `kap_alanlari["baslangic"]` bir `date`; ham hâliyle serileştirilemez.
    """
    if isinstance(deger, (date, datetime)):
        return deger.isoformat()
    if isinstance(deger, dict):
        return {anahtar: _json_uyumlu(alt) for anahtar, alt in deger.items()}
    if isinstance(deger, list):
        return [_json_uyumlu(alt) for alt in deger]
    return deger


def bildirim_satiri(bildirim: Bildirim) -> dict[str, Any]:
    """`Bildirim`i `bildirim` tablosunun sütunlarına eşler."""
    satir = {sutun: getattr(bildirim, sutun) for sutun in BILDIRIM_SUTUNLARI}
    satir["kap_alanlari"] = _json_uyumlu(bildirim.kap_alanlari)
    return satir


class Depo:
    """Açık bir psycopg bağlantısı üzerinden yazar.

    İşlem yönetimi çağırana ait: 1.100 satırı tek tek commit etmek
    gereksiz yavaş, hiç commit etmemek ise kesintide her şeyi kaybettirir.
    Yükleyici aralıklarla commit eder.
    """

    def __init__(self, baglanti) -> None:
        self._baglanti = baglanti

    def bildirim_kaydet(self, bildirim: Bildirim) -> bool:
        """Bildirimi yazar; zaten varsa dokunmaz.

        Dönüş: satır gerçekten eklendiyse True.
        """
        satir = bildirim_satiri(bildirim)
        satir["kap_alanlari"] = Jsonb(satir["kap_alanlari"])

        with self._baglanti.cursor() as imlec:
            if bildirim.ticker:
                imlec.execute(
                    SIRKET_UPSERT,
                    {
                        "ticker": bildirim.ticker,
                        "unvan": bildirim.sirket_unvani,
                        "mkk_uye_oid": bildirim.mkk_uye_oid,
                    },
                )
            imlec.execute(BILDIRIM_UPSERT, satir)
            return imlec.fetchone() is not None

    def sirket_var_mi(self, ticker: str) -> bool:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select 1 from public.sirket where ticker = %s", (ticker,)
            )
            return imlec.fetchone() is not None

    def kontrol_noktasi_yaz(
        self,
        anahtar: str,
        *,
        son_islenen_tarih: date | None = None,
        son_islenen_index: int | None = None,
        notlar: dict | None = None,
    ) -> None:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                KONTROL_NOKTASI_UPSERT,
                {
                    "anahtar": anahtar,
                    "tarih": son_islenen_tarih,
                    "indeks": son_islenen_index,
                    "notlar": Jsonb(_json_uyumlu(notlar or {})),
                },
            )

    def kontrol_noktasi_oku(self, anahtar: str) -> dict | None:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select son_islenen_tarih, son_islenen_index, notlar "
                "from public.cekim_durumu where anahtar = %s",
                (anahtar,),
            )
            satir = imlec.fetchone()
        if satir is None:
            return None
        return {
            "son_islenen_tarih": satir[0],
            "son_islenen_index": satir[1],
            "notlar": satir[2],
        }
