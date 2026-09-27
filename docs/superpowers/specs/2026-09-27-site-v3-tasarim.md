# KAP·RADAR site v3 — tasarım belgesi

Tarih: 2026-09-27 · Durum: **onaylandı (maket v2 + "Söz ve gerçek"), uygulanmadı**
Dal: `feat/site-v3` · Maket: https://claude.ai/artifact/UwkLgaj1E578WCUnjDAXwd (v2)
Önceki bilgi mimarisi kararı: 2026-09-26 beyin fırtınası ("ürün önde")

---

## 1. Amaç

Site bugün yalnız bir bildirim akışı. Ziyaretçi bir hissenin hikâyesini
göremiyor, ürünün ne yaptığını ilk ekranda anlamıyor ve projenin
arkasındaki mühendislik görünmüyor. v3'ün üç hedefi var:

1. **Ürün önde.** Her sayfada hisse arama. Ana sayfa ürünün ne yaptığını
   tek bir görselle gösteriyor. Hisse sayfası bir hikâye anlatıyor.
2. **Söz ve gerçek.** Sitenin ölçtüğü "söz" (duyurulan iş) ilk kez
   gerçekleşenle (reel ciro büyümesi) yan yana konuyor, zayıf sonuç
   olduğu gibi raporlanıyor.
3. **İşveren için vaka çalışması.** Proje sayfası, veri hattını ve
   denetim hikâyesini okunabilir bir anlatıya çeviriyor.

Kalite ölçütü Hüseyin'in cümlesi: *"Bu çocuk ne yaptığını biliyor"
dedirten kalite.* Pratikte bunun anlamı: her sayı kaynağına iniyor,
hiçbir istatistik abartılmıyor, telefonda da kusursuz.

## 2. Bilgi mimarisi

| Rota | İçerik | Durum |
|---|---|---|
| `/` | Kahraman + ölçek cetveli plakası, en büyük üç iş, Söz ve gerçek, nasıl çalışıyor, son bildirimler | yeniden yazılıyor |
| `/akis` | Bugünkü süzgeçli akış (J/K, detay paneli) | **yeni rota**, mevcut `Akis` bileşeni taşınıyor |
| `/hisse` | 144 şirketin aranabilir, sıralanabilir dizini | **yeni** |
| `/hisse/[ticker]` | Hikâye: tez cümlesi, söz-gerçek kartı, duyuru/ciro grafiği, işler, kiminle, bağlam | yeniden yazılıyor |
| `/kap/[kap_id]` | Kanıt sayfası; üste şirketin diğer işleri ve hikâyeye bağlantı | eklenti |
| `/proje-hakkinda` | İşverene vaka çalışması | yeniden yazılıyor |
| `/metodoloji` | Makale | yalnız görsel uyum |
| `/film` | Film | menüden çıkıyor, proje sayfasından bağlanıyor |

**Başlık (her sayfada):** logo · hisse arama · Hisseler / Akış / Yöntem /
Proje. Telefonda logo + menü düğmesi, arama ikinci satırda tam genişlik.
Altında tek satır ibare: *Kişisel araştırma projesi · yatırım tavsiyesi
değildir · fiyat tahmini üretmez.* Bugünkü iki bant (UYARI + PİYASA) bu
tek satıra iniyor. Piyasa bağlamı yalnız ana sayfada, son bildirimlerin
üstünde.

**Arama:** 144 hisse (ticker, unvan, bildirim sayısı) derleme anında
sayfaya gömülür, arama istemcide çalışır. Ticker önekiyle ya da unvan
içinde eşleşir. ↑/↓ ile seçilir, Enter hisse sayfasına gider, `/` tuşu
kutuya odaklanır, Esc kapatır. Eşleşme yoksa "Bu adla bildirim yok;
arşivde N şirket var" yazar.

## 3. Görsel sistem

Mevcut kimlik korunuyor: kâğıt zemin (`#f2eee3`, nokta ızgara), IBM Plex
Serif başlıklar, Plex Sans metin, JetBrains Mono sayılar ve etiketler.
v3'ün eklediği tek şey **veri plakası**: ana görseller koyu mürekkep
zeminde (`#1b1a16`), bej üstüne bej düzlüğünü kırıyor.

Renkler (her iki zemin için CVD ve kontrast doğrulandı):

| Rol | Kâğıtta | Plakada |
|---|---|---|
| Duyurulan (seri) | mavi-koyu `#135298` | mavi `#4a8fd6` |
| Ciro (seri, kesikli) | toprak `#9a5b2e` | toprak `#bd7b44` |
| Mega iş | `#135298` | `#a6cbf1` |
| Önemli iş | `#2677b2` | `#4a8fd6` |
| Rutin iş | `#9b9480` | `#7a7466` |

Kehribar, yeşil ve kırmızı durum renkleri seri rengi olarak kullanılmaz.

**İmza öğesi, ölçek cetveli:** logaritmik `f(r)` (%0,25 taban, %100
tavan, sitenin skor ölçeğiyle aynı) üstünde %5 ve %15 çentikleri. Her
iş satırında küçük, ana sayfada büyük (plaka) hâliyle var.

**Yazım kuralları:**
- Unvanlar KAP'taki gibi büyük harf, `.unvan` stiliyle küçültülüp
  aralıklanır. Başlık düzenine çevrilmez: "SDT" → "Sdt" bozulması
  maket v1'de görüldü.
- Grafik etiketlerinde bilinen kurumlar kısaltmayla (SSB, ASFAT),
  kalanlar ilk sözcükle.
- Mobil ızgaralarda `minmax(0, 1fr)`: düz `1fr` uzun kelimede taşıyor.
  Kabul ölçütü: 390 px'te yatay kaydırma sıfır.

## 4. Sayfalar

### 4.1 Ana sayfa `/`

1. **Kahraman.** Sol: etiket, başlık ("Bir şirket yeni iş duyurdu.
   *Kendi cirosuna göre* ne kadar büyük?"), bir paragraf, büyük arama
   kutusu, en çok duyuran beş hissenin hızlı düğmeleri ve canlı veri
   satırı (bildirim sayısı · şirket sayısı · son bildirim tarihi).
   Sağ: **cetvel plakası.** Son 14 günün her işi, log cetvel üstünde
   arı kovanı dizilimiyle bir nokta. Arka planda rutin/önemli/mega
   bölgeleri ve bölge sayıları var. En büyük beş iş çakışmasız
   etiketlenir, yer yoksa etiket konmaz (ipucu var). Noktalar klavyeyle
   odaklanabilir. 14 günde 8'den az iş varsa pencere 30 güne uzar,
   başlık bunu söyler.
2. **En büyük üç iş.** Aynı penceredeki en yüksek ciro oranlı üç iş
   kartı. `ayni_is` tekrarları sayılmaz.
3. **Söz ve gerçek** (§5).
4. **Nasıl çalışıyor.** Üç adım (okunur → çıkarılıp kapıdan geçer →
   ciroya bölünür), her adımın altında kanıt satırı. Sayılar
   veritabanından gelir, sabit yazılmaz.
5. **Son bildirimler.** Piyasa bağlamı satırı (eşit ağırlıklı BIST ve
   XU100, son 5 seans) ve son 8 bildirim. Satırda tarih, ticker, özet,
   ciro oranı ve cetvel var. Sonunda "Bütün bildirimler ve süzgeçler →
   /akis" bağlantısı.

Satırlardan "3 günde piyasaya göre" değeri **çıkıyor**. Gürültülü ve
alım satım sinyali gibi okunuyor; bildirim sayfasında kalıyor.

### 4.2 Hisse sayfası `/hisse/[ticker]`

1. **Kimlik:** ticker, unvan, meta (arşivdeki bildirim sayısı, son 12
   aylık ciro).
2. **Tez cümlesi:** "Son 12 ayda **15 iş** duyurdu. Toplamı **375,5
   milyar TL**: yıllık cirosunun *1,7 katı*." Oran = son 12 ayda
   duyurulan TL toplamı ÷ bugün bilinen son 12 aylık ciro. Okuyucu iki
   sayıyı bölerek doğrulayabilir. Altında sabit not: duyurular çok
   yıllık, ciro bir yıllık; oran büyüklük söyler, gelecek yılın
   cirosunu söylemez.
3. **Söz-gerçek kartı** (§5.4).
4. **Grafik plakası:** kayan 12 ayda duyurulan toplam (mavi çizgi,
   dolgulu) ile aynı gün bilinen son 12 aylık ciro (toprak, kesikli).
   Tekil işler kademe renginde çubuklar, en büyük üçü doğrudan
   etiketli (ör. "SSB 79"). Başlık veriye göre kurulur: iki seri
   kesişmiyorsa "Son bir yılın her gününde, duyurulan işler yıllık
   cirodan büyüktü", kesişiyorsa nötr başlık. İmleçle gün gün okunur.
   "Tablo olarak göster" erişilebilir alternatiftir.
5. **Bütün işler:** aylara bölünmüş liste. Satırda gün, özet, karşı
   taraf, asıl para birimindeki kalem, TL, cetvel ve kademe var.
   "Tekrar" ve "Güncelleme" işaretleri görünür. Süzgeçler: Tümü /
   Önemli ve üstü / Karşı tarafı belli. İlk 16 satır açık, gerisi
   düğmeyle.
6. **Yan sütun:** "Kiminle iş yapıyor?" (son 12 ay, karşı taraf
   başına TL çubuğu, adı verilmeyenler sonda) · "Hisse ve şirket"
   (tahta durumu ve piyasa taban oranı, bildirim sıklığı yalnız sayım
   olarak) · fon sahipliği katlanmış `<details>` içinde.

Çıkan iddia: "Sık bildirimci: her duyuru daha az şaşırtıcı." Bulgu 7
örneklem dışında tekrarlanmadı (2026-09-24), iddia olarak duramaz.

### 4.3 Hisse dizini `/hisse`

Tablo, her satır bir şirket. Sütunlar: ticker · unvan · son 12 ayda
iş sayısı · son iş tarihi · son 12 ay duyurulan/ciro (kat) · son
dönem reel ciro büyümesi (yeniden ifade etmeyenlerde "—") · tahta.
Sütun başlığına tıklayınca sıralanır, üstte süzgeç kutusu var.
Varsayılan sıra son iş tarihi. Telefonda tablo kart listesine döner.

### 4.4 Bildirim sayfası `/kap/[kap_id]`

Mevcut kanıt sayfası korunuyor. İki eklenti var: üstte "ŞİRKET
hikâyesi →" bağlantısı, altta "Şirketin diğer işleri" (son 5, satır
bileşeni). Güncelleme zinciri `bildirim_bag` üzerinden zaten
gösteriliyor, dokunulmuyor.

### 4.5 Proje sayfası `/proje-hakkinda`

İşverene vaka çalışması. Sıra: sorun → veri hattı (KAP → çıkarım →
kapı → ciro, point-in-time) → ölçülen doğruluk (altın kümede 50'de
47) → **denetim hikâyesi** (ARDYZ muhammen bedeli; kapının neyi
denetlemediği; eklenen B4–B6, A7; 23 elle karar) → ampirik sınama
(tutanlar ve örneklem dışında tutmayanlar) → Söz ve gerçek → maliyet
(gerçek sayılarla) → Claude ile nasıl çalışıldı (kararlar Hüseyin'in,
kod ortak) → film. Sayılar metne gömülmez, veritabanından ya da
repodaki notlardan gelir. Hiçbir iddia `docs/arastirma/` altındaki
notlardan güçlü olamaz.

## 5. Veri eklentisi: Söz ve gerçek

### 5.1 Soru

"Çok iş duyuran şirketler, ertesi yıl gerçekten büyüdü mü?" Site
bugün yalnız sözü ölçüyor. Bu modül sözü gerçekleşenle karşılaştırıyor.
Nedensellik iddiası yok; betimleyici bir karşılaştırma.

### 5.2 Tanım (sabit, sonuca bakılarak değiştirilmez)

- **Gerçekleşen, reel ciro büyümesi.** Bir raporun cari dönem
  hasılatı ÷ aynı raporun "geçen yılın aynı dönemi" sütunu − 1. TMS 29
  gereği iki sütun aynı satın alma gücüyle raporlanıyor. Bu yüzden
  oran, dış TÜFE verisi olmadan **reel** büyüme veriyor.
- **TMS 29 kapısı.** Yukarıdaki cümle yalnız raporunu yeniden ifade
  eden şirkette doğru. Yeniden ifade katsayısı `k` = karşılaştırma
  sütunu ÷ aynı dönemin ilk yayınındaki hasılat. Bu, mevcut
  `finansal._yeniden_ifade_katsayisi` fonksiyonunun kendisi, ikinci
  kopya yazılmıyor. **`k ≥ 1,05` olmayan rapor reel sayılmaz.**
  Ölçülen (6A2026, 72 aday): k iki değerli, 65 şirkette 1,321 (Haziran
  TÜFE oranı), 7 şirkette tam 1,000 (ERCB, NETAS, BRSAN, MARBL, KLYPV,
  ODINE, ALCTL). Bu 7 şirketin "büyümesi" nominal. Kapı, BDDK muafiyetli
  bankaları ve USD raporlayanları da kendiliğinden dışarıda bırakıyor.
  Eşik %5, yıllık enflasyon %5'in üstünde kaldıkça güvenli.
- **Söz, duyuru yoğunluğu.** Y yılında duyurulan işlerin TL toplamı ÷
  şirketin Y yılı cirosu (FY raporu, son yayın). `ayni_is` tekrarları
  ve skorsuz bildirimler toplamda yok. Hisse sayfasındaki tez cümlesiyle
  **aynı biçim**: bir dönemde duyurulan TL ÷ o dönemin cirosu.
- **Dönem seçimi.** Büyüme dönemi P, raporların geldiği en yeni çeyrek
  sonu. Kural: kapsamı, bir önceki çeyreğin kapsamının en az %90'ı
  olan en yeni dönem. Söz yılı Y = P'nin yılı − 1. Bugün P = 30.06.2026
  (6A2026), Y = 2025. Kasım'da 9A2026 raporları gelince modül kendi
  kendine güncellenir, sonuç zayıflarsa zayıflamış hâli gösterilir.
- **Gruplar.** Şirketler duyuru yoğunluğuna göre üç eşit gruba ayrılır:
  Az duyuran / Orta / Çok duyuran. Her grubun reel büyüme medyanı ve
  duyuru yoğunluğu medyanı gösterilir. İlişki Spearman sıra
  korelasyonu ve t istatistiğiyle özetlenir.

### 5.3 Bugünkü sonuç ve nasıl anlatılacağı

Tanımın bugünkü çıktısı (2026-09-27): **64 şirket**, grup medyanları
**+%4,3 / −%5,4 / +%20,8**, ρ = **0,24**, t = 1,91 (%5'te anlamlı
değil). Duyuru yoğunluğu grup medyanları 0,07× / 0,28× / 0,81×.

Tanım varyantlarında sonuç ne kadar oynuyor (hepsi 6A2026):

| Varyant | n | Az / Orta / Çok | ρ | t |
|---|---|---|---|---|
| Maket v2 (Σ ciro oranı, TMS 29 süzgeci yok) | 72 | +2,5 / −1,7 / +20,8 | 0,20 | 1,74 |
| Σ ciro oranı, TMS 29 süzgeçli | 65 | −1,6 / +2,1 / +19,6 | 0,25 | 2,06 |
| TL ÷ FY ciro, süzgeçsiz | 71 | +4,3 / +2,0 / +19,6 | 0,18 | 1,51 |
| **TL ÷ FY ciro, TMS 29 süzgeçli (seçilen)** | **64** | **+4,3 / −5,4 / +20,8** | **0,24** | **1,91** |

Her varyantta sabit kalan tek şey: **en çok duyuran üçte bir yaklaşık
%20 reel büyüdü, alttaki iki grup birbirinden ayrışmıyor.** Seçilen
tanım sonuca bakılarak değil iki ilkeyle seçildi: reel olmayanı reel
diye göstermemek ve sitede tek oran biçimi kullanmak.

*Güncelleme (27.09.2026, K2 TÜFE düzeltmesinden sonra):* A ve B satırları
değişti (her işi kendi tarihindeki ciroya bölüyorlar, 2024 ara dönem
paydası düzeldi). B'nin t'si 2,06: %5 eşiğini kıl payı geçiyor. Seçilen
D değişmedi (1,91) ve D'de kalınıyor; gerekçe
`docs/arastirma/2026-09-27-soz-ve-gercek.md`'de.

Sitedeki "dürüst okuma" metni bu cümleyi söyler, sonra şunları ekler:
ρ ve anlamlı olmadığı, tek dönem olduğu, sözleşmelerin çok yıllık
olduğu ve bunun bir neden-sonuç iddiası olmadığı. "Vay, bulduk"
çerçevesi yasak. Metin grafikten türetilir: sonuç değişirse cümle
de değişir. "En çok duyuran grup belirgin önde" ifadesi, yalnız o
grubun medyanı diğer ikisinin en büyüğünü 10 puandan fazla geçiyorsa
kurulur.

### 5.4 Hisse sayfasındaki kart

**Söz, gerçekten önce gelmeli.** Maket v2 kartı "son 12 ayda duyurulan
1,7×" ile "2026 ilk yarı büyüme"yi yan yana koyuyordu. Oysa son 12
ayın duyuruları büyüme döneminden sonraya da uzanıyor: söz
gerçekleşmeden önce ölçülmüş olmuyor. Kart ana sayfa modülünün
tanımını kullanır:

- **Söz:** "2025'te duyurulan · yıllık cirosunun 1,4 katı (29 iş)"
- **Gerçek:** "2026 ilk yarı · enflasyondan arındırılmış ciro
  büyümesi +%24,7"
- Alt satır: şirketin grubu ve grup medyanı ("Çok duyuran grubunda;
  grubun medyanı +%20,8").

Şirket kapıdan geçemiyorsa (`k` < 1,05) gerçek hücresi "Şirket
raporunu enflasyona göre yeniden ifade etmiyor; reel büyüme
hesaplanamıyor" der. Söz yılında hiç skorlu işi yoksa kart gösterilmez.
Son 12 ay ölçüsü tez cümlesinde kalır.

## 6. Veri katmanı

### 6.1 Yeni türetilmiş tablolar (Python yazar, site okur)

**`ttm_seri`, point-in-time ciro basamakları.** Bir satır, bir
şirketin son 12 aylık cirosunun değiştiği an: her finansal raporun
`yayin_zamani` anında `finansal.ttm_coz` çağrılır, değer değiştiyse
satır yazılır. Sütunlar: `ticker, gecerlilik_basi, hasilat, donem_sonu,
yontem, enflasyon_carpani, kaynak_kap_index`. Maketteki aylık örnekleme
bir aya kadar gecikebiliyordu. Olay bazlı seri tam point-in-time ve
daha küçük. Grafik ciroyu bu basamaklardan çizer.

**`donem_buyume`, rapor başına reel büyüme.** Bir satır = bir
(ticker, dönem sonu, ay sayısı) için son yayın; her rapor dönemi, FY
dahil. Sütunlar: `ticker, kap_index, donem_sonu, ay_sayisi,
yayin_zamani, hasilat, onceki_yil_hasilat, buyume, katsayi, reel`.
`buyume` karşılaştırma sütunu yoksa boş; `reel = katsayi >= 1,05`.
FY satırları (`ay_sayisi = 12`) sözün paydası olan yıllık ciroyu da
taşıdığı için ayrı bir kaynak gerekmiyor.

Söz ve gerçek modülü ayrı tablo değil. Sitede `akis` + `donem_buyume`
üzerinden hesaplanır.
Bu, mevcut `panelleriHesapla` kalıbıyla aynı: site görüntü
istatistiklerini (medyan, sıra korelasyonu) saf, testli bir
fonksiyonda kendisi hesaplıyor.

**Tek kaynak kuralı:** TTM ve `k` mantığı yalnız `finansal.py`'de.
Yeni kod onu çağırır, kopyalamaz. `_yeniden_ifade_katsayisi` herkese
açık bir ada taşınır.

### 6.2 Siteye açılış

Tablolar RLS açık, politikasız (mevcut kural). Site bunları
`akis`/`piyasa_bandi` kalıbıyla, `security_invoker` olmayan ve
`anon`'a `select` verilen iki görünümden okur: `ciro_seri` (←
`ttm_seri`) ve `reel_buyume` (← `donem_buyume`). Görünümler yalnız
sitenin kullandığı sütunları açar; iç sütunlar (`yuklendi_at` vb.)
dışarıda kalır.

### 6.3 Günlük hat ve denetim

- `scripts/gunluk.py`'ye "finansal -> DB" adımından sonra yeni bir adım
  eklenir: `scripts/ciro_seri_yaz.py`. İki tabloyu idempotent olarak
  baştan yazar. Ağ yok, birkaç saniye.
- `veri_denetimi.py`'ye bir tutarlılık kontrolü eklenir: her şirketin
  son `ttm_seri` değeri `sirket.son_yillik_hasilat_tl` önbelleğiyle
  aynı olmalı.
- Yeni görünüme sütun eklendiğinde `site/.next/cache/fetch-cache`
  silinir (2026-09-23 dersi).

### 6.4 Araştırma notu

`docs/arastirma/2026-09-27-soz-ve-gercek.md`: tanım, TMS 29 kapısı,
§5.3 tablosu ve sınırlar. Tablo, repoya giren bir analiz betiğiyle
(`scripts/analiz_soz_gercek.py`) yeniden üretilir. Sitedeki sayı ile
betiğin "seçilen" satırı aynı olmalı. Uygulama planı bunu bir
karşılaştırma adımıyla sınar.

Bilinen sınırlar (nota ve siteye): duyurular yıl içine yayılmış nominal
TL, FY cirosu Aralık TL'si, bu yüzden yoğunluk tekdüze biçimde %10–15
küçük okunur (sıralamayı bozmaz). Tek dönem. Hayatta kalan yanlılığı:
yalnız rapor vermiş şirketler var.

## 7. Uygulama ilkeleri

- Grafikler SVG. Sunucuda sabit genişlikte çizilir, JS olmadan da
  görünür. İstemcide gerçek genişliğe göre yeniden yerleşir. Yerleşim
  (arı kovanı çarpışması, etiket yeri, gruplama, sıra korelasyonu) saf
  fonksiyonlarda, `node --test` ile testli.
- Skor ve oran sitede hesaplanmaz, okunur. Kademe eşikleri tek yerde
  (`lib/skor.ts`).
- Her iş satırı ve nokta klavyeyle odaklanabilir. İpucu odakta da
  açılır. Grafiklerin tablo alternatifi var.
- Sayfalar statik + saatlik tazeleme (bugünkü gibi).

## 8. Doğrulama

- Python: yeni fonksiyonlara pytest (TTM basamakları, reel kapısı,
  aynı dönemin çift raporu), `pyflakes scripts src` temiz.
- Site: `npm test` (saf fonksiyonlar), `npx tsc --noEmit`,
  `npm run build`.
- Görsel: puppeteer ile 1280 px ve **emüle edilmiş** 390 px (headless
  `--window-size` 504 px çiziyor, 2026-09-23 dersi). Ana sayfa, ASELS
  ve bir küçük şirket sayfası, dizin. Ölçüt: yatay taşma 0, üst üste
  binen etiket yok, konsol hatası yok.
- İçerik: Söz ve gerçek sayıları §6.4'teki betikle karşılaştırılır.

## 9. Kapsam dışı

Üyelik ve alarm, fiyat grafiği (Yahoo lisansı), İngilizce site, sektör
etiketi (`sirket.sektor` 144 şirketin hiçbirinde dolu değil, uydurma
olur), EKAP doğrulaması, sözleşme süresine göre yıllıklandırma (ücretli
yeniden çıkarım ister).

## 10. Maket v2'den sapmalar

Dördü de yazarken yapılan kontrollerden çıkan düzeltmeler. Tasarımın
kendisi değişmiyor.

1. **TMS 29 kapısı eklendi.** Maketteki 72 şirketin 7'si reel değil
   nominal büyüme gösteriyordu.
2. **Tek oran biçimi.** Maket ana sayfada Σ ciro oranı, hisse
   sayfasında TL ÷ TTM kullanıyordu. ASELS'te ikisi 1,98 ve 1,67
   çıkıyor. Artık ikisi de "dönemde duyurulan TL ÷ dönemin cirosu".
3. **Hisse kartında söz, gerçekten önce.** §5.4.
4. **Ciro serisi olay bazlı**, aylık örnek değil. §6.1.

Sonuç sayıları bu yüzden değişti: 72 → 64 şirket, +%3 / −%2 / +%21 →
+%4,3 / −%5,4 / +%20,8, ρ 0,20 → 0,24.

## 11. Açık riskler

- 9A2026 raporları gelince sonuç zayıflayabilir. Tasarım bunu
  saklamıyor, metin veriden türüyor.
- Cetvel plakası seyrek haftalarda boş görünebilir. 30 güne uzatma
  kuralı var.
- `/` bugün 1.267 satırı istemciye gönderiyor. Akış `/akis`'e taşınınca
  ana sayfa hafifliyor. `/akis`'in yükü aynı kalıyor.
