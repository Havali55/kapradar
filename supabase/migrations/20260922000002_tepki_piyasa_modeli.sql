-- Adım 16, Öneri 4: Modül C piyasa modeline geçiyor.
--
-- Eski formül Σ (hisse − xu100) her hissenin betasını 1 sayıyordu. Bu
-- evrende betalar belirgin biçimde 1'in altında (578 bildirimde dinamik
-- beta ort. 0,77) ve stres günlerinde düşük betalı hisse endeksin tüm
-- düşüşüyle cezalandırılıyordu. Yeni formül:
--
--     car = Σ hisse − (alfa + beta · xu100)
--
-- beta: bildirimin kendi geçmişinden (120 işlem günü, t0−10'da biten,
-- aynı hissenin diğer olay pencereleri dışlanmış) OLS, sonra Vasicek ile
-- evren ortalamasına küçültülmüş. Seçilen model "C" — karşılaştırma
-- `scripts/analiz_piyasa_modeli.py`.
--
-- Saklanan beta/alfa, car_Ng'yi fiyat serisinden birebir yeniden
-- üretmeye yeter: yayınlanan sayının nereden geldiği izlenebilir kalsın.

alter table public.tepki
  add column model       text not null default 'beta1'
                         check (model in ('beta1', 'piyasa')),
  add column beta        numeric,
  add column alfa        numeric,
  add column beta_ham    numeric,
  add column beta_gozlem integer,
  add column beta_r2     numeric,
  add column beta_kaynak text
                         check (beta_kaynak in ('tahmin', 'evren_ort'));

comment on column public.tepki.model is
  'beta1 = Σ (hisse − xu100); piyasa = Σ hisse − (alfa + beta · xu100).';
comment on column public.tepki.beta is
  'CAR''da kullanılan beta. beta_kaynak=tahmin ise Vasicek-küçültülmüş '
  'tahmin; evren_ort ise geçmiş yetmediği için evren ortalaması.';
comment on column public.tepki.beta_ham is
  'Küçültme öncesi OLS betası. evren_ort satırlarında NULL.';
comment on column public.tepki.beta_kaynak is
  'evren_ort: tahmin penceresinde 60 gözlem yok (yeni halka arz). '
  'Beta evren ortalaması, alfa 0 — sitede işaretleniyor.';
comment on column public.tepki.car_3g is
  'Birikimli anormal getiri, üç işlem günü; formül `model` sütununda. '
  'Eksik tek kapanış bile NULL bırakır — yanlış sayı yayınlanmaz.';

-- akis: yeni sütunlar sona ekleniyor (create or replace view sıra değiştiremez).
create or replace view public.akis as
with son_cikarim as (
  select distinct on (kap_id)
         kap_id, etki_skoru, ciro_orani, net_tutar_tl, veri, yayina_hazir
  from public.cikarim
  order by kap_id, id desc
),
siklik as (
  select ticker, count(*)::int as adet
  from public.bildirim
  group by ticker
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
  f.adet                                             as bildirim_sikligi,
  t.model                                            as tepki_modeli,
  t.beta,
  t.beta_kaynak
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
join siklik f on f.ticker = b.ticker
where c.yayina_hazir;

comment on view public.akis is
  'Sitenin tek genel yüzeyi. Yalnızca kapıdan geçmiş (yayina_hazir) '
  'bildirimler; ham KAP metni ve elle inceleme alanları dışarıda.';

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;
