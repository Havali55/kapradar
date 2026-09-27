# Bulgular ne kadar genellenebilir? Piyasa rejimi, kirlenme ve güç (2026-09-27)

**Durum: KARARLAR VERİLDİ (2026-09-27).** Hüseyin K1 (bedava katman),
K2 (a) ve K3'ü onayladı:

- **K2:** 2024 paydası resmî TÜFE ile düzeltildi. 253 skor değişti.
  Commit `f2f083d`.
- **K3:** Metodoloji makalesi sürüm 2.1'e güncellendi.
- **K1:** 2020–2024 arşivi `scripts/rejim_arsivi.py` ile hazırlanıyor.

Yeniden üretim (ikisi de yazmaz, LLM yok):

- `python scripts/analiz_gecerlilik.py`: arındırma, güç, kümelenme,
  payda. Yalnız veritabanı ve yerel KAP arşivi.
- `python scripts/analiz_piyasa_rejimi.py`: 2019–2026 çerçevesi, aylık
  spekülasyon ölçüleri, rejime duyarlılık. Ek olarak yfinance'e çıkar
  (ücretsiz).

Web kaynaklı olgular (faiz kararları, olaylar, yatırımcı sayıları) §9'da
kaynaklarıyla listeleniyor. Metinde bunlar veriden ayrı tutuldu.

## Özet

- **Sağlam.** Bildirim günü hacmi artıyor (Bulgu 1) ve ortalama 3 günlük
  tepki pozitif. Bu iki sonuç şunların hepsinden arındırıldıktan sonra
  ayakta kalıyor:
  - piyasanın genel hacim dalgası
  - aynı pencerede yapılan başka açıklamalar
  - sermaye işlemleri
  - aynı haftaya yığılan şoklar

  Sakin ve spekülatif aylarda, fonların yoğun tuttuğu ve tutmadığı
  hisselerde, iki yılın ikisinde de görünüyor.
- **Zayıfladı.** Bulgu 2'nin "bilgi resmî açıklamadan önce sızıyor"
  yorumu. Ön-hacmin yarıdan fazlası şirketin önceki günlerdeki kendi KAP
  açıklamalarıyla örtüşüyor, kalanı anlamlı değil.
- **Döneme özgü.** Bulgu 12 (oynak tahtada bildirim sonrası aşağı yön),
  sonradan tasfiye edilen fonların yoğun tuttuğu hisselerde toplanıyor.
  Fonların pozisyonu arttıkça etki büyüyor. Oynak tahtaların genel bir
  özelliği olarak sunulmamalı.
- **Yeni kusur.** 2024 ara dönemlerinde skorun paydası TMS 29 geçişi
  yüzünden bozuk. 235 bildirimi etkiliyor, skordaki kayma en fazla ~0,3.
- **Genelleme.** Bütün bulgular 2024-09 → 2026-09'a, yani yüksek reel faiz
  ve bireysel yatırımcının çekildiği döneme ait. Seçim öncesi negatif reel
  faiz dönemine taşınamaz, çünkü o dönemden tek gözlem yok.

## 1. İtiraz

Hüseyin (2026-09-27), özetle:

> Seçimden sonra faizler yüksek olduğu için borsada hacim yoktu. Bu
> yılki yükseliş sanıldığı gibi değil; fonlar ve manipülatif olaylar
> sürükledi, son yıl tamamen spekülatif. Seçimden önce de enflasyon
> yüksekti ama borsa çok yükseldi. Bu koşullarda yapılan ölçümler
> arınmış sayılmaz. Buradan genel bir çıkarım yapılabilir mi?

Burada iki ayrı soru var:

1. **İç geçerlilik:** Ölçülenler gerçekten bildirimin etkisi mi, yoksa
   dönemin gürültüsü mü?
2. **Dış geçerlilik:** Bu dönemde doğru olan, başka bir para rejiminde de
   doğru mu?

Not, Hüseyin'in tespitlerini tek tek veriyle karşılaştırıyor (§3). Onların
dışında kalan piyasa olaylarını da çerçeveye katıyor (§2).

**Önceki çalışma bu itirazı karşılamıyordu.** Metodoloji makalesi "tek
rejimli örneklem" diye bir sınır yazmıştı ama çalışma rejime göre
kurulmamıştı. Ayrıca örneklem dışı sınamanın iki yılı (2024-09 → 2025-09
ve 2025-09 → 2026-09) aynı sıkı para dönemine ait. Sınama "bir yıl sonra
da tutuyor mu"yu ölçtü, "başka rejimde tutuyor mu"yu ölçmedi.

## 2. Piyasa çerçevesi, 2019–2026

### Para rejimleri ve endeks (yfinance XU100 ve USD/TRY)

| Rejim | Dönem | Politika faizi | XU100 yıllık TL | Yıllık USD | Oynaklık | −%3'ten sert gün / yıl |
|---|---|---|---|---|---|---|
| Gevşek para | 2019-07 → 2023-05 | %8,5–19, enflasyonun çok altında | +%50,1 | +%8,2 | %28,6 | 10,5 |
| Sıkılaştırma | 2023-06 → 2024-12 | %8,5 → %50 | +%54,0 | +%10,2 | %26,8 | 8,2 |
| Kademeli indirim | 2025-01 → 2026-09 | %50 → %37; Nisan 2025'te ara artış | +%16,1 | −%3,8 | %24,6 | 4,1 |

Yarıyıllara bakınca üç şey öne çıkıyor:

- **Seçim öncesi zirve:** 2022 ikinci yarısında XU100 TL bazında %129,
  dolar bazında %104 yükseldi.
- **Seçim sonrası borsa hemen durmadı:** 2023 ikinci yarısı +%29,7 (USD
  +%14,1), 2024 ilk yarısı +%42,5 (USD +%27,9).
- **Durgunluk faiz %50'ye çıktıktan sonra başladı:** 2024 ikinci yarısı
  −%7,7 (USD −%14,0), 2025 ilk yarısı +%1,2 (USD −%10,4).

**Örneklemimiz (Eylül 2024 →) tam olarak bu durgun dönemde.** İki yılda
XU100 TL bazında %27,5 yükseldi, dolar bazında %11,3 düştü. Yıllık
enflasyon (şirketlerin TMS 29 katsayılarından) %44'ten %32'ye indi. Reel
kayıp kabaca %27.

### Örneklemdeki büyük olaylar

| Tarih | Olay | Veride |
|---|---|---|
| 19–21 Mart 2025 | İBB Başkanı'na gözaltı kararı; endekse bağlı devre kesici | XU100 −%9,1 ve −%8,1 |
| 17 Nisan 2025 | TCMB politika faizini %42,5'ten %46'ya çıkardı | — |
| Q4 2025 | Savcılık ve SPK'ya göre, belirli fonlar düşük dolaşımlı paylarda açıklanamayan fiyat hareketlerine yol açmaya başladı | aynı dönemde EW − XU100 Kasım −%6,7, Ocak −%13,1 |
| Aralık 2025 | Finansal İstikrar Komitesi konuyu gündeme aldı; nitelikli yatırımcı eşiği 1 → 10 milyon TL | — |
| 21 Mayıs 2026 | CHP kurultay davasında "mutlak butlan" kararı; endekse bağlı devre kesici | XU100 −%6,2 |
| 19 Ağustos 2026 | Başsavcılık, bazı hisselerde 100 kata varan yükselişleri SPK'ya sordu | — |
| 15–17 Eylül 2026 | Pusula ve Tera fonlarında temerrüt; endekse bağlı devre kesici; SPK 7 portföy şirketinin 130 fonunu tasfiyeye aldı (yaklaşık 456 bin yatırımcı) | XU100 −%5,7; EW Temmuz–Eylül −%26,3 |

Hüseyin'in sözünü etmediği iki olay, Mart 2025 ve Mayıs 2026, siyasi
kaynaklı piyasa çapında şoklar. Örneklemin en sert iki günü de Mart
2025'te.

### Katılım

MKK'ya göre pay senedi bakiyeli yatırımcı sayısı 2023'te 8,6 milyonla
zirve yaptı. 2025 sonunda 6,51 milyona, 2026'da 6,4–6,9 milyon bandına
indi. Yabancıların işlem hacmi 2023'te 773 milyar dolar, 2024'te 607,
2025'te 713 milyar dolar.

Bu veri, sıkı para döneminde bireysel katılımın geri çekildiğini
destekliyor.

**Toplam işlem hacmi (resmî, 27.09 akşamı eklendi).** Kaynak, Borsa
İstanbul'un günlük pay piyasası bültenleri: 2020-01-02 → 2026-09-25
arası 1.690 işlem günü, pay (EQT) satırlarının TL işlem hacmi
(`scripts/rejim_arsivi.py bulten` ve `rapor`). yfinance'in endeks hacmi
kullanılamazdı: 2020'deki endeks sadeleşmesiyle 60 katlık bir kırılma
var ve seri pay adedi, TL değil.

| Yarıyıl | Günlük TL, nominal (mr) | Reel, Ağu 2026 TL (mr) | Günlük USD (mn) |
|---|---|---|---|
| 2020 Y1 | 18,6 | 175 | 2.872 |
| 2020 Y2 | 32,9 | 290 | 4.355 |
| 2021 Y1 | 31,4 | 257 | 4.093 |
| 2021 Y2 | 28,4 | 199 | 2.752 |
| 2022 Y1 | 43,4 | 214 | 2.926 |
| 2022 Y2 | 95,6 | 379 | 5.192 |
| 2023 Y1 | 90,2 | 305 | 4.590 |
| **2023 Y2** | 163,2 | **419** | 5.951 |
| 2024 Y1 | 153,4 | 306 | 4.857 |
| **2024 Y2** | 117,8 | **199** | 3.466 |
| **2025 Y1** | 142,0 | **204** | 3.792 |
| 2025 Y2 | 192,0 | 244 | 4.621 |
| 2026 Y1 | 266,1 | 291 | 5.970 |
| 2026 Y2 (Tem–Ağu) | 263,2 | 270 | 5.508 |

Rejim ortalamaları (reel, günlük): gevşek para 259, sıkılaştırma 308,
kademeli indirim 249 milyar TL. Dolar bazında 3,8 → 4,7 → 4,9 milyar
dolar.

Okuma:

- Reel hacmin zirvesi seçimden hemen sonraki yarıyıl (2023 Y2).
- Dip, faizin %50'ye çıkmasından sonraki bir yıl (2024 Y2 – 2025 Y1).
  Bu, 2021 sonundan beri en düşük seviye.
- Örneklemimiz tam bu dipte başlıyor ve 2026'daki toparlanmayı da
  kapsıyor.
- **Piyasa hacmi yarıyıllar arasında ~1,5 kat oynarken Bulgu 1 bu
  dalgayı izlemiyor** (yarıyıllık düzeltilmiş AV +%25 … +%38, dipte
  +%25 ve +%38). Bu, bulgunun piyasa hacim düzeyinden bağımsız olduğuna
  dair örneklem içi bir kanıt.

## 3. Hüseyin'in tespitleri, veriyle

| Tespit | Veri ne diyor | Hüküm |
|---|---|---|
| "Seçimden sonra faiz yüksek, borsada hacim yoktu" | Bireysel pay yatırımcısı 8,6 → 6,5 milyon. Resmî bültene göre reel işlem hacmi seçimden hemen sonra zirve yaptı (2023 Y2, günde 419 milyar TL, bugünün fiyatlarıyla). Dip, 2024 Y2 – 2025 Y1'de (199–204 milyar). Borsa da seçimden sonra bir yıl daha güçlü yükseldi (USD +%14, +%28). | **Kısmen doğru.** Katılım düştü ve hacim dibe vurdu, ama başlangıç seçim değil, faizin %50'ye çıkması (2024 ortası). |
| "İki yıl borsa pek yükselmedi" | Örneklem döneminde XU100 USD −%11,3, reel kabaca −%27. | **Doğru.** |
| "Seçimden önce enflasyon yüksekti ama borsa çok yükseldi" | Gevşek para döneminde XU100 yılda +%50 (TL), +%8 (USD). 2022 ikinci yarısı +%129. | **Doğru.** Ama bu dönem örneklemimizde hiç yok. |
| "Bu yılki yükseliş fonlar ve manipülasyon kaynaklı" | 2026 ilk yarısında XU100 +%25,4, BIST 30 +%33,7: büyük hisseler daha çok yükseldi. Haberler faiz indirimi, enflasyon beklentisi ve yabancı işlemlerini gösteriyor. Aynı dönemde küçük hisseler (EW) analiz yılında XU100'ün %27 gerisinde kaldı. Manipülasyon iddiası düşük dolaşımlı paylarda. | **Endeks düzeyinde hayır, küçük düşük dolaşımlı paylarda evet.** |
| "Son yıl tamamen spekülatif" | Analiz yılı sınama yılından daha spekülatif: seans başına devre kesici 54,3 / 38,5, ayda devre kesici gören hisse 396 / 332. Ama Borsa'nın kendi ölçüleriyle en spekülatif dönem seçim sonrası ralli (2023-09 → 2024-08): 68,5 devre kesici/seans, ayda 37 VBTS. Eylül 2026 (89,7) bir uç. | **Daha spekülatif, "tamamen" değil.** Ölçüler oynaklığı yakalıyor; sessiz, kontrollü yükselişi yakalamayabilir. |

## 4. İç geçerlilik: arındırma sınavları

1.253 CAR'lı olay, 144 hisse, 108 hafta. Yedi sınav (`analiz_gecerlilik.py`):

| Sınav | Bulgu 1 (hacim) | Ortalama CAR3 | Bulgu 12 (oynak tahta) | Bulgu 3/11 (skor ~ getiri) |
|---|---|---|---|---|
| Havuz (hisse kümeli) | +%38,1, t 10,5 | +%0,72, t 3,5 | −0,20 puan/gün, t −3,1 | t 0,4 |
| Piyasa hacmiyle düzeltilmiş | +%37,8, t 10,4 | — | — | — |
| Hisse + hafta iki yönlü kümeleme | t 10,0 | t 3,4 (takvim-zaman portföyü t 3,05) | t −2,6 | t 0,3 |
| Karışan açıklama yok (sıkı) | +%30,4, t 6,9 | — | −0,12, t −1,6 | t 1,4 |
| Yalnız diğer türler hariç (finansal rapor, sermaye işlemi, geri alım, kâr payı, birleşme, ihale) | — | — | −0,18, t −2,7 | — |
| Aynı şirketin başka yeni iş duyurusu hariç | — | — | −0,16, t −1,8 | — |
| Beş yarıyılın her biri | 5/5 pozitif, t > 4 | 5/5 pozitif; 2026 Y2'de ≈ 0 (+%0,09) | 5/5 negatif, 1'i anlamlı | işaret karışık |

Bulgu 12'de, karışan açıklamaların çıkarılmasıyla kaybolan anlamlılık
kısmen güç kaybı. Aynı büyüklükte rastgele alt örneklemlerin %77'sinde t
hâlâ anlamlı. Ama gözlenen katsayı (−0,120), rastgele alt örneklemlerin
%95'inden daha zayıf (sınır −0,118). Üst üste binen iş duyuruları etkinin
bir kısmını taşıyor.

**Bulgu 2 ayrıca:** ön-hacim [t0−4, t0−1] havuzda +%9,5 (t 3,8).
Şirketin önceki beş günde başka açıklaması olmayan 481 olayda +%3,6 (t
1,1). Yalnız başka yeni iş duyurusu olmayanlarda +%5,4 (t 1,8).

**Temiz çıkanlar:**

- **Sermaye işlemi kirliliği pratikte yok.** 89.061 hisse-gününde ±%10
  marjını aşan 46 gün var. Bunların 1'i CAR penceresine, 22'si hacim
  penceresine giriyor.
- **Tavan serisi 3 günlük pencereyi taşırmıyor.** Tavan gören 102 olayda
  t0+3…+5 arasında devam yok (−%0,98, t −1,0). "Büyük haber daha çok
  fiyatlanmıyor" sonucunu pencere kesmesi üretmiyor. Yan gözlem: tavan
  payı S ≥ 3'te %13,9, S < 1'de %6,8. Yani uç tepki büyük haberde iki kat
  sık, ortalama ise farklı değil.

**Güç (MDE, %80 güç, iki yönlü %5):**

| Ölçü | Yakalanabilen en küçük etki |
|---|---|
| Ortalama hacim | ~8,6 puan |
| Ortalama CAR3 | ~0,6 puan |
| CAR3 ~ S eğimi | ~0,6 puan/S |
| Hacim ~ S eğimi | ~0,068/S; ölçülen +0,04…+0,07 |

Bulgu 4'ün sonuçsuz kalması bu güçle beklenen bir sonuç.

## 5. Spekülasyon ve fonlar: bulgular nerede değişiyor

`analiz_piyasa_rejimi.py` iki sınıflama yapıyor:

- **Ay sınıfı:** O ayki piyasa çapında devre kesici yoğunluğunun
  tercili.
- **Fon sınıfı:** Sonradan tasfiye edilen fonların Ağustos 2026
  pozisyonunun, hissenin günlük işlem hacmine oranı.

| Grup | n | Hisse | Hacim (piyasaya göre) | CAR3 | Bulgu 12 (iki yönlü t) |
|---|---|---|---|---|---|
| Ay: sakin | 619 | | +%29,3 | +%0,55 | −0,17 (−2,1) |
| Ay: orta | 411 | | +%41,4 | +%0,88 | −0,14 (−1,7) |
| Ay: spekülatif | 233 | | +%23,1 | +%0,91 | −0,40 (−1,6) |
| Fon: tutmuyor | 486 | 84 | +%31,7 | +%0,60 | −0,14 (−1,2) |
| Fon: < 0,5 gün hacim | 640 | 50 | +%34,0 | +%0,75 | −0,18 (−2,3) |
| Fon: ≥ 0,5 gün hacim | 137 | 10 | +%24,2 | +%1,00 | −0,44 (−2,3) |
| Sınama yılı | 663 | | +%30,3 | +%0,61 | −0,14 (−2,3) |
| Analiz yılı | 600 | | +%34,0 | +%0,84 | −0,26 (−2,1) |

Okuma:

- **Hacim ve ortalama tepki her grupta var.** Spekülatif aylar ya da fon
  hisseleri bu iki bulguyu üretmiyor.
- **Bulgu 12 fon yoğunluğuyla büyüyor.** Fonların hiç tutmadığı hisselerde
  anlamlı değil. Fonların yoğun tuttuğu hisselerde üç kat büyük. Hüseyin'in
  "manipülasyon sonuçları şekillendirdi" sezgisi bu bulguda iz bırakıyor.
- **Sınırı ciddi:** Yoğun grupta yalnız 10 hisse var. Fon portföyü olaydan
  sonra (Ağustos 2026) ölçülüyor. Bir fonun hisseyi tutması manipülasyon
  kanıtı değil. Doğru cümle: "oynak tahtadaki aşağı yönlü tepki, sonradan
  tasfiye edilen fonların ağırlıklı olduğu hisselerde toplanıyor".

## 6. Yeni bulunan kusur: 2024 paydası (DÜZELTİLDİ, `f2f083d`)

**Düzeltme.** Karşılaştırılan dönem 31.12.2023'ten önce bittiyse ya da
katsayı yoksa, şirket TMS 29 uyguluyorsa yıllık terim resmî TÜFE
oranıyla taşınıyor: TÜFE(dönem sonu) / TÜFE(önceki Aralık), o gün
yayımlanmış olanıyla. Şirketin TMS 29 uygulayıp uygulamadığı, herhangi
bir raporundaki katsayıdan okunuyor.

Sonuç:

- 2024 köprülerinin 227'si TÜFE ile taşındı (ortalama çarpan 1,316).
- 253 skor değişti.
- Sitede 13 bildirimin kademesi iki yönde kaydı.
- Yayın kararı değişmedi.
- Politikası okunamayan 19 köprü düzeltmesiz kaldı.

Aşağıdaki metin kusurun kendisini anlatıyor.

Skorun paydası, ara dönem raporlarından kurulan bir köprüyle hesaplanıyor.
Köprünün yıllık terimi, şirketin kendi TMS 29 katsayısıyla cari birime
taşınıyor. Katsayı, geçen yılın aynı döneminin ilk yayınına bölünerek
bulunuyor. **2023 ara dönem raporları TMS 29 öncesi, tarihî maliyetle
yayınlanmıştı.** Bu yüzden 2024 ara dönemlerinde katsayı enflasyonu değil
muhasebe geçişini ölçüyor.

Kanıt verinin kendisinde: 9A2024 katsayısının medyanı 1,791, aynı
şirketlerin Aralık 2023 → Aralık 2024 (12 ay) katsayısı 1,444. Dokuz aylık
bir düzeltme on iki aylıktan büyük olamaz.

Etkilenen skorlu bildirimler:

- **152 bildirim** (Ekim 2024 – Mart 2025): çarpan ortalaması 1,52. Oran
  yaklaşık %10 küçük.
- **83 bildirim** (Eylül 2024 – Şubat 2025): katsayı yok, köprü
  düzeltmesiz. Oran %25–35'e kadar büyük.

Skor logaritmik olduğu için kayma en fazla ~0,3. Hacim ve getiri ölçüleri
bundan etkilenmiyor.

Daha küçük ve sistematik bir sapma da var: duyuru tutarı duyuru gününün
TL'si, payda son dönem sonunun TL'si. Aradaki 0–5 ayın enflasyonu (%0–12)
oranı her zaman biraz büyütüyor.

## 7. Hâlâ sınanmamış kör noktalar

- **Seyrek işlem ve beta.** Tek günlük piyasa modeli, az işlem gören
  hissede betayı aşağı çeker. Dimson gecikmeli terimi denenmedi.
- **Hayatta kalan yanlılığı.** Fiyat ve eşit ağırlıklı endeks, bugün işlem
  gören hisselerden kuruldu.
- **Manipülasyon doğrudan gözlenmiyor.** Devre kesici ve VBTS oynaklık
  ölçüyor. Kontrollü, tavan tavan yükselen bir tahta her gün devre kesici
  tetiklemeyebilir.
- **Devre kesici sayısı borsadaki hisse sayısıyla da artar.** Halka
  arzlarla büyüyen evrene göre normalize edilmedi.
- **Çoklu sınama.** Bu çalışma onlarca sınav koşuyor. Tek başına p < 0,05
  değil, tekrarlanma ve alt örneklem kararlılığı esas alınmalı. Bulgu 1 bu
  ölçütü rahatça geçiyor, Bulgu 12 zar zor.
- **Yayın evreni sonradan belirlendi.** Kapı kuralları (B4–B6, A7) 26.09
  denetiminde verinin kendisine bakılarak yazıldı. Etkisi küçük (23 karar).

## 8. Hüküm: bu veri genel bir çıkarım için yeterli mi?

**Bu dönemin içinde, ortalama etkiler için büyük ölçüde evet.** Hacim
artışı ve pozitif ortalama tepki; piyasa dalgasından, başka haberlerden,
sermaye işlemlerinden ve takvim kümelenmesinden arındırıldıktan sonra
sakin ve spekülatif aylarda, fon hisselerinde ve dışında, iki yılda da
duruyor.

**Aynı dönemin içinde, kesit ilişkileri ve alt gruplar için hayır.** Soru
"büyük haber daha çok hacim yaratıyor mu" ya da "tahta türü ilişkiyi
değiştiriyor mu" olduğunda örneklemin gücü yetmiyor. Bulgu 12, bu dönemin
fon ve manipülasyon dinamiğine bağlı görünüyor.

**Başka bir rejime genelleme için hayır.** Seçim öncesi negatif reel faiz
ve bireysel yatırımcı akını döneminden tek gözlem yok. O dönemde
bildirimlerin daha çok ya da daha az ilgi gördüğüne dair iki yöne de akla
yatkın mekanizmalar var. Veri yokken birini seçmek tahmin olur. **Bütün
bulgular "Eylül 2024 – Eylül 2026: yüksek reel faiz, bireysel katılımın
geri çekildiği, iki siyasi şok ve bir fon krizi içeren dönem" koşuluyla
okunmalı.**

## 9. Kaynaklar (web)

- **Politika faizi kronolojisi:**
  [Hibya, TCMB'nin 2019–2026 faiz kararları](https://hibya.com/tcmbnin-20192026-donemindeki-faiz-kararlari-kronolojik-olarak-degerlendirildi-991627),
  [TCMB PPK kararları](https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/PPK/PPK+Toplanti+Kararlari)
- **19 Mart 2025:**
  [CNBC-e](https://www.cnbce.com/borsa/borsa-istanbul-bist-100-endeksinde-son-durum-19-mart-2025-h10715),
  [Cumhuriyet](https://www.cumhuriyet.com.tr/ekonomi/imamogluna-gozalti-karari-sonrasi-borsalar-devre-kesti-islemler-2310851)
- **21 Mayıs 2026:**
  [Uzmanpara](https://uzmanpara.milliyet.com.tr/uzmanpara/borsa-neden-dustu-borsa-ne-kadardan-islem-goruyor-21-mayis-2026-bist-endeksi-7592125),
  [Haberler.com](https://www.haberler.com/haber/borsa-neden-dustu-21-mayis-2026-borsa-neden-19868769-haberi/)
- **Fon krizi ve soruşturma:**
  [KÜRE Ansiklopedi zaman çizelgesi](https://kureansiklopedi.com/tr/detay/2026-turkiye-sermaye-piyasasi-fon-krizi-ve-manipul),
  [Habertürk, SPK tasfiye kararı](https://www.haberturk.com/ekonomi/spkdan-7-portfoy-sirketinin-fonlarina-kapatma-karari-3913085),
  [Euronews, tasfiye süresi](https://tr.euronews.com/2026/09/21/sermaye-piyasasi-kurulu-fonlarin-tasfiye-surecini-6-aya-uzatti),
  [Sözcü, Başsavcılık müzekkeresi](https://www.sozcu.com.tr/iste-fon-sorusturmasini-baslatan-o-yazi-istanbul-cumhuriyet-bassavciligi-19-agustos-ta-spk-ya-gizli-p362255),
  [SPK rehber açıklaması](https://spk.gov.tr/duyurular/basin-duyurulari/2026/yatirim-fonlarina-iliskin-rehber-duzenleme-surecine-iliskin-aciklama)
- **Yatırımcı sayıları:**
  [BloombergHT, MKK 2025 sonu](https://www.bloomberght.com/mkk-yatirimci-sayisi-2025-sonunda-37-94-milyona-cikti-3766558),
  [Borsagündem, Eylül 2026](https://www.borsagundem.com.tr/pay-piyasasinda-yatirimci-sayisi-678-milyona-ulasti)
- **Yabancı işlem hacmi:**
  [Borsagündem, "Yabancının 29 yıllık yolculuğu"](https://www.borsagundem.com.tr/yabancinin-borsa-istanbulda-29-yillik-yolculugu)
- **2026 ilk yarı:**
  [Haberler.com](https://www.haberler.com/ekonomi/borsada-yilin-ilk-yarisinda-23-sektorden-21-i-20011283-haberi/),
  [Ekotürk](https://www.ekoturk.com/borsa/borsa-istanbulda-ilk-yari-bilancosu-21-sektor-yatirimcisina-kazandirdi/)

Web kaynakları haber ve ikincil derleme niteliğinde. Faiz kronolojisi,
TCMB'nin kendi kararlarıyla karşılaştırılarak kullanılmalı.

## 10. Karar bekleyenler

**K1 durumu (27.09 akşamı).**

- **Borsa İstanbul bültenleri:** tam (1.690 gün), hacim tablosu §2'de.
- **KAP listesi:** 2020-01 → 2020-10 arası indi (100 pencere). Sonra WAF
  IP'mizi geçici engelledi; `.env`'deki 500 ms fazla hızlıydı.
  - Betik artık en az 2 sn aralıkla çalışıyor ve üç ardışık hatada
    duruyor. Engel kalkınca kaldığı yerden devam edecek (347 pencere,
    ~25 dk).
  - Engel başka IP'lerden dolanılmayacak.
  - Resmî ve ücretsiz alternatif: MKK API Portalı'ndaki KAP veri yayın
    servisleri (hesabı Hüseyin açar).
- **İlk bulgu: şablon kullanımı zamanla değişmiş.**
  - "Yeni İş İlişkisi" konusuyla 2020'de ayda ~11 bildirim var,
    2023-09 → 2024-08'de ayda ~65–70.
  - 2020'de "Özel Durum Açıklaması (Genel)" ayda ~455 ve özetlerinin
    ~%7'sinde sözleşme, ihale ya da sipariş geçiyor.
  - Rejim karşılaştırması yalnız şablonla kurulursa rejim farkı ile
    duyuru alışkanlığı farkı karışır. Seçim öncesi örneklem, genel özel
    durum açıklamalarındaki sözleşme duyurularının sınıflanmasını da
    gerektirecek.
- **Bütçe:**
  - Şimdilik elde olan 898 şablonlu bildirim ~1,3 M girdi token,
    ~0,63 USD.
  - 2021–2023 geldikçe artacak.
  - Genel özel durum sınıflaması (senaryo B) kaba desenle +1.028
    bildirim, ~0,73 USD.
  - Kesin rakam KAP listesi tamamlanınca `rapor` ile.

**K1 · Rejim sınaması (önerilen).** 2020-01 → 2023-05 ve 2023-06 →
2024-08 için aynı sınavlar.

- **Bedava kısım:** Şunlar geriye uzatılır:
  - KAP liste ve detay arşivi (birkaç saatlik sıralı çekim)
  - yfinance fiyat ve hacmi
  - devre kesici kayıtları
  - Borsa İstanbul aylık işlem hacmi istatistikleri

  Böylece Bulgu 1, 2, 12, ortalama tepki ve Hüseyin'in hacim tespiti LLM
  olmadan sınanır.
- **Ücretli kısım:** Skora dayanan sınavlar eski bildirimlerin tutar
  çıkarımını istiyor. Bildirim başına ~0,0004 USD; önce bildirim sayısı
  çekilip kesin maliyet söylenir. 2023 öncesi raporlar TMS 29'suz, bu
  yüzden payda için TÜFE düzeltmesi şart.
- **Riskler:** Hayatta kalan yanlılığı altı yılda büyür. VBTS ve devre
  kesici sistemlerinin başlangıç tarihleri önce doğrulanmalı.

**K2 · 2024 paydası.** İki seçenek:

- **(a) Önerilen:** Katsayının çözülemediği ya da TMS 29 geçişiyle
  kirlendiği köprülerde resmî TÜİK TÜFE endeksini kullanmak. Dış veri, ama
  o gün yayınlanmış olduğu için point-in-time bozulmuyor. 235 bildirim
  ücretsiz yeniden skorlanır.
- **(b)** Sınır olarak yazmak.

**K3 · Metodoloji makalesi ve site metinleri.**

- Bulgu 2'nin başlığı ve yorumu düzeltilmeli ("sızıntı" yerine "önemli
  kısmı şirketin önceki açıklamalarıyla örtüşüyor").
- Bulgu 12'ye fon yoğunluğu ve üst üste binen pencere duyarlılığı
  eklenmeli.
- Örneklem dışı sınamanın aynı rejimde yapıldığı açıkça yazılmalı.
- §8 "Genellenebilirlik" başlığıyla sınırlar bölümüne girmeli.
- Tedbirli tahta kartındaki cümle ("fiyat hareketi bu haberle ilgili
  olmayabilir") bu bulguyla uyumlu, değişmesine gerek yok.
