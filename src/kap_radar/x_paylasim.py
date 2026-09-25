"""X (Twitter) paylaşımı: tweet metni, OAuth 1.0a imzası, gönderim.

Üç parça, üçü de ayrı sınanıyor:
  - `tweet_metni`: akış satırından tek satırlık metin. Saf fonksiyon.
  - `oauth_basligi`: OAuth 1.0a (HMAC-SHA1) Authorization başlığı. Nonce
    ve zaman çağırandan geliyor, böylece X belgesindeki örnek imzayla
    birebir sınanabiliyor.
  - `XIstemci`: iki uç nokta. `ben` anahtarları tweet atmadan doğrular
    (GET /2/users/me), `gonder` paylaşır (POST /2/tweets).

İmza için kütüphane eklenmedi: gereken tek şey bir HMAC-SHA1. Test
vektörü bağımsız bir uygulamayla (oauthlib) üretildi.

Gönderim YENİDEN DENENMİYOR. POST /2/tweets idempotent değil; zaman
aşımından sonra tekrar denemek aynı tweet'i iki kez atabilir. Tekrarı
önleyen kayıt `x_paylasim` tablosunda (bkz. migration 20260925000001).

Hangi bildirim aday: yayına hazır (akış view'ı), büyüklüğü bilinen,
`PAYLASIM_BASLANGICI`'ndan sonra yayınlanmış, `AZAMI_YAS`'tan genç ve
daha önce paylaşılmamış. Başlangıç tarihi, 2024-09'dan beri biriken
arşivin hiçbir zaman tweet'lenmemesi için var.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from kap_radar.ayarlar import VARSAYILAN_ENV, env_oku
from kap_radar import karsi_taraf as _karsi_taraf
from kap_radar.skor import buyukluk_kademesi

__all__ = [
    "AZAMI_YAS",
    "PAYLASIM_BASLANGICI",
    "SITE_KOKU",
    "XAnahtarlari",
    "XHatasi",
    "XIstemci",
    "adaylari_sec",
    "anahtarlari_bul",
    "oauth_basligi",
    "tweet_metni",
    "x_uzunlugu",
]

PAYLASIM_BASLANGICI = datetime(2026, 9, 25, tzinfo=ZoneInfo("Europe/Istanbul"))

# Koşu hafta içi akşam. Cuma 20:00'deki bir bildirim Pazartesi koşusunda
# ~72 saatlik; araya bir tatil girerse ~96. Daha eskisi haber değil.
AZAMI_YAS = timedelta(days=4)

SITE_KOKU = "https://kap.calibresolve.com"
MAKS_UZUNLUK = 280
KUNYE = "Yatırım tavsiyesi değildir"

# Karşı taraf adı bundan uzunsa kısaltılıyor; tweet'in geri kalanı ~120 karakter.
AD_SINIRI = 70

_KADEME_METNI = {"rutin": "Rutin iş", "onemli": "Önemli iş", "mega": "Mega iş"}

# Sitedeki `yuzdeIyelik` ile aynı: ek, tek ondalıklı sayının son rakamının
# okunuşuna uyar (üç → 'ü, altı → 'sı, sıfır → 'ı).
_SON_RAKAM_EKI = ["'ı", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u"]

# Sitedeki `Kiminle` bileşeniyle aynı ölçüt: harfsiz ya da tek noktalık
# değerler isim sayılmıyor.
_HARF = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]{3}")


# --- tweet metni ------------------------------------------------------------


def _yuzde_iyelik(oran: Decimal) -> str:
    """0,0231 → "%2,3'ü". Site ile aynı yuvarlama.

    Site oranı JSON'dan float olarak okuyup `oran * 100`'ü yarımı yukarı
    yuvarlıyor. Burada da aynı float çarpımı kullanılıyor; Decimal ile
    kesin hesap bazı sınır değerlerde sitedekinden bir ondalık farklı
    bir sayı basardı.
    """
    yuzde = Decimal(float(oran) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    tam, ondalik = f"{yuzde:.1f}".split(".")
    metin = f"%{int(tam):,}".replace(",", ".") + f",{ondalik}"
    return metin + _SON_RAKAM_EKI[int(metin[-1])]


def _kiminle(karsi_taraf: str | None, acik: bool | None) -> str:
    # Sınıflandırılmamış satır (None) kanonik sınıflandırıcıdan geçiyor;
    # "alan dolu = isim" kuralına geri düşmek 2026-09-24'te düzeltilen hata olurdu.
    if acik is None:
        acik = _karsi_taraf.karsi_taraf_acik(karsi_taraf)
    if not (acik and karsi_taraf and _HARF.search(karsi_taraf)):
        return "adı verilmemiş"
    ad = " ".join(karsi_taraf.split())
    return ad if len(ad) <= AD_SINIRI else ad[: AD_SINIRI - 1].rstrip() + "…"


def tweet_metni(
    *,
    kap_id: str,
    ticker: str,
    ciro_orani: Decimal,
    karsi_taraf: str | None,
    karsi_taraf_acik: bool | None,
) -> str:
    """$ORGE · Cirosunun %6,2'si · Önemli iş · Kiminle: … · link · künye"""
    if ciro_orani is None or ciro_orani <= 0:
        raise ValueError(f"{kap_id}: ciro oranı yok, tweet metni kurulamaz")
    kademe = _KADEME_METNI[buyukluk_kademesi(Decimal(ciro_orani))]
    parcalar = [
        f"${ticker}",
        f"Cirosunun {_yuzde_iyelik(Decimal(ciro_orani))}",
        kademe,
        f"Kiminle: {_kiminle(karsi_taraf, karsi_taraf_acik)}",
        f"{SITE_KOKU}/kap/{kap_id}",
        KUNYE,
    ]
    return unicodedata.normalize("NFC", " · ".join(parcalar))


_URL = re.compile(r"https?://\S+")
# X'in ağırlık tablosu (twitter-text v3): bu aralıklar 1, geri kalan 2 sayılır.
_TEK_AGIRLIK = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
_URL_UZUNLUGU = 23  # t.co kısaltması, adresin kendisi ne olursa olsun


def x_uzunlugu(metin: str) -> int:
    """X'in saydığı uzunluk: her URL 23, Latin/Türkçe harf 1, çoğu simge 2."""
    metin = unicodedata.normalize("NFC", metin)
    url_sayisi = len(_URL.findall(metin))
    kalan = _URL.sub("", metin)
    toplam = url_sayisi * _URL_UZUNLUGU
    for harf in kalan:
        kod = ord(harf)
        toplam += 1 if any(a <= kod <= b for a, b in _TEK_AGIRLIK) else 2
    return toplam


# --- aday seçimi ------------------------------------------------------------

_ADAY_SORGUSU = """
select a.kap_id, a.ticker, a.ciro_orani, a.karsi_taraf, a.karsi_taraf_acik,
       a.yayin_zamani
from public.akis a
where a.yayin_zamani >= %(en_eski)s
  and a.ciro_orani > 0
  and not exists (select 1 from public.x_paylasim x where x.kap_id = a.kap_id)
order by a.yayin_zamani, a.kap_id
limit %(adet)s
"""


def adaylari_sec(baglanti, *, simdi: datetime, adet: int) -> list[dict]:
    """Paylaşılacak bildirimler, eskiden yeniye (akış X'te sırayla okunsun)."""
    en_eski = max(PAYLASIM_BASLANGICI, simdi - AZAMI_YAS)
    with baglanti.cursor() as imlec:
        imlec.execute(_ADAY_SORGUSU, {"en_eski": en_eski, "adet": adet})
        sutunlar = [s.name for s in imlec.description]
        return [dict(zip(sutunlar, satir)) for satir in imlec.fetchall()]


# --- OAuth 1.0a -------------------------------------------------------------


@dataclass(frozen=True)
class XAnahtarlari:
    api_key: str
    api_secret: str = field(repr=False)
    access_token: str
    access_token_secret: str = field(repr=False)


_ANAHTAR_ADLARI = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")


def anahtarlari_bul(yol: Path = VARSAYILAN_ENV) -> XAnahtarlari | None:
    """Ortamdan ya da `.env`'den dört anahtar; biri eksikse None."""
    dosya = env_oku(yol)
    degerler = [os.environ.get(ad) or dosya.get(ad, "") for ad in _ANAHTAR_ADLARI]
    return XAnahtarlari(*degerler) if all(degerler) else None


def _kodla(metin: str) -> str:
    """RFC 3986: harf, rakam ve - . _ ~ dışındaki her bayt %XX olur."""
    return quote(metin, safe="~")


def oauth_basligi(
    yontem: str,
    url: str,
    anahtarlar: XAnahtarlari,
    *,
    nonce: str,
    zaman: int,
    parametreler: dict[str, str] | None = None,
) -> str:
    """Authorization başlığı. `url` sorgusuz taban adres; sorgu ve form
    parametreleri `parametreler` ile verilir. JSON gövde imzaya girmez."""
    oauth = {
        "oauth_consumer_key": anahtarlar.api_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(zaman),
        "oauth_token": anahtarlar.access_token,
        "oauth_version": "1.0",
    }
    ciftler = sorted(
        (_kodla(k), _kodla(v)) for k, v in {**(parametreler or {}), **oauth}.items()
    )
    parametre_metni = "&".join(f"{k}={v}" for k, v in ciftler)
    taban = "&".join([yontem.upper(), _kodla(url), _kodla(parametre_metni)])
    anahtar = f"{_kodla(anahtarlar.api_secret)}&{_kodla(anahtarlar.access_token_secret)}"
    ozet = hmac.new(anahtar.encode(), taban.encode(), hashlib.sha1).digest()
    oauth["oauth_signature"] = base64.b64encode(ozet).decode()
    return "OAuth " + ", ".join(f'{_kodla(k)}="{_kodla(v)}"' for k, v in sorted(oauth.items()))


# --- istemci ----------------------------------------------------------------


class XHatasi(Exception):
    """X bir hata cevabı döndü; tweet atılmadı."""

    def __init__(self, durum_kodu: int, govde: str) -> None:
        super().__init__(f"X {durum_kodu}: {govde[:300]}")
        self.durum_kodu = durum_kodu


class XIstemci:
    KOK = "https://api.x.com"

    def __init__(
        self,
        anahtarlar: XAnahtarlari,
        *,
        transport: httpx.BaseTransport | None = None,
        nonce: Callable[[], str] = lambda: secrets.token_hex(16),
        saat: Callable[[], float] = time.time,
        zaman_asimi: float = 30.0,
    ) -> None:
        self._anahtarlar = anahtarlar
        self._nonce = nonce
        self._saat = saat
        self._oturum = httpx.Client(base_url=self.KOK, transport=transport, timeout=zaman_asimi)

    def _istek(self, yontem: str, yol: str, **kw) -> dict:
        baslik = oauth_basligi(
            yontem,
            self.KOK + yol,
            self._anahtarlar,
            nonce=self._nonce(),
            zaman=int(self._saat()),
        )
        cevap = self._oturum.request(yontem, yol, headers={"Authorization": baslik}, **kw)
        if not cevap.is_success:
            raise XHatasi(cevap.status_code, cevap.text)
        return cevap.json()

    def ben(self) -> str:
        """Anahtarların sahibi olan hesabın kullanıcı adı. Tweet atmaz."""
        return self._istek("GET", "/2/users/me")["data"]["username"]

    def gonder(self, metin: str) -> str:
        """Tweet'i atar, kimliğini döndürür. Yeniden denemez."""
        return self._istek("POST", "/2/tweets", json={"text": metin})["data"]["id"]

    def kapat(self) -> None:
        self._oturum.close()
