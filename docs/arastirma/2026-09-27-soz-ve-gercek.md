# Söz ve gerçek — duyurulan iş ile gerçekleşen reel büyüme (2026-09-27)

**Durum: UYGULANIYOR (site v3, dal `feat/site-v3`).** Yeniden üretim:
`python scripts/ciro_seri_yaz.py && python scripts/analiz_soz_gercek.py --ayrinti`.

## Soru

KAP Radar bir işin şirket için büyüklüğünü ölçüyor: duyurulan tutar ÷
son 12 aylık ciro. Bu bir **söz**. Yatırımcının asıl sorusu farklı: çok
iş duyuran şirketler, sonra gerçekten büyüyor mu? Bu not iki ölçüyü yan
yana koyuyor. Nedensellik iddiası yok; betimleyici bir karşılaştırma.

## Tanım

**Gerçekleşen, reel ciro büyümesi.** Bir finansal raporun cari dönem
hasılatı ÷ aynı raporun "geçen yılın aynı dönemi" sütunu − 1. TMS 29
(yüksek enflasyonlu ekonomilerde finansal raporlama) karşılaştırma
sütununu cari dönem sonunun satın alma gücüyle yeniden ifade ettiriyor.
Böylece oran, dış TÜFE verisi olmadan reel büyüme veriyor ve
point-in-time kalıyor: iki sayı da aynı raporda.

**TMS 29 kapısı.** Yukarıdaki cümle yalnız raporunu yeniden ifade eden
şirkette doğru. Katsayı k = karşılaştırma sütunu ÷ aynı dönemin ilk
yayınındaki hasılat (`finansal.yeniden_ifade_katsayisi`, skorun TTM
köprüsünde de kullanılan fonksiyon). 6A2026'da ölçülen k iki değerli:
yeniden ifade edenlerde 1,321 (Haziran 2025 → Haziran 2026 TÜFE oranı),
etmeyenlerde tam 1,000. **k < 1,05 olan rapor reel sayılmıyor**
(`finansal.REEL_ESIK`). Söz yılında işi olan adaylardan dışarıda
kalanlar: ALCTL, BRSAN, ERCB, KLYPV, MARBL, NETAS, ODINE. Arşivin
tamamında 6A2026 raporu veren 140 şirketin 117'si reel, 13'ü k = 1, 10'unda
k çözülemiyor (karşılaştırılan dönemin ilk yayını arşivde yok ya da oran
kabul aralığının dışında). BDDK muafiyetli bankalar ve USD raporlayanlar da kapıda
kalıyor.

**Söz, duyuru yoğunluğu.** Y yılında duyurulan işlerin TL toplamı
(duyuru günü TCMB kuruyla) ÷ şirketin Y yılı cirosu (FY raporu, son
yayın). Aynı işin ihale ve sözleşme aşamasında iki kez duyurulması bir
kez sayılıyor (`bildirim_bag`, `ayni_is`). Skorsuz bildirimler toplamda
yok. Yıl sınırı İstanbul saatiyle.

**Dönem.** Büyüme dönemi P, kapsamı bir önceki çeyreğin en az %90'ı
olan en yeni çeyrek sonu (raporlama sezonu bitmeden yarım kapsamla
medyan oynar). Söz yılı Y = P'nin yılı − 1. Bugün P = 30.06.2026, Y = 2025.

**Özet.** Şirketler yoğunluğa göre üç eşit gruba ayrılıyor (Az duyuran
/ Orta / Çok duyuran; artan satır son gruba). Her grubun reel büyüme
medyanı ve ilişkinin Spearman sıra korelasyonu (eşitlikte ortalama
sıra) ile t istatistiği raporlanıyor (`src/kap_radar/soz_gercek.py`).

## Sonuç

64 şirket. Grup medyanları: **Az duyuran +%4,3 · Orta −%5,4 · Çok
duyuran +%20,8.** Grupların duyuru yoğunluğu medyanı 0,07× · 0,28× ·
0,81×. Spearman ρ = **0,24**, t = 1,91 (62 sd, iki yönlü p ≈ 0,06).

Okuma: **en çok duyuran üçte bir, 2026'nın ilk yarısında belirgin reel
büyüme gösterdi. Alttaki iki grup birbirinden ayrışmıyor. Sıra
ilişkisi zayıf ve %5 düzeyinde anlamlı değil.** Tek dönem, 64 şirket.

Örnek: ASELS 2025'te 29 iş duyurdu, toplamı 248,7 milyar TL = 2025
cirosunun (180,4 milyar TL) 1,38 katı. 2026'nın ilk yarısında cirosu
reel olarak %24,7 büyüdü. "Çok duyuran" grubunda, grubun medyanının
(+%20,8) biraz üstünde.

## Tanım ne kadar oynatıyor

| Varyant | n | Az / Orta / Çok | ρ | t |
|---|---|---|---|---|
| A · Σ ciro oranı, süzgeçsiz (maket v2) | 72 | +2,5 / −1,7 / +20,8 | 0,20 | 1,67 |
| B · Σ ciro oranı, yalnız reel | 65 | +0,8 / +2,0 / +19,6 | 0,24 | 1,99 |
| C · TL ÷ FY ciro, süzgeçsiz | 71 | +4,3 / +2,0 / +19,6 | 0,18 | 1,51 |
| **D · TL ÷ FY ciro, yalnız reel (seçilen)** | **64** | **+4,3 / −5,4 / +20,8** | **0,24** | **1,91** |

Dört varyantın hepsinde sabit kalan tek şey üst grubun yaklaşık %20'lik
medyanı. Alt iki grubun sırası varyanta göre değişiyor. D sonuca
bakılarak seçilmedi, iki ilkeyle seçildi:

1. **Reel olmayanı reel diye göstermemek.** A ve C yedi şirketin
   nominal büyümesini (yaklaşık %32 enflasyon dahil) reel sayıyor.
2. **Sitede tek oran biçimi.** Hisse sayfasındaki tez cümlesi "dönemde
   duyurulan TL ÷ dönemin cirosu" diyor ve okuyucu iki sayıyı bölerek
   doğrulayabiliyor. Σ ciro oranı (A, B) her işi kendi tarihindeki
   ciroya bölüyor. Birim tutarlı ama ekrandan doğrulanamıyor. ASELS'in
   son 12 ayında iki biçim 1,98 ve 1,67 veriyor.

Varyant tablosu D'nin şanslı bir seçim olmadığını göstermek için
burada: ρ dört varyantta 0,18–0,24 arasında, hiçbiri %5'te anlamlı değil.
B'nin t'si (1,99) en yüksek olanı; seçilen D ondan düşük.

## Sınırlar

- **Tek dönem.** Kasım'da 9A2026 raporları gelince site kendi kendine
  P = 30.09.2026'ya geçer. Sonuç zayıflarsa zayıflamış hâli gösterilir;
  metin veriden türüyor, sabit yazılmadı.
- **Zamanlama.** Sözleşmeler çoğu zaman çok yıllık. 2025'te duyurulan
  bir işin ciroya yansıması 2027'ye kayabilir. İlişki gecikmeyle
  güçlenebilir de zayıflayabilir de; burada ölçülmedi.
- **Birim.** Duyurular yıl içine yayılmış nominal TL, FY cirosu Aralık
  TL'si. Yoğunluk bu yüzden tekdüze biçimde yaklaşık %10–15 küçük
  okunuyor. Sıralamayı ve grupları bozmuyor.
- **Seçilim.** Yalnız 2025'te skorlu işi olan ve 6A2026 raporu veren
  şirketler var. Hiç iş duyurmayan şirketler karşılaştırmada yok. Bu,
  "duyuranlar duyurmayanlardan fazla mı büyüdü" sorusunu cevaplamıyor.
- **Nedensellik yok.** Çok duyuran şirketler zaten büyüyen sektörlerde
  olabilir (savunma). Sektör etiketi veride yok, kontrol edilemedi.

## Sitede nasıl anlatılıyor

Ana sayfa: üç grup medyanı, her şirket bir nokta, "dürüst okuma"
paragrafı. "Üst grup belirgin önde" cümlesi yalnız üst grubun medyanı
diğer ikisinin büyüğünü 10 puandan fazla aştığında kuruluyor
(`soz_gercek.ONDE_ESIGI`). Paragraf ρ'yu, anlamlı olmadığını ve tek
dönem olduğunu her zaman söylüyor.

Hisse sayfası: şirketin kendi sözü (2025 yoğunluğu) ve gerçeği (6A2026
reel büyüme) ile grubunun medyanı. Söz, gerçekten önce ölçülüyor. Son
12 ayın duyurularıyla geçmiş bir dönemin büyümesini yan yana koymak
söz ile gerçeğin sırasını bozardı.

Hesap iki yerde yapılıyor: Python (`soz_gercek.py`, bu not) ve site
(`site/lib/soz.ts`). İkisi aynı fikstürle (`tests/fixtures/soz_gercek.json`)
sınanıyor. Biri değişip öteki unutulursa testlerden biri kırılır.
