-- hisse_limit_gunleri: ortalama günlük hareket ve sermaye işlemi günleri
-- (2026-09-27).
--
-- Neden: taban/tavan sayımı yalnız uç günleri görüyor; 144 hissenin 76'sı
-- son 20 seansta hiç limit görmemişti ve dizinde hepsi "yok" diyordu,
-- oysa aralarında günlük ortalama %1,2 ile %4,5 arası fark var. Site artık
-- `ort_hareket`i (son 20 seansın ortalama |getiri|si) listedeki hisselerin
-- ortasına göre kademeliyor.
--
-- Düzeltme: fiyat marjı ±%10; kapanıştan kapanışa %10,5'i aşan hareket
-- normal işlemle oluşamaz (Yahoo'nun düzeltmediği bedelsiz ya da veri
-- hatası: HRKET 09.09 −%93, 15.07 −%93 ve ertesi gün +%1.308). İlk sürüm
-- bu günleri taban sayıyordu. Artık taban −%10,5…−%9,5, tavan +%9,5…+%10,5;
-- dışındaki günler (`gecersiz_gun`) ne limit ne ortalama hareket sayılıyor.
-- Süren seriyi de kırıyorlar: geçersiz gün, seri devam ediyor mu bilinmez.

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
  select ticker, tarih, getiri, sira,
         getiri between -0.105 and -0.095 as taban,
         getiri between 0.095 and 0.105 as tavan,
         abs(getiri) > 0.105 as gecersiz
  from sirali
  where sira <= 20 and getiri is not null
)
select ticker,
       max(tarih) as son_tarih,
       count(*)::int as seans,
       count(*) filter (where taban)::int as taban_gun,
       count(*) filter (where tavan)::int as tavan_gun,
       -- Sondan kesintisiz seri: en yeni seanstan geriye, ilk kıran güne kadar.
       (coalesce(min(sira) filter (where not taban), count(*) + 1) - 1)::int
         as son_taban_serisi,
       (coalesce(min(sira) filter (where not tavan), count(*) + 1) - 1)::int
         as son_tavan_serisi,
       (avg(abs(getiri)) filter (where not gecersiz))::float8 as ort_hareket,
       count(*) filter (where gecersiz)::int as gecersiz_gun
from son
group by ticker;

grant select on public.hisse_limit_gunleri to anon, authenticated;
