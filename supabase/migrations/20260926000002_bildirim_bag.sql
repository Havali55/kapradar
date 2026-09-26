-- Güncelleme ve düzeltme bağları (2026-09-26).
--
-- Veri denetimi iki çift sayım buldu: kamu ihalelerinde "ihale üzerimizde
-- kaldı" ve aynı tutarla "sözleşme imzalandı" ikisi de skorlanıyordu
-- (PLTUR'un %54'lük İBB işi iki "mega iş"), düzeltme gelince asıl bildirim
-- yayında kalıyordu (KAYSE %19,5 iki kart). Bağ kuralı
-- src/kap_radar/bag.py'de; scripts/bag_kur.py her koşuda tabloyu baştan
-- yazar (türetilmiş veri).
--
-- akis'a eklenen sütunlar: onceki_kap_id, onceki_tur (duzeltme | ayni_is
-- | guncelleme), onceki_yayin. 'ayni_is' bildirim yayında kalır ama site
-- onu yeni iş gibi saymaz; X botu paylaşmaz.

create table if not exists public.bildirim_bag (
  kap_id        text primary key references public.bildirim(kap_id) on delete cascade,
  onceki_kap_id text not null references public.bildirim(kap_id) on delete cascade,
  tur           text not null check (tur in ('duzeltme', 'ayni_is', 'guncelleme')),
  yontem        text not null check (yontem in ('kap_tarih', 'tutar')),
  hesaplandi_at timestamptz not null default now(),
  check (kap_id <> onceki_kap_id)
);

alter table public.bildirim_bag enable row level security;

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
  e.neden                                            as elle_not,
  g.onceki_kap_id                                    as onceki_kap_id,
  g.tur                                              as onceki_tur,
  o.yayin_zamani                                     as onceki_yayin
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
left join public.siklik_durumu sd on sd.kap_id = b.kap_id
left join public.fon_baglam fb on fb.kap_id = b.kap_id
left join public.elle_duzeltme e on e.kap_id = b.kap_id
left join public.bildirim_bag g on g.kap_id = b.kap_id
left join public.bildirim o on o.kap_id = g.onceki_kap_id
where c.yayina_hazir
  -- Yayında bir düzeltmesi olan bildirim yayından çekilir: aynı iş iki
  -- kart olmasın. Düzeltme elle kuyruktaysa asıl bildirim kalır.
  and not exists (
    select 1
    from public.bildirim_bag d
    join son_cikarim dc on dc.kap_id = d.kap_id
    where d.onceki_kap_id = b.kap_id and d.tur = 'duzeltme' and dc.yayina_hazir
  );

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;
