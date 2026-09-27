-- Site v3 (2026-09-27): point-in-time ciro basamakları ve dönem büyümesi.
--
-- Tasarım: docs/superpowers/specs/2026-09-27-site-v3-tasarim.md §6.
-- İki tablo da türetilmiş; scripts/ciro_seri_yaz.py her koşuda baştan
-- yazar. Kural src/kap_radar/finansal.py'de (ttm_basamaklari,
-- donem_buyumeleri), burada hesap yok.
--
-- Taban tablolarda RLS açık, politika yok: anon onları göremez. Site
-- aşağıdaki iki görünümden okur (akis kalıbı: security_invoker olmadan,
-- sahibinin haklarıyla). Görünümlerin select listesi herkese açık
-- yüzeyin tamamı.

create table if not exists public.ttm_seri (
  ticker            text not null references public.sirket(ticker),
  gecerlilik_basi   timestamptz not null,  -- bu değeri getiren raporun yayını
  hasilat           numeric,               -- null: bu andan sonra TTM çözülemiyor
  donem_sonu        date,
  para_birimi       text,
  yontem            text check (yontem in ('yillik', 'ytd_koprusu')),
  enflasyon_carpani numeric,
  kaynak_kap_index  bigint,
  hesaplandi_at     timestamptz not null default now(),
  primary key (ticker, gecerlilik_basi)
);

comment on table public.ttm_seri is
  'Son 12 aylık cironun değiştiği anlar. Her finansal rapor yayınında '
  'finansal.ttm_coz çağrılır, değer değiştiyse satır yazılır; aylık '
  'örneklemenin bir aya varan gecikmesi yok.';

create table if not exists public.donem_buyume (
  ticker             text not null references public.sirket(ticker),
  donem_sonu         date not null,
  ay_sayisi          smallint not null check (ay_sayisi between 1 and 12),
  kap_index          bigint not null,       -- dönemin son yayını
  yayin_zamani       timestamptz not null,
  hasilat            numeric not null,
  onceki_yil_hasilat numeric,
  para_birimi        text,
  buyume             numeric,               -- hasilat / onceki_yil_hasilat - 1
  katsayi            numeric,               -- TMS 29 yeniden ifade katsayısı
  reel               boolean not null,      -- katsayi >= finansal.REEL_ESIK
  hesaplandi_at      timestamptz not null default now(),
  primary key (ticker, donem_sonu, ay_sayisi)
);

comment on column public.donem_buyume.reel is
  'Rapor TMS 29''a göre yeniden ifade edilmiş mi (finansal.REEL_ESIK = 1,05). '
  'false ise buyume nominaldir; site onu reel büyüme diye göstermez.';

alter table public.ttm_seri enable row level security;
alter table public.donem_buyume enable row level security;

-- kap_index'ler herkese açık KAP bildirim numaraları: sitedeki her ciro
-- ve büyüme sayısı kaynak rapora bağlanabilsin diye açılıyor.
create or replace view public.ciro_seri as
select ticker, gecerlilik_basi, hasilat, donem_sonu, para_birimi, yontem,
       kaynak_kap_index
from public.ttm_seri;

create or replace view public.reel_buyume as
select ticker, donem_sonu, ay_sayisi, kap_index, yayin_zamani, hasilat,
       para_birimi, buyume, katsayi, reel
from public.donem_buyume;

grant select on public.ciro_seri to anon, authenticated;
grant select on public.reel_buyume to anon, authenticated;
