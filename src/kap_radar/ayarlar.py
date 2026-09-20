"""`.env` okuması ve veritabanı DSN'i.

Bu mantık `scripts/` altında dokuz kez kopyalanmıştı; yeni betikler
buradan alıyor (eskiler dokunulmadan çalışmaya devam ediyor).
"""

from __future__ import annotations

import os
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent.parent
VARSAYILAN_ENV = KOK / ".env"

# Depoda `.env.example` bu yer tutucuyla duruyor. Onunla bağlanmayı
# denemek anlaşılmaz bir psycopg hatası verir; erken ve anlaşılır reddet.
PAROLA_YER_TUTUCU = "<PAROLA>"


def env_oku(yol: Path = VARSAYILAN_ENV) -> dict[str, str]:
    """`.env` dosyasını sözlüğe çevirir; yoksa boş döner."""
    if not yol.exists():
        return {}
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def dsn_bul(yol: Path = VARSAYILAN_ENV) -> str | None:
    """Ortamdan ya da `.env`'den DATABASE_URL; yer tutucu varsa None."""
    dsn = os.environ.get("DATABASE_URL") or env_oku(yol).get("DATABASE_URL", "")
    return dsn if dsn and PAROLA_YER_TUTUCU not in dsn else None
