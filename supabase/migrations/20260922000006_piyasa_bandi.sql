-- Piyasa bandı: sitenin üstündeki tek satır (bağlam katmanı F4).
--
-- Son 5 seansta eşit ağırlıklı BIST ve XU100 birikimli getirisi + en son
-- SPK tasfiye kararı. Kaynaklı, tarihli, yorumsuz. Görünüm sahibinin
-- yetkisiyle çalışıyor (akis gibi): ham tablolar anon'a açılmıyor.

create or replace view public.piyasa_bandi as
with takvim as (
  select tarih, xu100_kapanis,
         row_number() over (order by tarih desc) as sira
  from public.endeks_gunluk
),
son as (select max(tarih) as tarih from takvim),
bas as (select tarih, xu100_kapanis from takvim where sira = 6)
select
  (select tarih from son)                                        as son_tarih,
  (select exp(sum(ln(1 + ew_getiri))) - 1 from public.faktor_gunluk f
    where f.tarih > (select tarih from bas) and f.tarih <= (select tarih from son))
                                                                 as ew_5s,
  (select t.xu100_kapanis / b.xu100_kapanis - 1
     from takvim t, bas b where t.sira = 1)                      as xu100_5s,
  (select max(karar_tarihi) from public.tasfiye_kurulus)         as tasfiye_tarihi,
  (select count(*)::int from public.tasfiye_kurulus
    where karar_tarihi = (select max(karar_tarihi) from public.tasfiye_kurulus))
                                                                 as tasfiye_sirket_sayisi;

revoke all on public.piyasa_bandi from public;
grant select on public.piyasa_bandi to anon, authenticated;
