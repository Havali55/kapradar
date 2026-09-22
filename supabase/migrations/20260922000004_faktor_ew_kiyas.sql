-- Modül C kıyas endeksi: XU100 → eşit ağırlıklı BIST (2026-09-22, Hüseyin onayı).
--
-- analiz_faktor.py: bildirim evrenimizin hisseleri XU100'ü değil eşit
-- ağırlıklı BIST'i izliyor. İki faktörlü modelde küçük hisse faktörüne
-- duyarlılık ort. +0,98 (%98 pozitif); XU100'ün net ağırlığı ~0,09 kalıyor.
-- EW'ye karşı beta ort. 1,07, medyan R² 0,163 → 0,216. 8–18 Eylül fon
-- krizinde XU100 −%7,8, EW −%15,5: XU100'e karşı ölçülen "tepki" küçük
-- hisse şokunu bildirime yazıyordu.
--
-- Seri scripts/faktor_kur.py'den: KAP arşivindeki ~630 pay kodunun
-- yfinance kapanışlarının kesitsel ortalama günlük getirisi.

create table public.faktor_gunluk (
  tarih     date primary key,
  ew_getiri numeric not null,
  n_hisse   integer not null
);

comment on table public.faktor_gunluk is
  'Eşit ağırlıklı BIST günlük getirisi. yfinance''te küçük hisse endeksi '
  '(XTUMY/XUTUM) yok; kesitsel ortalama, |getiri| >= %50 gün atılmış.';

alter table public.faktor_gunluk enable row level security;

alter table public.tepki drop constraint tepki_model_check;
alter table public.tepki add constraint tepki_model_check
  check (model in ('beta1', 'piyasa', 'ew'));

comment on column public.tepki.model is
  'beta1 = Σ (hisse − xu100); piyasa = Σ hisse − (alfa + beta · xu100); '
  'ew = Σ hisse − (alfa + beta · eşit ağırlıklı BIST).';
