-- Modül B gerçek veriye geçiyor; bildirim sıklığı point-in-time oluyor.
--
-- 2026-09-22 keşfi: liste arşivi (data/ham/liste, 2024-09'dan beri tüm
-- bildirim türleri) Borsa İstanbul'un kendi kayıtlarını taşıyor.
--   * Pay Bazında Devre Kesici: onaylı eşikler (v90<=2 temiz, v90>6
--     tedbirli) zaten bu sayı için kurulmuştu. v90/v5 artık limit yakını
--     gün vekili değil, devre kesicinin başladığı ayrı seans günü sayısı.
--   * VBTS: tedbirin kademesi ve süresi. Bildirim anında yürürlükte bir
--     VBTS tedbiri varsa tahta "tedbirli" — adın kelime anlamı.
--
-- Vekil gerçek veriyle kötü örtüşüyordu: vekilin "tedbirli" dediği 87
-- bildirimin 50'sinde 90 günde VBTS yok; "temiz"lerin 12'si VBTS altında.

alter table public.tahta_durumu
  add column vbts_kademe smallint not null default 0
                         check (vbts_kademe between 0 and 4),
  add column vbts_bitis  date;

comment on column public.tahta_durumu.v90 is
  'yontem=kap_v1: bildirimden önceki 90 seansta pay bazında devre '
  'kesicinin başladığı ayrı gün sayısı (bildirim anından sonrası sayılmaz). '
  'yontem=limit_vekili_v1: |getiri| >= %9 olan gün sayısı.';
comment on column public.tahta_durumu.v5 is
  'Aynı ölçü, yalnız önceki 5 seans. Tazelik sinyali.';
comment on column public.tahta_durumu.vbts_kademe is
  'Bildirim anında yürürlükteki en ağır VBTS kademesi: 0 yok, 1 kredili '
  'işlem/açığa satış yasağı, 2 brüt takas, 3 emir paketi, 4 tek fiyat.';
comment on column public.tahta_durumu.bayrak is
  'tedbirli: yürürlükte VBTS veya v90/v5 üst eşikte · temiz: alt eşikte · '
  'aradakiler hareketli. Eşikler ve kanonik tanım skor.tahta_bayragi.';

-- Bildirim sıklığı: bildirim anından ÖNCEKİ 12 ay. Eski ölçü
-- (akis.bildirim_sikligi = arşivin tamamı) ileriye bakıyordu ve 613
-- bildirimin 121'inde kademeyi değiştiriyordu.
create table public.siklik_durumu (
  kap_id        text primary key references public.bildirim (kap_id) on delete cascade,
  yeni_is_12a   smallint not null,
  kap_oda_12a   smallint not null,
  arsiv_gun     smallint not null,
  hesaplandi_at timestamptz not null default now()
);

comment on table public.siklik_durumu is
  'Point-in-time şirket sıklığı. Kaynak: KAP liste arşivi (2024-09-01 '
  've sonrası), yani 2025-09 sonrası her bildirimin 12 ayı tam kapsanıyor.';
comment on column public.siklik_durumu.yeni_is_12a is
  'Bildirimden önceki 365 günde aynı şirketin Yeni İş İlişkisi sayısı, '
  'bu bildirim DAHİL.';
comment on column public.siklik_durumu.kap_oda_12a is
  'Aynı pencerede şirketin tüm özel durum açıklamaları (disclosureClass=ODA). '
  'Yeni İş İlişkisi seyrek ama genel olarak çok konuşan şirketi ayırt eder.';
comment on column public.siklik_durumu.arsiv_gun is
  'Şirketin arşivde ilk görüldüğü günden bildirime kadar geçen gün, 365 ile '
  'sınırlı. 365''ten azsa 12 aylık sayım eksik pencereden (yeni halka arz).';

alter table public.siklik_durumu enable row level security;

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
  sd.arsiv_gun::int                                  as siklik_arsiv_gun
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
left join public.siklik_durumu sd on sd.kap_id = b.kap_id
where c.yayina_hazir;

comment on view public.akis is
  'Sitenin tek genel yüzeyi. Yalnızca kapıdan geçmiş (yayina_hazir) '
  'bildirimler; ham KAP metni ve elle inceleme alanları dışarıda.';

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;
