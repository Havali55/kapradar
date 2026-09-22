-- Adım 16, Öneri 3: bildirim yorgunluğu bağlam etiketi.
--
-- Adım 16'nın en sağlam bulgusu skorun kendisi değildi: ln(sıklık)
-- katsayısı −0,111, hisse-kümelenmiş t = −2,48 (p = 0,013). Yılda ~30
-- bildirim yapan şirketlerde bildirim başına tepki, seyrek
-- bildirimcilerin yarısından az.
--
-- Bu ölçü SKORA GİRMİYOR. Gerekçe tahta bayrağıyla aynı: bu *şirketin*
-- özelliği, bildirimin değil. Skora gömülseydi "neden 2,4?" sorusunun
-- cevabı "çünkü şirket çok bildirim yapıyor" olurdu. Arayüzde Modül B'nin
-- yanında üçüncü bir bağlam etiketi olarak duruyor.
--
-- Sayım `bildirim` tablosunun TAMAMINDAN geliyor, `akis`ten değil:
-- şirketin ne sıklıkta bildirim yaptığı, bizim kaçını skorlayabildiğimizden
-- bağımsız bir gerçek. 613 bildirimin hepsi sayılıyor, 597'si değil.
--
-- Eşikler (8 ve 18) bildirim ağırlıklı üçlük kesimlerden: 613 bildirimi
-- %33,9 / %33,1 / %33,0 diye bölüyor. Kanonik tanım
-- `src/kap_radar/skor.py::siklik_bayragi`.

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
  -- Payda geri türetiliyor: kartta "TTM hasılat" satırı için gerekli,
  -- ayrı bir join'e değmez.
  case when c.ciro_orani > 0 then round(c.net_tutar_tl / c.ciro_orani)
  end                                                as ttm_hasilat,
  -- hap_ozet + tutarlar(alıntılı). Denetlenebilirlik ürünün özü:
  -- her sayının yanında ham cümlesi duruyor.
  c.veri -> 'hap_ozet'                               as hap_ozet,
  c.veri -> 'tutarlar'                               as tutarlar,
  coalesce((c.veri ->> 'tutar_gizli')::boolean, false) as tutar_gizli,
  t.car_1g,
  t.car_3g,
  t.car_5g,
  td.bayrak                                          as tahta,
  td.v90                                             as tahta_v90,
  td.v5                                              as tahta_v5,
  f.adet                                             as bildirim_sikligi
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
