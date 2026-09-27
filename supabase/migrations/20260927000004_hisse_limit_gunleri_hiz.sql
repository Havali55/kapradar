-- hisse_limit_gunleri'ni son 60 güne sınırla (2026-09-27).
--
-- Neden: ilk sürüm bütün fiyat tablosunu (89 bin satır) iki kez sıralıyordu,
-- tek başına 567 ms. Site derlemesinde eşzamanlı sorguların arasında anon'un
-- 3 sn'lik statement_timeout'una takıldı ve /hisse ön üretimi düştü.
--
-- 60 takvim günü ~40 seans; 20 getiri için gereken 21 kapanışı bayram
-- tatillerinde de fazlasıyla karşılıyor. Uzun süre işlem görmeyen hissede
-- `seans` 20'nin altında kalır ve site sayımı o seans sayısıyla yazar.
-- Tarih indeksiyle 35 ms; 144 hissede sonuç ilk sürümle birebir aynı.

create index if not exists fiyat_gunluk_tarih_idx on public.fiyat_gunluk (tarih);

create or replace view public.hisse_limit_gunleri as
with sinir as (
  select max(tarih) - 60 as bas from public.fiyat_gunluk
),
sirali as (
  select f.ticker,
         f.tarih,
         f.kapanis_duzeltilmis / nullif(
           lag(f.kapanis_duzeltilmis) over (partition by f.ticker order by f.tarih), 0
         ) - 1 as getiri,
         row_number() over (partition by f.ticker order by f.tarih desc) as sira
  from public.fiyat_gunluk f, sinir
  where f.tarih >= sinir.bas
),
son as (
  select ticker, tarih, getiri, sira
  from sirali
  where sira <= 20 and getiri is not null
)
select ticker,
       max(tarih) as son_tarih,
       count(*)::int as seans,
       count(*) filter (where getiri <= -0.095)::int as taban_gun,
       count(*) filter (where getiri >= 0.095)::int as tavan_gun,
       -- Sondan kesintisiz seri: en yeni seanstan geriye, ilk kıran güne kadar.
       (coalesce(min(sira) filter (where getiri > -0.095), count(*) + 1) - 1)::int
         as son_taban_serisi,
       (coalesce(min(sira) filter (where getiri < 0.095), count(*) + 1) - 1)::int
         as son_tavan_serisi
from son
group by ticker;

grant select on public.hisse_limit_gunleri to anon, authenticated;
