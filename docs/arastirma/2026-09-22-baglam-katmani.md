# Bağlam katmanı — fon sahipliği ve bilgilendirme filtreleri

*Taslak, 2026-09-22. Karar bekleyen maddeler en sonda.*

## Neden

Eylül 2026 fon krizi şunu gösterdi: bir bildirimin nasıl karşılanacağını
çoğu zaman bildirimin kendisi değil, **hissenin o anki durumu** belirliyor.
8–18 Eylül'de eşit ağırlıklı BIST −%15,5 düşerken tahtası "temiz" olan
hisseler bile −%17,8 düştü. Tasfiyedeki fonların elinde 372 milyar TL
hisse var; OZATD'deki pozisyon 19,7 günlük işlem hacmine denk.

Modül B bugün iki şey söylüyor: tahta kalitesi ve bildirim sıklığı. Kullanıcının
bir bildirimi okurken sorduğu soruların yalnız bir kısmı bunlar.

## Kullanıcı ne soruyor?

Bir bildirim ya da hisse sayfasına bakan kişinin aklındaki sorular ve
bunları cevaplayan KAP verisi:

| Soru | Sinyal | Kaynak (KAP arşivinde) | Durum |
|---|---|---|---|
| Tahtada olağandışı bir şey var mı? | VBTS, devre kesici | BIST duyuruları | ✅ yayında |
| Bu şirket her gün böyle haber mi veriyor? | bildirim sıklığı | Yeni İş İlişkisi + ÖDA | ✅ yayında |
| **Bu hissede kim var?** | fon sahipliği: fon sayısı, TL, trend | Portföy Dağılım Raporu (1.314 fon) | 🔶 7 şirkette kanıtlandı |
| **Üstünde satış baskısı var mı?** | tasfiyedeki fonların pozisyonu / günlük hacim | aynı + SPK tasfiye listesi | 🔶 hesaplandı, yayında değil |
| İçeridekiler ne yapıyor? | pay alım/satım bildirimi | 4.384 bildirim | ⬜ |
| Şirket kendi hissesini alıyor mu? | geri alım programı | 4.431 bildirim | ⬜ |
| Sulandırma yaklaşıyor mu? | sermaye artırımı / bedelli | 2.733 bildirim | ⬜ |
| Resmî bir uyarı var mı? | SPK tedbir kararı, işlem sırası kapatma, dava | 52 + 69 + 184 | ⬜ |
| Piyasanın geneli ne durumda? | eşit ağırlıklı BIST vs XU100, rejim | 630 hisselik seri | 🔶 seri hazır |

Soruların hiçbiri "al/sat" sorusu değil. Hepsi "neye bakıyorum?" sorusu.
Katman bu yüzden yorum değil **bağlam** üretir.

## Tasarım ilkeleri

1. **İki zaman, açıkça etiketli.** Bildirim sayfası "bildirim anında"
   durumu gösterir (point-in-time — araştırmanın doğruluğu buna bağlı).
   Hisse sayfası "bugün" durumu gösterir (kullanıcının kararı buna bağlı).
   İkisi aynı kutuda karışmaz.
2. **Her satır bir olgu + kaynak linki.** "Tasfiyedeki fonların pozisyonu:
   59,4 milyar TL · 19,7 günlük hacim · kaynak: 4 fonun Ağustos raporu".
   Sıfat yok, "manipülasyon" yok, "riskli" yok.
3. **Renk yalnız nesnel durumlara.** VBTS altında → kırmızı; bu bir
   Borsa İstanbul kararı. Fon pozisyonu büyük → renk yok, sayı var.
4. **Bilinmeyeni söyle.** Nitelikli yatırımcı muafiyetiyle portföy açıklamayan
   fonlar var (tasfiyedeki 7 şirkette 62 fon; piyasanın geri kalanında 316'da 4).
   Hisse sayfası "ayrıca portföyünü açıklamayan X fon bu şirketin yönetiminde"
   der; görünmeyeni sıfır saymaz.
5. **Gecikmeyi söyle.** Portföy raporları çoğunlukla aylık, bir ay geriden
   gelir. Her fon satırında rapor dönemi yazar.

## Fon katmanı — ne gösterilecek

Hisse başına, her rapor dönemi için:

- **Fon ilgisi**: kaç fon tutuyor, toplam TL, kaç günlük hacim
- **Yön**: son 3 dönemde fon pozisyonu arttı mı azaldı mı (birikim / boşaltım)
- **Yoğunlaşma**: pozisyonun ne kadarı tek bir portföy şirketinde
- **Tasfiye baskısı**: pozisyonun ne kadarı SPK'nın işleme kapattığı fonlarda;
  kaç günlük hacim. Tasfiye listesi ayrı bir tabloda, tarihli — bir sonraki
  krizde yalnız satır eklenir.

Bilgilendirme filtreleri (akış ve hisse listesi):

- `Tasfiye baskısı altında` — tasfiyedeki fonların pozisyonu ≥ 1 günlük hacim
- `Fonlar biriktiriyor` / `Fonlar çıkıyor` — 3 dönemlik yön
- `VBTS altında` — yürürlükte tedbir
- `İçeriden işlem (30 gün)`, `Geri alım programı`, `Sermaye artırımı yolda`
- `Resmî uyarı` — SPK tedbir kararı / işlem sırası kapatma

Piyasa bandı (sitenin üstünde, tek satır): "Eşit ağırlıklı BIST son 5 seans
−%x · XU100 −%y · SPK 17.09.2026'da 7 portföy şirketinin 131 fonunu tasfiyeye
aldı." Kaynaklı, tarihli, yorumsuz.

## Araştırmaya katkısı (yalnız ürün değil)

Tüm piyasanın 12 aylık fon haritası çıkınca test edilebilecek sorular:

1. **Tasfiye baskısı fiyata ne yapıyor?** Tasfiyedeki pozisyonu yüksek
   hisseler krizden sonra eşit ağırlıklı BIST'e göre nasıl gidiyor — bu,
   önümüzdeki 6 ay canlı izlenebilecek doğal bir deney.
2. **Sakin yükseliş parmak izi.** Soruşturma dönemlerinde devre kesici
   AZALMIŞTI. Fonların biriktirdiği + oynaklığı düşen + sürekli yükselen
   hisseler bir desen oluşturuyor mu? (Etiketli örnek az; iddia değil,
   betimleme olarak raporlanır.)
3. **Bildirim + fon ilgisi.** Fonların tuttuğu hissede yeni iş bildirimi
   farklı mı karşılanıyor? (Adım 16b'nin kurumsal versiyonu.)

## Uygulama sırası

| Faz | İş | Maliyet |
|---|---|---|
| F1 | 12 aylık tüm Portföy Dağılım Raporları → `fon_pozisyon` tablosu (fon, portföy şirketi, dönem, hisse, TL) | bedava, ~2 saat çekim |
| F2 | `tasfiye_kurulus` tablosu + hisse×dönem özet görünümü (point-in-time) | bedava |
| F3 | Diğer sinyaller: içeriden işlem, geri alım, sermaye artırımı, SPK tedbir, işlem sırası — konu başlığından, LLM'siz | bedava |
| F4 | Site: bağlam kartı, filtre çipleri, piyasa bandı | — |
| F5 | Araştırma: yukarıdaki üç soru, metodolojiye yeni bölüm | bedava |

## Sınırlar

- Portföy raporu fonun pozisyonunu gösterir, bireysel büyük yatırımcıyı
  göstermez. Muaf fonlar görünmez.
- Raporlar bir ay geriden gelir; "bugün" dediğimiz şey son rapordur.
- Pay alım satım bildiriminin yönü (alım mı satım mı) detay metninde;
  F3'te ilk sürüm yalnız varlığını sayar, yön ayrıştırması ayrı iş.
- Hiçbir sinyal skora girmez. Skor bildirimin büyüklüğüdür; bağlam hissenin
  durumudur. Bu ayrım Adım 16'dan beri projenin omurgası.
