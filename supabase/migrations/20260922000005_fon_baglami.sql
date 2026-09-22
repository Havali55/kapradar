-- Bağlam katmanı F2: fon sahipliği ve tasfiye baskısı.
--
-- Kaynak: fonların KAP'taki Portföy Dağılım Raporları (PDF, SPK şablonu).
-- scripts/fon_arsiv.py indirir, scripts/fon_yukle.py ayrıştırıp yazar;
-- her rapor kendi "Hisse Türk" grup toplamıyla doğrulanır, tutmayan
-- rapor pozisyon YAZMAZ (fon_raporu.durum = 'tutarsiz').
-- Tasarım notu: docs/arastirma/2026-09-22-baglam-katmani.md

create table public.fon_raporu (
  kap_index        bigint primary key,
  fon_kodu         text not null,
  fon_adi          text not null,
  portfoy_sirketi  text,
  donem            text,
  yayin_zamani     timestamptz not null,
  durum            text not null
                   check (durum in ('tutarli', 'tutarsiz', 'muaf', 'hisse_yok')),
  hisse_toplam_tl  numeric
);
comment on table public.fon_raporu is
  'Fon Portföy Dağılım Raporu künyesi. muaf = nitelikli yatırımcı '
  'muafiyetiyle portföy açıklanmamış (görünmeyen ≠ sıfır).';
create index fon_raporu_fon_yayin_idx on public.fon_raporu (fon_kodu, yayin_zamani desc);

create table public.fon_pozisyon (
  kap_index bigint not null references public.fon_raporu (kap_index) on delete cascade,
  ticker    text not null,
  net_tl    numeric not null,
  primary key (kap_index, ticker)
);
comment on column public.fon_pozisyon.net_tl is
  'Fonun o rapordaki net pozisyonu (TL); aynı hissenin farklı alış '
  'satırları ve negatif (ödünç/satış) satırları toplanmış.';
create index fon_pozisyon_ticker_idx on public.fon_pozisyon (ticker);

create table public.tasfiye_kurulus (
  portfoy_sirketi text primary key,
  karar_tarihi    date not null,
  kaynak          text not null
);
comment on table public.tasfiye_kurulus is
  'SPK''nın fonlarını işleme kapatıp tasfiyeye aldığı portföy şirketleri. '
  'Bir sonraki olayda yalnız satır eklenir.';

insert into public.tasfiye_kurulus (portfoy_sirketi, karar_tarihi, kaynak) values
  ('TERA PORTFÖY',       '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  ('PUSULA PORTFÖY',     '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  ('HEDEF PORTFÖY',      '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  ('ATLAS PORTFÖY',      '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  -- Noktalı İ: KAP'taki fon unvanları "A1 CAPİTAL PORTFÖY" diye yazıyor.
  ('A1 CAPİTAL PORTFÖY', '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  ('PARDUS PORTFÖY',     '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon'),
  ('BULLS PORTFÖY',      '2026-09-17', 'SPK kararı, 17.09.2026 — 7 portföy şirketi, 131 fon');

-- Bildirim anındaki fon durumu (point-in-time): her fonun bildirimden
-- ÖNCE yayınlanmış son raporu (en fazla 70 gün eski). Tasfiye alanları
-- yalnız karar tarihinden sonraki bildirimlerde dolu — öncesinde tasfiye yoktu.
create table public.fon_baglam (
  kap_id           text primary key references public.bildirim (kap_id) on delete cascade,
  fon_sayisi       integer not null,
  fon_tl           numeric not null,
  portfoy_sirketi_sayisi integer not null,
  en_buyuk_pay     numeric,
  tasfiye_tl       numeric not null default 0,
  gunluk_hacim_tl  numeric,
  hesaplandi_at    timestamptz not null default now()
);
comment on column public.fon_baglam.en_buyuk_pay is
  'Fon pozisyonunun en büyük portföy şirketinde toplanan payı (0–1).';
comment on column public.fon_baglam.gunluk_hacim_tl is
  'Bildirimden önceki 20 seansın ortalama TL işlem hacmi; "kaç günlük '
  'hacim" oranının paydası.';

-- Hisse sayfası için BUGÜNKÜ durum: her fonun son raporu.
create table public.hisse_fon_guncel (
  ticker           text primary key,
  fon_sayisi       integer not null,
  fon_tl           numeric not null,
  portfoy_sirketi_sayisi integer not null,
  en_buyuk_pay     numeric,
  tasfiye_tl       numeric not null default 0,
  tasfiye_fon_sayisi integer not null default 0,
  gunluk_hacim_tl  numeric,
  fon_tl_3ay_once  numeric,
  son_rapor_donemi text,
  muaf_fon_sayisi  integer not null default 0,
  hesaplandi_at    timestamptz not null default now()
);
comment on column public.hisse_fon_guncel.muaf_fon_sayisi is
  'Bu hissede pozisyonu olan portföy şirketlerinin portföy açıklamayan '
  '(muaf) fon sayısı — görünmeyen kısım.';

alter table public.fon_raporu enable row level security;
alter table public.fon_pozisyon enable row level security;
alter table public.tasfiye_kurulus enable row level security;
alter table public.fon_baglam enable row level security;
alter table public.hisse_fon_guncel enable row level security;

create or replace view public.akis as
with son_cikarim as (
  select distinct on (kap_id)
         kap_id, etki_skoru, ciro_orani, net_tutar_tl, veri, yayina_hazir
  from public.cikarim
  order by kap_id, id desc
)
select
  b.kap_id,
  b.ticker,
  coalesce(s.unvan, b.sirket_unvani)                 as sirket,
  b.ozet                                             as is_tanimi,
  b.yayin_zamani,
  b.kaynak_url,
  b.guncelleme_mi,
  nullif(b.kap_alanlari ->> 'karsi_taraf', '')       as karsi_taraf,
  nullif(b.kap_alanlari ->> 'karsi_taraf_niteligi', '') as karsi_taraf_niteligi,
  nullif(b.kap_alanlari ->> 'baslangic', '')         as baslangic,
  c.etki_skoru,
  c.ciro_orani,
  c.net_tutar_tl,
  case when c.ciro_orani > 0 then round(c.net_tutar_tl / c.ciro_orani)
  end                                                as ttm_hasilat,
  c.veri -> 'hap_ozet'                               as hap_ozet,
  c.veri -> 'tutarlar'                               as tutarlar,
  coalesce((c.veri ->> 'tutar_gizli')::boolean, false) as tutar_gizli,
  t.car_1g,
  t.car_3g,
  t.car_5g,
  td.bayrak                                          as tahta,
  td.v90                                             as tahta_v90,
  td.v5                                              as tahta_v5,
  sd.yeni_is_12a::int                                as bildirim_sikligi,
  t.model                                            as tepki_modeli,
  t.beta,
  t.beta_kaynak,
  td.vbts_kademe                                     as tahta_vbts_kademe,
  td.vbts_bitis                                      as tahta_vbts_bitis,
  td.yontem                                          as tahta_yontem,
  sd.kap_oda_12a::int                                as kap_aciklama_12a,
  sd.arsiv_gun::int                                  as siklik_arsiv_gun,
  fb.fon_sayisi                                      as fon_sayisi,
  fb.fon_tl                                          as fon_tl,
  fb.tasfiye_tl                                      as fon_tasfiye_tl,
  fb.gunluk_hacim_tl                                 as gunluk_hacim_tl
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
left join public.siklik_durumu sd on sd.kap_id = b.kap_id
left join public.fon_baglam fb on fb.kap_id = b.kap_id
where c.yayina_hazir;

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;

-- Site yalnız özetleri okur; ham pozisyonlar service_role'de kalır.
create policy hisse_fon_guncel_okuma on public.hisse_fon_guncel
  for select to anon, authenticated using (true);
grant select on public.hisse_fon_guncel to anon, authenticated;
