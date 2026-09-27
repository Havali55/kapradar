-- X (Twitter) paylaşım kaydı (2026-09-25).
--
-- Her bildirim en fazla bir kez paylaşılır: kap_id birincil anahtar.
-- Satır tweet GÖNDERİLMEDEN ÖNCE yazılıp commit ediliyor ("gonderiliyor"),
-- sonra sonuca göre güncelleniyor. Böylece gönderim ile kayıt arasında
-- süreç düşerse satır "gonderiliyor"da kalır ve bir sonraki koşu o
-- bildirimi yeniden denemez — iki kez paylaşmaktansa hiç paylaşmamayı
-- seçiyoruz (en fazla bir kez). "hata" satırları da kendiliğinden
-- yeniden denenmez; satırı silmek bildirimi kuyruğa geri koyar.
--
-- Hangi bildirimlerin aday olduğu (başlangıç tarihi, yaş sınırı) kodda:
-- src/kap_radar/x_paylasim.py.

create table if not exists public.x_paylasim (
  kap_id       text primary key references public.bildirim (kap_id),
  metin        text not null,
  durum        text not null check (durum in ('gonderiliyor', 'gonderildi', 'hata')),
  tweet_id     text,
  hata         text,
  olusturma    timestamptz not null default now(),
  guncelleme   timestamptz not null default now()
);

-- Diğer tablolar gibi: RLS açık, politika yok → yalnız service_role.
alter table public.x_paylasim enable row level security;
