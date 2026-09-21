-- Sitenin okuyacağı TEK genel yüzey.
--
-- `.env.example` kuralı: gizli anahtar siteye asla konmaz. Dolayısıyla
-- site `service_role` ile değil, yayınlanabilir anahtarla bağlanır ve
-- yalnızca buradan okur. Taban tablolarda RLS açık ve politika yok —
-- yani bu view olmadan anon hiçbir şey göremez.
--
-- View `security_invoker` OLMADAN oluşturuluyor (varsayılan): sahibinin
-- haklarıyla çalışır, taban tablolardaki RLS'i atlar. Genel yüzeyin
-- tamamı bu yüzden tek bir yerde ve gözle denetlenebilir durumda:
-- aşağıdaki select listesinde ne varsa herkese açıktır, fazlası değil.
--
-- Dışarıda bıraktıklarımız bilinçli:
--   - ham_govde_html / ham_metin_*  : KAP'ın telifli tam metni
--   - cikarim.red_nedeni / guven    : elle inceleme kuyruğunun iç işleyişi
--   - yayina_hazir=false satırlar   : kapıdan geçmeyen hiçbir şey çıkmaz
--   - finansal_donem                : ham rapor arşivi, sitenin işi değil

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
  td.v5                                              as tahta_v5
from public.bildirim b
join son_cikarim c on c.kap_id = b.kap_id
left join public.sirket s on s.ticker = b.ticker
left join public.tepki t on t.kap_id = b.kap_id
left join public.tahta_durumu td on td.kap_id = b.kap_id
where c.yayina_hazir;

comment on view public.akis is
  'Sitenin tek genel yüzeyi. Yalnızca kapıdan geçmiş (yayina_hazir) '
  'bildirimler; ham KAP metni ve elle inceleme alanları dışarıda.';

revoke all on public.akis from public;
grant select on public.akis to anon, authenticated;
