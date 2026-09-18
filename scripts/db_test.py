"""Supabase Postgres baglantisini dogrular.

Kullanim:  python scripts/db_test.py

.env icindeki DATABASE_URL'i okur, baglanir, public semadaki tablolari
listeler. Parolayi hicbir zaman ekrana basmaz.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import psycopg

KOK = Path(__file__).resolve().parent.parent
ENV = KOK / ".env"


def env_oku(yol: Path) -> dict[str, str]:
    if not yol.exists():
        sys.exit(f"{yol} yok. .env.example'i kopyalayip doldurun.")
    veri: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, deger = satir.split("=", 1)
            veri[anahtar.strip()] = deger.strip()
    return veri


def main() -> int:
    env = env_oku(ENV)
    dsn = env.get("DATABASE_URL", "")

    if not dsn:
        sys.exit("DATABASE_URL bos.")
    if "<PAROLA>" in dsn:
        sys.exit(
            "DATABASE_URL icinde hala <PAROLA> yer tutucusu var.\n"
            "Supabase panel > Settings > Database > Reset database password\n"
            "ile uretilen degeri .env dosyasina yazin."
        )

    print("hedef:", re.sub(r"//[^@]+@", "//<gizli>@", dsn))

    try:
        with psycopg.connect(dsn, connect_timeout=20) as baglanti:
            with baglanti.cursor() as imlec:
                imlec.execute("select version(), current_database(), current_user")
                surum, veritabani, kullanici = imlec.fetchone()
                print("BAGLANDI")
                print("  surum :", surum.split(",")[0])
                print("  db    :", veritabani)
                print("  user  :", kullanici)

                imlec.execute(
                    "select table_name from information_schema.tables "
                    "where table_schema = 'public' order by 1"
                )
                tablolar = [satir[0] for satir in imlec.fetchall()]
                print("  public tablolari:", tablolar or "(bos)")
    except psycopg.OperationalError as hata:
        mesaj = str(hata).strip()
        print("BAGLANTI HATASI:", mesaj[:300], file=sys.stderr)
        if "password authentication failed" in mesaj:
            print(
                "\nParola yanlis. Session pooler kullanicisinin "
                "'postgres.<proje-ref>' formatinda oldugunu da dogrulayin.",
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
