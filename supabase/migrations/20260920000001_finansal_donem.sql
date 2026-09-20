-- Adım 7 — dönem bazlı hasılat tablosu.
--
-- Neden `sirket.son_yillik_hasilat_tl` yetmiyor: o sütun tek bir "bugünkü"
-- rakam tutuyor. Skorun paydası ise bildirim anında piyasanın bildiği
-- hasılat olmak zorunda (point-in-time). Bugünün bilançosuyla dünün
-- bildirimini puanlamak lookahead'dir ve geriye dönük testi geçersiz kılar.
--
-- Bir satır = bir finansal rapor. TTM tek rapordan çıkmadığı için
-- (ara dönem raporu yalnız YTD verir) köprünün iki bacağı da burada durur:
-- cari YTD `hasilat`, geçen yılın aynı dönemi `onceki_yil_hasilat`.
-- Yıllık rapor eklenince TTM = yillik + ytd - onceki_ytd.

create table public.finansal_donem (
  kap_index          bigint primary key,          -- raporun KAP indeksi
  ticker             text not null references public.sirket(ticker),
  yayin_zamani       timestamptz not null,        -- point-in-time anahtarı
  donem_basi         date not null,
  donem_sonu         date not null,
  ay_sayisi          smallint not null check (ay_sayisi between 1 and 12),
  hasilat            numeric not null,
  onceki_yil_hasilat numeric,
  onceki_donem_sonu  date,
  para_birimi        text,                        -- 'TL' değilse çevrilmeden kullanılamaz
  konsolide          boolean,
  birim_carpani      numeric not null default 1,  -- '1.000 TL' → 1000
  yuklendi_at        timestamptz not null default now()
);

comment on column public.finansal_donem.birim_carpani is
  'Sunum biriminden gelen çarpan. hasilat ZATEN çarpılmış mutlak tutar; '
  'bu sütun hangi ölçeğin uygulandığını izlenebilir tutuyor.';

comment on table public.finansal_donem is
  'Bir satır = bir KAP finansal raporu. TTM hesabı kap_radar.finansal.ttm_coz '
  'içinde; yayin_zamani''ndan sonraki raporlar o bildirim için görünmez.';
comment on column public.finansal_donem.yayin_zamani is
  'Point-in-time kapısı: bildirim anında yayınlanmamış rapor paydaya giremez.';
comment on column public.finansal_donem.onceki_yil_hasilat is
  'Aynı raporun karşılaştırma sütunu. TTM köprüsünün çıkarılan bacağı.';
comment on column public.finansal_donem.para_birimi is
  'Raporun sunum para birimi. USD raporlayan şirkette TL sanılırsa ~40 kat hata.';

-- Sorgu deseni: bir ticker'ın tüm dönemleri, en güncel dönem önce.
create index finansal_donem_ticker_idx
  on public.finansal_donem (ticker, donem_sonu desc, yayin_zamani desc);

alter table public.finansal_donem enable row level security;

-- `sirket` üzerindeki tek satırlık önbellek sütunları duruyor; site
-- "son yıllık hasılat"ı oradan okuyacak. Hangi yöntemle bulunduğu
-- izlenebilsin diye kaynak artık rapor linki.
comment on column public.sirket.son_yillik_hasilat_tl is
  'TTM önbelleği — yalnızca TL raporlayan şirketlerde dolu. Point-in-time '
  'hesap için finansal_donem kullanılır, bu sütun değil (spec §8).';
