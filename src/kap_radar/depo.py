"""Ayrıştırılmış bildirimlerin Postgres'e yazılması.

Idempotency tek satırla çözülüyor (spec §5): `bildirim` upsert'i
`on conflict do nothing`. Backfill ikinci kez koşsa, poller'la çakışsa
ya da çekim yarıda kalsa mükerrer kayıt oluşmaz.

Bu modül ayrıştırma yapmaz; `ayristirici.Bildirim` ne ürettiyse satır
odur. Şema bilgisi tek yerde kalsın diye sütun listesi de burada.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from psycopg.types.json import Jsonb

from kap_radar.ayristirici import Bildirim
from kap_radar.cikarim import CikarimMeta, TutarCikarimi
from kap_radar.finansal import DonemHasilat

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

# Yayınlanmış bülten sonradan değişmiyor: çakışmada güncelleme değil,
# dokunmama doğru davranış.
KUR_UPSERT = (
    "insert into public.kur_gunluk (tarih, para_birimi, tl_karsiligi) "
    "values (%(tarih)s, %(para_birimi)s, %(tl)s) "
    "on conflict do nothing returning tarih"
)

FIYAT_UPSERT = (
    "insert into public.fiyat_gunluk (ticker, tarih, kapanis_duzeltilmis, hacim) "
    "values (%(ticker)s, %(tarih)s, %(kapanis)s, %(hacim)s) "
    "on conflict do nothing returning tarih"
)

ENDEKS_UPSERT = (
    "insert into public.endeks_gunluk (tarih, xu100_kapanis) "
    "values (%(tarih)s, %(kapanis)s) on conflict do nothing returning tarih"
)

# Tepki türetilmiş veri: fiyat serisi tamamlandıkça ya da pencere tanımı
# değiştikçe tazelenmeli. Bildirimin aksine dondurulmuyor.
TEPKI_UPSERT = (
    "insert into public.tepki "
    "(kap_id, t0, car_1g, car_3g, car_5g, pencere_basi, hesaplandi_at) "
    "values (%(kap_id)s, %(t0)s, %(car_1g)s, %(car_3g)s, %(car_5g)s, "
    "%(pencere_basi)s, now()) "
    "on conflict (kap_id) do update set "
    "t0 = excluded.t0, car_1g = excluded.car_1g, car_3g = excluded.car_3g, "
    "car_5g = excluded.car_5g, pencere_basi = excluded.pencere_basi, "
    "hesaplandi_at = now()"
)

# Yayınlanmış finansal rapor değişmez; düzeltilmiş rapor KAP'a yeni bir
# indeksle düşer. Dolayısıyla çakışmada güncelleme değil dokunmama doğru.
FINANSAL_SUTUNLARI: tuple[str, ...] = (
    "kap_index",
    "ticker",
    "yayin_zamani",
    "donem_basi",
    "donem_sonu",
    "ay_sayisi",
    "hasilat",
    "onceki_yil_hasilat",
    "onceki_donem_sonu",
    "para_birimi",
    "konsolide",
    "birim_carpani",
)

FINANSAL_UPSERT = (
    f"insert into public.finansal_donem ({', '.join(FINANSAL_SUTUNLARI)}) "
    f"values ({', '.join('%(' + s + ')s' for s in FINANSAL_SUTUNLARI)}) "
    "on conflict (kap_index) do nothing returning kap_index"
)

SIRKET_HASILAT_GUNCELLE = (
    "update public.sirket set son_yillik_hasilat_tl = %(hasilat_tl)s, "
    "hasilat_donemi = %(donem)s, hasilat_kaynak = %(kaynak)s, "
    "guncellendi_at = now() where ticker = %(ticker)s"
)

# `cikarim` APPEND-ONLY (spec §5): prompt ya da şema değişince yeni satır
# yazılır, eski silinmez. "Bu sayfadaki sayıyı hangi model, hangi prompt,
# hangi şema üretti" her zaman cevaplanabilir kalmalı.
CIKARIM_SUTUNLARI: tuple[str, ...] = (
    "kap_id",
    "model",
    "katman",
    "prompt_versiyon",
    "sema_versiyon",
    "veri",
    "guven",
    "yayina_hazir",
    "red_nedeni",
    "net_tutar_tl",
    "ciro_orani",
    "etki_skoru",
    "girdi_token",
    "cikti_token",
)

CIKARIM_EKLE = (
    f"insert into public.cikarim ({', '.join(CIKARIM_SUTUNLARI)}) "
    f"values ({', '.join('%(' + s + ')s' for s in CIKARIM_SUTUNLARI)}) "
    "returning id"
)

# Kur çözümünde geriye yürüme sınırı. Uzun tatiller (9 günü bulabiliyor)
# kapsansın, ama üç ay öncesine düşülmesin.
AZAMI_GERI_GUN = 10

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

    def kur_kaydet(self, tarih: date, kurlar: dict[str, Decimal]) -> int:
        """Bir günün kurlarını yazar; zaten varsa dokunmaz.

        Dönüş: gerçekten eklenen satır sayısı. Yayınlanmış bir bülten
        sonradan değişmediği için güncelleme yapılmıyor.
        """
        if not kurlar:
            return 0

        with self._baglanti.cursor() as imlec:
            imlec.executemany(
                KUR_UPSERT,
                [
                    {"tarih": tarih, "para_birimi": kod, "tl": deger}
                    for kod, deger in sorted(kurlar.items())
                ],
                returning=True,
            )
            return self._eklenen_say(imlec)

    def kur_coz(
        self, tarih: date, para_birimi: str, azami_geri_gun: int = AZAMI_GERI_GUN
    ) -> tuple[date, Decimal] | None:
        """Bildirim tarihli kuru verir; o gün yayın yoksa önceki iş gününü.

        Spec §8'in kuralı burada tek yerde duruyor. Geri yürüme sınırlı:
        üç ay önceki kurla çevirmek sessizce yanlış bir rakam üretir,
        bulunamayan kur §6'nın B2 kapısında elle incelemeye düşer.
        """
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select tarih, tl_karsiligi from public.kur_gunluk "
                "where para_birimi = %(para_birimi)s "
                "and tarih between %(alt)s and %(tarih)s "
                "order by tarih desc limit 1",
                {
                    "para_birimi": para_birimi,
                    "tarih": tarih,
                    "alt": tarih - timedelta(days=azami_geri_gun),
                },
            )
            satir = imlec.fetchone()
        return (satir[0], satir[1]) if satir else None

    def fiyat_kaydet(
        self,
        ticker: str,
        kapanislar: dict[date, Decimal],
        hacimler: dict[date, int] | None = None,
    ) -> int:
        """Bir hissenin günlük kapanışlarını yazar; olanlara dokunmaz.

        Dönüş: eklenen satır sayısı. Fiyat batch'i her gün koşacağı için
        geçmiş günlerin yeniden yazılmaması gerekiyor.
        """
        if not kapanislar:
            return 0
        hacimler = hacimler or {}

        with self._baglanti.cursor() as imlec:
            imlec.executemany(
                FIYAT_UPSERT,
                [
                    {
                        "ticker": ticker,
                        "tarih": gun,
                        "kapanis": kapanislar[gun],
                        "hacim": hacimler.get(gun),
                    }
                    for gun in sorted(kapanislar)
                ],
                returning=True,
            )
            return self._eklenen_say(imlec)

    def fiyat_serisi(
        self, ticker: str, baslangic: date, bitis: date
    ) -> dict[date, Decimal]:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select tarih, kapanis_duzeltilmis from public.fiyat_gunluk "
                "where ticker = %s and tarih between %s and %s",
                (ticker, baslangic, bitis),
            )
            return {satir[0]: satir[1] for satir in imlec.fetchall()}

    def endeks_kaydet(self, kapanislar: dict[date, Decimal]) -> int:
        if not kapanislar:
            return 0

        with self._baglanti.cursor() as imlec:
            imlec.executemany(
                ENDEKS_UPSERT,
                [
                    {"tarih": gun, "kapanis": kapanislar[gun]}
                    for gun in sorted(kapanislar)
                ],
                returning=True,
            )
            return self._eklenen_say(imlec)

    def endeks_serisi(self, baslangic: date, bitis: date) -> dict[date, Decimal]:
        """XU100 kapanışları — aynı zamanda BIST işlem takvimi.

        Endeksin kapanışı olan gün seans var demektir; elle bakılan bir
        tatil listesi eskir, bu seri kendini güncel tutar (spec §8).
        """
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select tarih, xu100_kapanis from public.endeks_gunluk "
                "where tarih between %s and %s",
                (baslangic, bitis),
            )
            return {satir[0]: satir[1] for satir in imlec.fetchall()}

    def tepki_kaydet(
        self,
        kap_id: str,
        *,
        t0: date,
        car_1g: Decimal | None = None,
        car_3g: Decimal | None = None,
        car_5g: Decimal | None = None,
        pencere_basi: int = 0,
    ) -> None:
        """Tepkiyi yazar; varsa günceller.

        Bildirimin kendisi dondurulur ama tepki türetilmiş veri: fiyat
        serisi tamamlandıkça ya da pencere tanımı değiştikçe tazelenir.
        """
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                TEPKI_UPSERT,
                {
                    "kap_id": kap_id,
                    "t0": t0,
                    "car_1g": car_1g,
                    "car_3g": car_3g,
                    "car_5g": car_5g,
                    "pencere_basi": pencere_basi,
                },
            )

    def tepki_oku(self, kap_id: str) -> dict | None:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select t0, car_1g, car_3g, car_5g, pencere_basi "
                "from public.tepki where kap_id = %s",
                (kap_id,),
            )
            satir = imlec.fetchone()
        if satir is None:
            return None
        return dict(
            zip(("t0", "car_1g", "car_3g", "car_5g", "pencere_basi"), satir)
        )

    # ------------------------------------------------------------ çıkarım

    def cikarim_kaydet(
        self,
        kap_id: str,
        *,
        cikarim: TutarCikarimi,
        meta: CikarimMeta,
        yayina_hazir: bool,
        red_nedeni: str | None = None,
        net_tutar_tl: Decimal | None = None,
        ciro_orani: Decimal | None = None,
        etki_skoru: Decimal | None = None,
    ) -> int:
        """Bir çıkarımı yazar. Hiçbir zaman güncellemez, hep ekler.

        §8 hesapları da satıra yazılıyor: hasılat sonradan güncellense
        bile sayfanın o gün neyi neden gösterdiği izlenebilir kalır.
        """
        satir = {
            "kap_id": kap_id,
            "model": meta.model,
            "katman": meta.katman,
            "prompt_versiyon": meta.prompt_versiyon,
            "sema_versiyon": meta.sema_versiyon,
            "veri": Jsonb(cikarim.model_dump(mode="json")),
            "guven": cikarim.guven,
            "yayina_hazir": yayina_hazir,
            "red_nedeni": red_nedeni,
            "net_tutar_tl": net_tutar_tl,
            "ciro_orani": ciro_orani,
            "etki_skoru": etki_skoru,
            "girdi_token": meta.girdi_token,
            "cikti_token": meta.cikti_token,
        }
        with self._baglanti.cursor() as imlec:
            imlec.execute(CIKARIM_EKLE, satir)
            return imlec.fetchone()[0]

    def cikarim_sayisi(self, kap_id: str) -> int:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select count(*) from public.cikarim where kap_id = %s", (kap_id,)
            )
            return imlec.fetchone()[0]

    def son_yayina_hazir(self, kap_id: str) -> dict | None:
        """Yayında olan çıkarım: `yayina_hazir=true` olan en son satır (spec §5)."""
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select id, model, katman, veri, net_tutar_tl, ciro_orani, etki_skoru "
                "from public.cikarim where kap_id = %s and yayina_hazir "
                "order by olusturuldu_at desc, id desc limit 1",
                (kap_id,),
            )
            satir = imlec.fetchone()
        if satir is None:
            return None
        return dict(
            zip(
                (
                    "id",
                    "model",
                    "katman",
                    "veri",
                    "net_tutar_tl",
                    "ciro_orani",
                    "etki_skoru",
                ),
                satir,
            )
        )

    # ------------------------------------------------------- finansal dönem

    def finansal_kaydet(self, donem: DonemHasilat) -> bool:
        """Bir finansal raporun hasılat satırını yazar; varsa dokunmaz.

        Dönüş: satır gerçekten eklendiyse True. Çekim tekrar koşturulabilir
        olsun diye idempotent.
        """
        satir = {sutun: getattr(donem, sutun) for sutun in FINANSAL_SUTUNLARI}
        with self._baglanti.cursor() as imlec:
            imlec.execute(FINANSAL_UPSERT, satir)
            return imlec.fetchone() is not None

    def donem_hasilatlari(self, ticker: str) -> list[DonemHasilat]:
        """Bir şirketin tüm dönem hasılatları.

        Point-in-time süzme burada değil `finansal.ttm_coz` içinde: o saf
        fonksiyon, testi ağ ve veritabanı olmadan koşuyor. Depo yalnız
        satırları veriyor.
        """
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                f"select {', '.join(FINANSAL_SUTUNLARI)} "
                "from public.finansal_donem where ticker = %s "
                "order by donem_sonu, yayin_zamani",
                (ticker,),
            )
            return [
                DonemHasilat(**dict(zip(FINANSAL_SUTUNLARI, satir)))
                for satir in imlec.fetchall()
            ]

    def sirket_hasilat_guncelle(
        self,
        ticker: str,
        *,
        hasilat_tl: Decimal | None,
        donem: str | None,
        kaynak: str | None,
    ) -> None:
        """`sirket` üzerindeki tek satırlık TTM önbelleğini tazeler.

        Sitenin "son yıllık hasılat" alanı burayı okuyor; skorun paydası
        okumuyor (spec §8 — o point-in-time olmak zorunda).
        """
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                SIRKET_HASILAT_GUNCELLE,
                {
                    "ticker": ticker,
                    "hasilat_tl": hasilat_tl,
                    "donem": donem,
                    "kaynak": kaynak,
                },
            )

    def sirket_hasilati(self, ticker: str) -> dict | None:
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select son_yillik_hasilat_tl, hasilat_donemi, hasilat_kaynak "
                "from public.sirket where ticker = %s",
                (ticker,),
            )
            satir = imlec.fetchone()
        if satir is None:
            return None
        return dict(
            zip(("son_yillik_hasilat_tl", "hasilat_donemi", "hasilat_kaynak"), satir)
        )

    def tickerlar(self) -> list[str]:
        """Bildirimi olan şirketlerin ticker'ları."""
        with self._baglanti.cursor() as imlec:
            imlec.execute(
                "select distinct ticker from public.sirket "
                "where ticker is not null order by ticker"
            )
            return [satir[0] for satir in imlec.fetchall()]

    @staticmethod
    def _eklenen_say(imlec) -> int:
        """`executemany(returning=True)` sonuç kümelerini sayar."""
        eklenen = 0
        while True:
            if imlec.fetchone() is not None:
                eklenen += 1
            if not imlec.nextset():
                break
        return eklenen

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
