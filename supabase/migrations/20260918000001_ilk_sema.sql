-- KAP Radar — ilk şema
-- Spec: docs/superpowers/specs/2026-09-17-kap-radar-design.md §5
--
-- Güvenlik duruşu: public şemadaki her tabloda RLS açık, POLİTİKA YOK.
-- Bu, yalnızca service_role'ün (worker) erişebilmesi demek. Site yazıldığında
-- yalnızca yayına hazır satırlar için okuma politikası eklenecek. Kapıdan
-- geçmemiş çıkarımların dışarıdan okunabilmesi kabul edilemez (spec §6).

-- ---------------------------------------------------------------- sirket
create table public.sirket (
  ticker                text primary key,
  unvan                 text not null,
  mkk_uye_oid           text unique,          -- KAP'ın mkkMemberOid'i
  sektor                text,
  son_yillik_hasilat_tl numeric,              -- son 4 çeyrek toplamı
  hasilat_donemi        text,                 -- "2025/12"
  hasilat_kaynak        text,                 -- KAP finansal rapor linki
  guncellendi_at        timestamptz not null default now()
);

comment on column public.sirket.son_yillik_hasilat_tl is
  'Boşsa ciro oranı gösterilmez — tahmin edilmez (spec §8).';

-- -------------------------------------------------------------- bildirim
-- KAP iki ayrı kimlik veriyor: disclosureId (kararlı hex) ve disclosureIndex
-- (URL'de görünen tamsayı). Upsert anahtarı kararlı olan olmalı.
create table public.bildirim (
  kap_id                    text primary key,           -- disclosureId
  kap_index                 bigint not null unique,     -- disclosureIndex
  ticker                    text references public.sirket(ticker),
  sirket_unvani             text not null,
  mkk_uye_oid               text,
  sablon_kodu               text not null,              -- 'oda-12000'
  sablon_adi                text not null,              -- 'Yeni İş İlişkisi'
  yayin_zamani              timestamptz not null,
  ozet                      text,
  ham_govde_html            text not null,              -- disclosureBody[0]
  ham_metin_tr              text,                       -- dil ayrımı sonrası
  ham_metin_en              text,
  kaynak_url                text not null,
  ek_sayisi                 integer not null default 0,
  guncelleme_mi             boolean not null default false,
  duzeltme_mi               boolean not null default false,
  onceki_aciklama_tarihleri date[] not null default '{}',
  ilgili_kap_id             text,                       -- relatedDisclosureOid
  kap_alanlari              jsonb not null default '{}'::jsonb,
  cekildi_at                timestamptz not null default now()
);

comment on column public.bildirim.ham_metin_tr is
  'oda_ExplanationTextBlock TR ve EN metni aynı blokta taşır; LLM''e yalnızca '
  'TR verilir, yoksa her rakam iki kez görünür ve alıntı kapısı yanlış eşleşir.';
comment on column public.bildirim.kap_alanlari is
  'Ayrıştırılmış oda_* XBRL alanları. LLM''e uğramaz — KAP''ın yapılandırılmış '
  'verisi (karşı taraf, niteliği, başlangıç tarihi, sözleşme koşulları).';

create index bildirim_sablon_zaman_idx on public.bildirim (sablon_kodu, yayin_zamani desc);
create index bildirim_ticker_zaman_idx on public.bildirim (ticker, yayin_zamani desc);
create index bildirim_zaman_idx        on public.bildirim (yayin_zamani desc);

-- --------------------------------------------------------------- cikarim
-- APPEND-ONLY, versiyonlu. Prompt/şema değişince yeni satır yazılır, eski
-- silinmez. Yayında olan = o kap_id için yayina_hazir=true olan en son satır.
create table public.cikarim (
  id              bigserial primary key,
  kap_id          text not null references public.bildirim(kap_id) on delete cascade,
  model           text not null,
  katman          smallint not null check (katman between 1 and 3),
  prompt_versiyon text not null,
  sema_versiyon   text not null,
  veri            jsonb not null,             -- tutarlar[], tutar_gizli, hap_ozet
  guven           text not null check (guven in ('yuksek', 'orta', 'dusuk')),
  yayina_hazir    boolean not null,
  red_nedeni      text,
  -- §8 deterministik hesapları: yayın anındaki değerlerin anlık görüntüsü.
  -- Hasılat sonradan güncellense bile sayfa neyi neden gösterdiği izlenebilir kalır.
  net_tutar_tl    numeric,
  ciro_orani      numeric,
  etki_skoru      numeric check (etki_skoru between 0 and 5),
  olusturuldu_at  timestamptz not null default now()
);

comment on column public.cikarim.veri is
  'tutarlar: [{deger, para_birimi, tip, alinti}]. tip ∈ ilave_siparis | '
  'fiyat_farki | toplam_sozlesme | tek_seferlik. net_tutar_tl hesabına '
  'toplam_sozlesme GİRMEZ (spec §8).';

create index cikarim_kap_zaman_idx on public.cikarim (kap_id, olusturuldu_at desc);
create index cikarim_yayin_idx     on public.cikarim (kap_id, olusturuldu_at desc)
  where yayina_hazir;

-- ----------------------------------------------------------- fiyat/endeks
create table public.fiyat_gunluk (
  ticker              text not null references public.sirket(ticker),
  tarih               date not null,
  kapanis_duzeltilmis numeric not null,       -- yfinance auth_adjust=True
  hacim               bigint,
  primary key (ticker, tarih)
);

create table public.endeks_gunluk (
  tarih         date primary key,
  xu100_kapanis numeric not null
);

create table public.kur_gunluk (
  tarih         date not null,
  para_birimi   text not null,
  tl_karsiligi  numeric not null,
  primary key (tarih, para_birimi)
);

comment on table public.kur_gunluk is
  'TCMB bildirim tarihli resmî kur. Tatil/hafta sonu ise önceki iş günü (spec §8).';

-- ------------------------------------------------------------- altin_kume
-- Elle doğrulanmış gerçek. Çıkarım buraya ASLA yazmaz.
create table public.altin_kume (
  kap_id           text primary key references public.bildirim(kap_id) on delete cascade,
  elle_dogrulanmis jsonb not null,
  etiketleyen      text,
  etiketlendi_at   timestamptz not null default now()
);

-- ----------------------------------------------------------- cekim_durumu
-- Backfill'in kaldığı yerden devam edebilmesi için kontrol noktası (spec §9).
create table public.cekim_durumu (
  anahtar            text primary key,        -- 'backfill' | 'poller'
  son_islenen_tarih  date,
  son_islenen_index  bigint,
  notlar             jsonb not null default '{}'::jsonb,
  guncellendi_at     timestamptz not null default now()
);

-- ------------------------------------------------------------------- RLS
-- Her tabloda açık, politika yok: yalnızca service_role erişir.
-- Site yazıldığında yalnızca yayınlanmış satırlar için okuma politikası eklenecek.
alter table public.sirket        enable row level security;
alter table public.bildirim      enable row level security;
alter table public.cikarim       enable row level security;
alter table public.fiyat_gunluk  enable row level security;
alter table public.endeks_gunluk enable row level security;
alter table public.kur_gunluk    enable row level security;
alter table public.altin_kume    enable row level security;
alter table public.cekim_durumu  enable row level security;
