-- Hisse başına son 20 seansın taban ve tavan günleri (2026-09-27).
--
-- Neden: tahta etiketi bildirim gününün ölçümü ve devre kesici günlerini
-- sayıyor. Tabanda kilitli bir hisse işlem görmediği için devre kesiciyi
-- tetiklemiyor: TEHOL 16.09'dan beri yedi seans üst üste -%10 kapatırken
-- dizinde 29.07 bildiriminin "Sakin" etiketiyle görünüyordu. Bu görünüm
-- bugünü, günlük kapanışlardan sayıyor.
--
-- Limit günü: kapanıştan kapanışa değişim -%9,5'in altında (taban) ya da
-- +%9,5'in üstünde (tavan). BIST'te günlük fiyat marjı %10; %9,5 fiyat
-- adımı yuvarlamasına pay bırakıyor. Kapanışlar düzeltilmiş (bölünme ve
-- temettü), bu yüzden bedelsiz günü limit sayılmıyor; temettü günü
-- %9,5'i geçecek bir düşüş nadir.
--
-- Fiyatın kendisi açılmıyor (Yahoo verisi dağıtılmıyor), yalnız sayımlar.
-- Görünüm akis kalıbında: security_invoker yok, sahibinin haklarıyla
-- okuyor; anon yalnız bu sütunları görüyor.

create or replace view public.hisse_limit_gunleri as
with sirali as (
  select ticker,
         tarih,
         kapanis_duzeltilmis / nullif(
           lag(kapanis_duzeltilmis) over (partition by ticker order by tarih), 0
         ) - 1 as getiri,
         row_number() over (partition by ticker order by tarih desc) as sira
  from public.fiyat_gunluk
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
