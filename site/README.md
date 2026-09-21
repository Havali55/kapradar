# KAP·RADAR — site

Next.js 15 (App Router) + Supabase. Tasarım Hüseyin'in maketinden
(`Çerçeve tasarımı ve site gereklilikleri.zip`) alındı; inline stiller
`app/globals.css` içinde token'lara taşındı, yeni renk üretilmedi.

## Çalıştırma

```bash
cp .env.local.example .env.local   # değerleri depo kökündeki .env'den al
npm install
npm run dev
```

## İki kural

**1. Skor burada HESAPLANMAZ.** `etki_skoru`, `ciro_orani` ve
`net_tutar_tl` veritabanından okunur. Maketteki JS kendi formülünü
kuruyordu (`1.8·log₁₀(1+40r)`) ve bu onaylanan formül değildi — ASELS
için 4,07 yerine 2,26 veriyordu. Formülün ikinci bir kopyası olmasın
diye site yalnızca gösterir. Detay panelindeki `5 × f(r) × K` satırı
saklanan sayının nasıl çıktığını göstermek için var, onu üretmek için
değil.

**2. Gizli anahtar siteye girmez.** Site yayınlanabilir (anon) anahtarla
bağlanır ve tek bir yüzeyden okur: `public.akis` view'ı. Taban
tablolarda RLS açık ve politika yok, yani anahtar sızsa bile yayına
hazır bildirimlerden fazlası görünmez. `SUPABASE_SERVICE_ROLE_KEY` /
`SUPABASE_SECRET_KEY` buraya **asla** konmaz — o yalnız worker'ındır.

## Veri yüzeyi

`public.akis` (migration `20260921000002_akis_gorunumu.sql`) yalnızca
`yayina_hazir` satırları verir. Dışarıda bıraktıkları bilinçli: ham KAP
metni (telifli), `red_nedeni`/`guven` (elle inceleme kuyruğunun iç
işleyişi), kapıdan geçmeyen bildirimler.

Tahta kalitesi `public.tahta_durumu` tablosundan gelir; `python
scripts/tahta_hesapla.py` ile üretilir. **Vekil ölçü**: VBTS verisi
henüz çekilmediği için "önceki 90 günde |getiri| ≥ %9 olan gün sayısı"
kullanılıyor. VBTS bağlanınca betik yeniden koşulmalı.

## Modül C'nin akran grubu

Aynı skor kademesi **ve** aynı tahta kalitesi; hücre 20'nin altına
düşerse yalnız kademeye gerilir ve bu kullanıcıya söylenir. Tahtanın
gruba girmesi Adım 16b'nin sonucu: limit günü sayısı mutlak tepkiyi
güçlü biçimde artırıyor (t = +4,80) ama yönle ilişkisi sıfır.
Tedbirli tahtalarda panel bir uyarıyla veriliyor.

## Bilinçli olarak yapılmayanlar

- **"CANLI" rozeti yok.** Canlı poller (Adım 15) henüz yazılmadı; rozet
  arşivin hangi tarihe kadar geldiğini söylüyor. Poller gelince
  değişebilir.
- `/hisse/[ticker]` ve `/kap/[id]` sayfaları yok (Adım 11 duruyor).
  Bildirim paylaşımı şimdilik `?b=<kap_id>` derin bağlantısıyla.
