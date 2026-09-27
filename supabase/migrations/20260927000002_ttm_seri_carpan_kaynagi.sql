-- 2026-09-27: köprü çarpanının kaynağı.
--
-- finansal.ttm_coz yıllık terimi cari birime taşırken artık iki kaynaktan
-- birini kullanıyor: şirketin kendi TMS 29 katsayısı ya da, katsayı yoksa
-- veya TMS 29 geçişiyle kirliyse (2024 ara dönemleri), resmî TÜFE oranı
-- (kap_radar/tufe_aylik.csv). Hangisinin kullanıldığı her basamakta
-- izlenebilsin. Gerekçe: docs/arastirma/2026-09-27-gecerlilik-degerlendirmesi.md §6.

alter table public.ttm_seri
  add column if not exists carpan_kaynagi text
  check (carpan_kaynagi in ('sirket', 'tufe'));

comment on column public.ttm_seri.carpan_kaynagi is
  'sirket: şirketin kendi yeniden ifade katsayısı; tufe: resmî TÜFE oranı; '
  'null: çarpan uygulanmadı (yıllık yöntem ya da TMS 29 uygulamayan şirket).';
