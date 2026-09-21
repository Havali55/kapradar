-- Tahta kalitesi — bildirim anındaki spekülasyon göstergesi (Modül B).
--
-- Adım 16b'de ölçüldü: skorun piyasa ilgisiyle ilişkisi TEMİZ tahtalarda
-- var (+0,083, t=+1,78), spekülatif tahtalarda YOK (−0,039, t=−0,52).
-- Dolayısıyla bu tablo süs değil, Modül C'nin gösterilip
-- gösterilmeyeceğini belirleyen **geçerlilik koşulu**.
--
-- VBTS/SPK tedbir verisi henüz çekilmedi (Adım 11). Vekil ölçü:
-- limit yakını gün sayısı. BIST günlük limit ±%10 olduğundan
-- |günlük getiri| >= %9 olan gün "limit yakını" sayılıyor. Vekil,
-- limit hareketini yakalar ama SPK tedbirlerinin tamamını değil —
-- VBTS bağlandığında bu tablo yeniden üretilmeli.

create table if not exists public.tahta_durumu (
  kap_id      text primary key references public.bildirim (kap_id) on delete cascade,
  v90         smallint not null,
  v5          smallint not null,
  bayrak      text     not null check (bayrak in ('temiz', 'hareketli', 'tedbirli')),
  yontem      text     not null default 'limit_vekili_v1',
  hesaplandi_at timestamptz not null default now()
);

comment on table public.tahta_durumu is
  'Bildirim anındaki tahta kalitesi. Türetilmiş veri: upsert günceller, '
  'dondurulmaz. Eşikler src/kap_radar/skor.py::tahta_bayragi ile aynı.';
comment on column public.tahta_durumu.v90 is
  'Bildirimden önceki 90 seans gününde |getiri| >= %9 olan gün sayısı.';
comment on column public.tahta_durumu.v5 is
  'Aynı ölçü, yalnız önceki 5 seans günü. Tazelik sinyali.';
comment on column public.tahta_durumu.bayrak is
  'temiz: v90<=2 ve v5=0 · tedbirli: v90>6 veya v5>=2 · aradakiler hareketli. '
  'Sıra tersten kurulu — iki devre kesici gören tahta "hareketli" sayılmaz.';
comment on column public.tahta_durumu.yontem is
  'Hangi ölçüyle üretildiği. VBTS bağlanınca ''vbts_v1'' olacak ve '
  'eski satırlar yeniden hesaplanacak.';

create index tahta_durumu_bayrak_idx on public.tahta_durumu (bayrak);

alter table public.tahta_durumu enable row level security;
