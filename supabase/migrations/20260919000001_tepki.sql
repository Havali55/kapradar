-- Bildirim sonrası piyasa tepkisi (spec §8).
--
-- Neden ayrı tablo: CAR her koşuda fiyat serisinden yeniden türetilebilir
-- ama site bunu sorgu anında hesaplayamaz (111 hisse + endeks serisi
-- üzerinde pencere kaydırmak ISR sayfasına ağır gelir). Ayrıca hangi
-- pencere tanımıyla hesaplandığı saklanmalı: tanım değişirse sayfadaki
-- sayının neden değiştiği izlenebilir kalsın.
create table public.tepki (
  kap_id        text primary key references public.bildirim(kap_id) on delete cascade,
  t0            date not null,
  car_1g        numeric,
  car_3g        numeric,
  car_5g        numeric,
  pencere_basi  smallint not null default 0,
  hesaplandi_at timestamptz not null default now()
);

comment on column public.tepki.t0 is
  'Piyasanın bildirime ilk tepki verebileceği işlem günü. Bildirim seans '
  'kapandıktan sonra düştüyse bir sonraki işlem günü (spec §8).';
comment on column public.tepki.pencere_basi is
  'car_Ng penceresinin t0''a göre başlangıcı. 0 = t0 dahil. Spec §8''in '
  'yazılı formülü t0+1 idi; t0 zaten "ilk tepki günü" olarak tanımlı '
  'olduğu için asıl tepki günü pencerenin dışında kalıyordu.';
comment on column public.tepki.car_3g is
  'Birikimli anormal getiri: Σ (hisse_getirisi − xu100_getirisi), üç işlem '
  'günü. Eksik tek kapanış bile NULL bırakır — yanlış sayı yayınlanmaz.';

create index tepki_t0_idx on public.tepki (t0 desc);

alter table public.tepki enable row level security;
