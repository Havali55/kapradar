-- Elle kararlar (2026-09-26).
--
-- Veri denetiminde 962 skorlu bildirimin 10'unda tutar metinde birebir
-- geçiyordu ama şirketin geliri değildi (alım, yatırım, tahmini ihale
-- bedeli, artışla birlikte sayılan yeni toplam). Kapıya anlam kontrolleri
-- eklendi (B4–B6); onların elle kuyruğa attığı bildirimlerin kararı
-- `data/elle_duzeltmeler.json`'da, gerekçesiyle, repoda duruyor.
--
-- `scripts/elle_duzelt.py` her kararı `cikarim` tablosuna model='elle',
-- katman=3 satırı olarak ekler (tablo append-only: LLM'in satırı
-- silinmez, akis en son satırı okur). Bu tablo yalnız kararın kendisini
-- ve gerekçesini tutar; site gerekçeyi kullanıcıya gösterir — bir
-- büyüklüğün neden değiştiği görünür olmalı.

create table if not exists public.elle_duzeltme (
  kap_id       text primary key references public.bildirim(kap_id) on delete cascade,
  karar        text not null check (karar in ('onayla', 'skorsuz', 'duzelt')),
  neden        text not null check (length(trim(neden)) > 0),
  cikarim_id   bigint references public.cikarim(id),
  uygulandi_at timestamptz not null default now()
);

alter table public.elle_duzeltme enable row level security;

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
  fb.gunluk_hacim_tl                                 as gunluk_hacim_tl,
  b.karsi_taraf_acik                                 as karsi_taraf_acik,
  e.karar                                            as elle_karar,
  e.neden                                            as elle_not
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
left join public.siklik_durumu sd on sd.kap_id = b.kap_id
left join public.fon_baglam fb on fb.kap_id = b.kap_id
left join public.elle_duzeltme e on e.kap_id = b.kap_id
where c.yayina_hazir;

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;
