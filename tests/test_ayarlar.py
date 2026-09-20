"""`.env` okumasının testleri.

Bu mantık scripts/ altında dokuz kez kopyalanmıştı; yenileri buradan
kullanıyor. Asıl kritik davranış yer tutucu parolanın reddi: `<PAROLA>`
içeren bir DSN'le bağlanmayı denemek anlaşılmaz bir psycopg hatası
veriyor, oysa hata mesajı "parolayı .env'e yaz" demeli.
"""

from __future__ import annotations

from kap_radar.ayarlar import dsn_bul, env_oku


def test_yorum_ve_bos_satirlar_atlanir(tmp_path):
    yol = tmp_path / ".env"
    yol.write_text(
        "# yorum\n\nKAP_USER_AGENT = deneme/1.0\nDATABASE_URL=postgres://x\n",
        encoding="utf-8",
    )

    assert env_oku(yol) == {
        "KAP_USER_AGENT": "deneme/1.0",
        "DATABASE_URL": "postgres://x",
    }


def test_olmayan_env_bos_doner(tmp_path):
    assert env_oku(tmp_path / "yok.env") == {}


def test_yer_tutucu_parolali_dsn_yok_sayilir(tmp_path):
    yol = tmp_path / ".env"
    yol.write_text("DATABASE_URL=postgres://u:<PAROLA>@host/db\n", encoding="utf-8")

    assert dsn_bul(yol) is None


def test_gercek_dsn_doner(tmp_path):
    yol = tmp_path / ".env"
    yol.write_text("DATABASE_URL=postgres://u:s3cr3t@host/db\n", encoding="utf-8")

    assert dsn_bul(yol) == "postgres://u:s3cr3t@host/db"
