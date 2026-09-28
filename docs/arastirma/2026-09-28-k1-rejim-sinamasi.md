# Yedi yıl, üç para rejimi: bulgular dönemin ürünü mü? (K1, 2026-09-28)

**Ön kayıt:** `2026-09-28-k1-on-kayit.md` (commit `e587b1b`, sonuçlardan
önce; iki veri sağlığı sapması `9d9262c`).
**Yeniden üretim:** `python scripts/analiz_k1_rejim.py --kaynak`. LLM yok,
ücret yok, veritabanına yazmıyor; `--kaynak` yalnız okur.

## Özet

2024–2026'da bulunan bulgular, aynı tanımlar ve aynı kodla 2020-01 →
2024-08 arasındaki iki para rejiminde yeniden ölçüldü. Toplam 3.091 olay,
210 pay, 1.690 işlem günü. Veri Borsa İstanbul'un resmî günlük
bültenlerinden alındı ve hayatta kalan yanlılığı taşımıyor.

- **Bildirim günü hacmi her rejimde artıyor.** Gevşek para (2020 – Mayıs
  2023) +%28,9 (t 6,4), sıkılaştırma +%22,0 (t 3,3), 2024–26 +%38,8
  (t 9,4). Pandemi, seçim öncesi ralli ve fon dönemi dahil yedi takvim
  yılının yedisinde pozitif.
- **Ortalama 3 günlük tepki pozitif, büyüklüğü rejime bağlı.** Gevşek
  parada +1,66 puan (t 4,9), 2024–26'dakinin iki katından fazla (fark
  z = −2,34). Sıkılaştırmada +0,85 puan, sonuçsuz (t 1,7).
- **"Bilgi sızıyor" yorumu yedi yılda da desteklenmiyor.** Şirketin önceki
  beş günde başka açıklaması olmayan 1.313 olayda ön hacim −%0,8 (t −0,3).
  2024–26'daki ön hacim artışı yalnız o döneme ait ve şirketin kendi önceki
  açıklamalarıyla açıklanıyor.
- **Oynak tahtada tepki her dönemde daha zayıf.** Tahtanın oynaklığında
  bir standart sapmalık artış tepkiyi gevşek parada −0,70, 2024–26'da −0,85
  puan düşürüyor. Yön genel. **Ortalama tepkinin eksiye dönmesi yalnız
  2024–26'da var** (oynak tahtada −0,75 puan, önceki dönemlerde +0,47 ile
  +0,49).
- **Bulgular fonların yoğun tuttuğu paylardan gelmiyor.** 2024–26'da
  sonradan tasfiye edilen fonların yoğun tuttuğu 10 pay çıkarılınca:
  - Hacim +%41,2 (t 9,2).
  - Tepki +0,69 puan (t 3,0).
  - Oynak tahta eğimi −0,21 (t −2,6).

  O 10 payda bildirimin hacim etkisi yarı yarıya düşük (+%20,2). Hacim
  orada ilginin temiz bir ölçüsü değil. Bu fon dinamiği yokken, 2020–24'te
  de aynı ana bulgular var.
- **Piyasa genelindeki hava da etkileri değiştirmiyor.** 81 ay piyasadaki
  limit-günü yoğunluğuna göre üçe bölündü. Sakin, orta ve spekülatif aylarda
  hacim ve tepki aynı, sürekli ölçüyle eğim sıfır (t −0,1). Bu,
  Hüseyin'in niş kağıt tezini değil, "piyasa çok hareketliydi" itirazını
  sınıyor.
- **Öz-denetim:** Önceki çalışmada dört fazla ya da eskimiş iddia bulundu
  ve düzeltildi (§7).

## 1. Soru ve neden şimdi

27.09 geçerlilik notu, bulguların "Eylül 2024 – Eylül 2026: yüksek reel
faiz, bireysel katılımın geri çekildiği, iki siyasi şok ve bir fon krizi
içeren dönem" koşuluyla okunması gerektiği sonucuna vardı. Sebep, başka bir
rejimden tek gözlem olmamasıydı.

Hüseyin'in itirazı iki dönemi özellikle ayırıyordu:

- Seçim öncesi negatif reel faizli ralli.
- Seçim sonrası, düşük dolaşımlı payların fonlarla yükseltildiği dönem.

Soru: KAP·RADAR'ın dayandığı etkiler bu dönemlerin birinin ürünü mü?

## 2. Veri ve yöntem

Ayrıntı ön kayıtta. Kısaca:

- **Olaylar:** KAP konusu "Yeni İş İlişkisi" olan bütün bildirimler, üç
  dönemde aynı seçim kuralıyla. (pay, t0) başına tekil.
- **Fiyat ve hacim:** Borsa İstanbul günlük pay piyasası bülteni. Resmî
  kapanış ve işlem gören pay adedi, borsadan çıkmış paylar dahil.
  855.631 pay-günü, 698 pay.
- **Ölçüler:** Tanımlar üretim kodundan içe aktarılıyor, kopyalanmıyor.
  - t0: `tepki.t0_bul`, seans kapanışı 18:10.
  - Anormal hacim (AV): ln(ort. adet [t0, t0+2]) − ln(medyan adet
    [t0−60, t0−11]).
  - CAR3: eşit ağırlıklı piyasaya karşı piyasa modeli. β 120 gün ve
    t0−10 tamponuyla, dönem içinde Vasicek küçültmesiyle.
  - V90: önceki 90 günde limite yakın (%9 ≤ |r| ≤ marj) gün sayısı.
- **Hacim birimi pay adedi.** TL hacmin tabanı olaydan ~1,7 ay önceye
  düşüyor. 2022'nin aylık %6'yı aşan enflasyonunda AV yalnız bu yüzden
  ~+0,10 büyürdü.
- **Çıkarım:** Standart hatalar pay ve ISO hafta düzeyinde iki yönlü
  kümeli (Cameron, Gelbach ve Miller 2011). MDE = 2,8 × SE (%80 güç,
  iki yönlü %5).
- **Dönemler:**

  | Dönem | Tarih aralığı | Olay | Pay |
  |---|---|---|---|
  | A · gevşek para | 2020-01 → 2023-05 | 1.000 | 123 |
  | A1 · pandemi ve bireysel akın | 2020–2021 | 367 | |
  | A2 · seçim öncesi ralli | 2022-01 → 2023-05 | 633 | |
  | B · sıkılaştırma | 2023-06 → 2024-08 | 850 | 123 |
  | C · bulguların dönemi | 2024-09 → 2026-09 | 1.241 | 144 |

- **Dışlanan olaylar:**
  - Sermaye işlemi (marjı aşan gün) yüzünden hacim sınavından 183 olay,
    CAR sınavından 11 olay çıktı.
  - 348 olayda beta tahmini yoktu, çoğu yeni halka arz. Bunlarda dönem
    çapası ve α = 0 kullanıldı, üretimdekiyle aynı.

**Veri sağlığı (sonuçlardan önce, ön kayda sapma olarak yazıldı).** Bülten
işlem görmeyen günde kapanışı 0 yazıyor. Borsa İstanbul'un günlük fiyat
marjı 13 Mart 2020'ye kadar ±%20'ydi. İkisi düzeltilmeden marjı aşan
pay-günü 9.122 görünüyordu. Düzeltmeden sonra yılda 71–124 kaldı ve %56'sı
%50'den büyük düşüş, yani bedelsiz ya da bölünme.

## 3. Kaynak doğrulaması: iki hat aynı şeyi ölçüyor mu?

C dönemi hem bu bülten hattıyla hem de sitenin kullandığı yfinance hattıyla
ölçüldü.

| | Bülten | Veritabanı (yfinance) |
|---|---|---|
| Eşleşen olay | 1.241 | 1.241 |
| t0 aynı | %99,0 | |
| CAR3 ortalaması (1.215 olay) | +0,72 puan | +0,73 puan |
| Olay bazında korelasyon | 0,996 | |
| AV | +%38,8 | +%38,1 (27.09 notu) |

İki bağımsız veri kaynağı, farklı piyasa endeksleri ve temettü düzeltmesi
farkına rağmen aynı sonucu veriyor. Bu hem sitenin yayınladığı tepki
sayılarının hem de A–B karşılaştırmasının kaynağa bağlı olmadığını
gösteriyor.

## 4. Sonuçlar: ön kayıttaki hipotezler

İki yönlü kümelenmiş t; parantezde MDE.

### H1 · Bildirim günü hacmi (Bulgu 1)

| Dönem | AV | Piyasaya göre AV | Hüküm |
|---|---|---|---|
| A | +%28,9 · t 6,43 (11,7) | +%34,3 · t 7,72 | **Tekrarlandı** |
| A1 | +%29,1 · t 3,65 | +%28,6 · t 3,84 | Tekrarlandı |
| A2 | +%28,7 · t 5,27 | +%37,3 · t 6,70 | Tekrarlandı |
| B | +%22,0 · t 3,28 (18,5) | +%23,2 · t 4,75 | **Tekrarlandı** |
| C | +%38,8 · t 9,39 | +%36,1 · t 9,02 | (referans) |

Olay penceresinde başka hiçbir KAP açıklaması olmayan sıkı alt kümede de
her dönemde duruyor: A +%29,2, B +%19,6, C +%32,6, hepsi t > 3.

Dönemler arası fark anlamlı değil: C−A z = +1,40, C−B z = +1,83.

### H2 · Ön hacim [t0−4, t0−1] (Bulgu 2)

| Dönem | Havuz | Önceki 5 günde açıklama yok | Hüküm (havuz) |
|---|---|---|---|
| A | +%2,8 · t 0,81 (9,9) | −%2,5 · t −0,51 | **Tekrarlanmadı** (MDE < C'deki etki) |
| B | +%2,9 · t 0,54 (15,8) | −%4,4 · t −0,78 | Güç yetmedi |
| C | +%10,8 · t 3,62 | +%2,7 · t 0,81 | (referans) |

- 2024–26'daki ön hacim artışı önceki rejimlerde yok.
- Temiz alt kümede üç dönemde de sıfır. Yedi yıl birlikte −%0,8 (t −0,3,
  n 1.313).
- 27.09'daki düzeltme ("çoğu şirketin kendi önceki açıklamaları") güçlendi:
  yedi yılın hiçbir döneminde sızıntıyı destekleyen bir iz yok.

### H3 · Ortalama 3 günlük tepki

| Dönem | CAR3 | Hüküm |
|---|---|---|
| A | +1,66 puan · t 4,86 (0,96) | **Tekrarlandı** |
| A1 | +1,27 · t 2,99 | Tekrarlandı |
| A2 | +1,88 · t 4,29 | Tekrarlandı |
| B | +0,85 · t 1,74 (1,36) | Yön aynı, güç yetmedi |
| C | +0,72 · t 3,32 | (referans) |

- Büyüklük rejime bağlı: A, C'nin iki katından büyük (z = −2,34).
- Uçlar %1'den kırpıldığında ortalamalar değişmiyor (A +1,67, B +0,89,
  C +0,75).
- Medyanlar daha küçük ama pozitif (A +0,64, B +0,17, C +0,34). Pozitif
  olay payı %52–56. Dağılım sağa çarpık. Ortalamayı tek tük uç olaylar
  değil, geniş bir sağ kuyruk taşıyor.

### H4 · Oynak tahta (Bulgu 12)

CAR3 ~ V90, limit günü başına puan:

| Dönem | Eğim | V90 ort. (SS) | 1 SS'lik etki | V90 ≥ 8 / V90 ≤ 1 ortalama CAR3 |
|---|---|---|---|---|
| A | −0,08 · t −2,64 (0,09) | 7,9 (8,5) | −0,70 | +0,49 / +1,71 |
| A1 | −0,07 · t −1,17 | 7,6 (8,7) | −0,64 | −0,13 / +1,32 |
| A2 | −0,09 · t −2,31 | 8,0 (8,4) | −0,74 | +0,79 / +1,95 |
| B | −0,06 · t −1,43 (0,12) | 7,4 (6,8) | −0,40 | +0,47 / +0,82 |
| C | −0,24 · t −3,29 | 3,1 (3,5) | −0,85 | **−0,75** / +1,63 |

Hüküm:

- **A tekrarlandı.** B'de etki daha küçük (MDE C'deki etkiden küçük).
- **Gün başına eğim C'de üç kat dik** (C−A z = −2,01, C−B z = −2,16).
  Ama C'de oynaklık dağılımı sıkışmış: ortalama 3 limit günü, önceki
  rejimlerde 7–8. Bir standart sapmalık oynaklığın etkisi A ve C'de
  benzer (−0,70 / −0,85).
- **Genel olan:** Oynak tahtada tepki daha zayıf.
- **C'ye özgü olan:** Oynak tahtada ortalamanın eksiye dönmesi.

27.09'daki "fonların yoğun tuttuğu hisselerde toplanıyor" gözlemi bu
ikinci kısımla uyumlu. 2020–24 için fon portföy verisi olmadığından fon
etkileşimi sınanamadı.

### H5 · Karışan açıklamalar

Olay penceresinde ([t0−1, t0+2]) aynı payın başka bir KAP açıklaması
olmayan sıkı alt küme:

| Dönem | AV | CAR3 |
|---|---|---|
| A | +%29,2 · t 5,72 | **+1,12 · t 3,45** |
| A1 | +%33,7 · t 4,02 | +0,67 · t 1,25 (1,51) |
| A2 | +%26,2 · t 3,98 | +1,45 · t 3,74 |
| B | +%19,6 · t 3,17 | +0,69 · t 1,45 (1,34) |
| C | +%32,6 · t 8,12 | **+0,43 · t 1,70 (0,70)** |
| Yedi yıl | | +0,71 · t 3,77 |

- H1 bütün dönemlerde ayakta.
- H3 temiz alt kümede A'da ayakta, B ve C'de sonuçsuz. Yedi yıl birlikte
  ayakta.
- **C'deki sonuç 27.09 notunun bir iddiasını düzeltiyor** (§7).

Temiz alt kümede tepkinin küçülmesinin sebebi keşif 4'te: pencerede aynı
şirketin başka bir yeni iş duyurusu olan olayların CAR3'ü her dönemde 2–3
kat büyük (A +3,06, C +1,54 puan). Bunun büyük kısmı mekanik: iki
duyurunun tepkisi aynı 3 günlük pencereye düşüyor. Finansal rapor,
sermaye işlemi gibi diğer türler tepkiyi sistematik olarak büyütmüyor.

## 5. Keşif (hipotez değil, betimleme)

### Yıllara göre

| Yıl | Olay | Ayda | AV | t | CAR3 | t | V90 ort. |
|---|---|---|---|---|---|---|---|
| 2020 | 139 | 11,6 | +%46,5 | 4,86 | +0,50 | 0,53 | 7,9 |
| 2021 | 228 | 19,0 | +%19,8 | 1,92 | +1,73 | 5,45 | 7,4 |
| 2022 | 368 | 30,7 | +%32,6 | 4,94 | +2,19 | 3,29 | 5,5 |
| 2023 | 649 | 54,1 | +%15,3 | 1,88 | +0,91 | 1,62 | 10,1 |
| 2024 | 690 | 57,5 | +%30,8 | 5,23 | +0,91 | 2,53 | 5,0 |
| 2025 | 641 | 53,4 | +%42,6 | 7,18 | +0,70 | 2,36 | 2,6 |
| 2026 | 376 | 41,8 | +%38,5 | 5,79 | +0,86 | 1,75 | 3,9 |

- Hacim etkisi yedi yılın yedisinde pozitif, beşinde t > 1,96.
- En zayıf iki yıl 2021 ve 2023. İkisi de bireysel spekülasyonun yoğun
  olduğu yıllar (2021 yatırımcı akını; 2023 bedelsiz ve halka arz dalgası,
  V90 en yüksek).
- Ama aynı sonuç ay düzeyinde tutmuyor (aşağıda). Bu yüzden yıllık desen
  bir kanıt değil, not edilen bir gözlem.

### Fonlarla yükseltilen niş kağıtlar (yalnız C)

Hüseyin'in "spekülasyon"dan kastı piyasanın genel havası ya da içeriden
bilgi değil. Kastı, düşük dolaşımlı belirli kağıtların fonlarca
yükseltilmesi: [ad], [ad], [ad], [ad]. Sınıf 27.09 notuyla aynı:
tasfiye edilen fonların Ağustos 2026 pozisyonu, payın günlük işlem
hacmine oranla. Portföy olaydan sonra ölçüldüğü için sınıf betimleyici.
2020–24 için fon portföy verisi yok, bu kırılım yalnız C'de.

Yoğun grup (pozisyon ≥ 0,5 günlük hacim) 10 pay ve 132 olay: OZATD 29,
ODINE 23, GESAN 23, ALTNY 22, EUPWR 12, BOBET 11, ALKLC 6, ESCAR 5,
ANELE 1, TEHOL 1. DSTKF ve KTLEV'in "Yeni İş İlişkisi" bildirimi yok.

| C, fon sınıfı | AV | CAR3 | CAR3 ~ V90 |
|---|---|---|---|
| Fon tutmuyor (77 pay) | +%40,9 · t 7,94 | +0,50 · t 1,65 | −0,19 · t −1,40 |
| Tutuyor, < 0,5 gün (50 pay) | +%41,5 · t 6,51 | +0,83 · t 2,50 | −0,23 · t −2,45 |
| **Yoğun, ≥ 0,5 gün (10 pay)** | **+%20,2** · t 3,10 | +0,96 · t 2,41 | −0,36 · t −2,01 |
| **C, yoğun grup hariç** | **+%41,2 · t 9,16** | **+0,69 · t 2,95** | **−0,21 · t −2,63** |

Okuma:

- **Pompalanan kağıtlarda bildirim daha az hacim yaratıyor.** Etki
  yarıya yakın. Tabanı fon akışı şişirdiğinde bildirim göze daha az
  çarpıyor. Hacim bu tahtalarda ilginin temiz bir ölçüsü değil.
- **Bulgular bu kağıtlardan gelmiyor.** Onlar çıkarılınca C'deki üç
  sonuç da duruyor.
- **Oynak tahta etkisi fon yoğunluğuyla büyüyor** (−0,19 → −0,23 → −0,36).
  27.09'daki gözlem tekrarlandı. Ama fonsuz paylarda da işaret aynı. A
  döneminde bu fonlar yokken de eğim negatif ve anlamlı (§4 H4).
  Fonlar bu etkiyi büyütüyor, ama tek başına yaratmıyor.

### Piyasa genelinde hava (Hüseyin'in tezinden ayrı bir itiraz)

81 ay, limite yakın pay-günü payına göre tercillere ayrıldı (sınırlar
%4,02 ve %6,46). Spekülatif ayların 9'u 2020, 5'i 2021, 7'si 2023'te.
2025–26'da yalnız 3 ay.

| Ay türü | AV | Piyasaya göre AV | CAR3 |
|---|---|---|---|
| Sakin (27 ay) | +%27,1 · t 8,33 | +%36,7 · t 10,63 | +1,07 · t 4,38 |
| Orta (27 ay) | +%36,5 · t 7,33 | +%30,4 · t 6,94 | +0,97 · t 4,27 |
| Spekülatif (27 ay) | +%27,4 · t 4,27 | +%28,0 · t 6,10 | +1,16 · t 2,35 |

Olay ayının limit-günü payına sürekli regresyonda AV eğimi −0,001
(t −0,12), CAR3 eğimi −0,012 puan (t −0,14). Etkiyi piyasanın genel
havası değil, hissenin kendi tahtası değiştiriyor (H4).

### Aynı şirketler

Üç dönemin üçünde de olayı olan 57 pay ile bileşim sabit tutuldu:

| Dönem | AV | CAR3 |
|---|---|---|
| A | +%25,5 · t 5,33 | +1,77 · t 4,49 |
| B | +%18,4 · t 2,34 | +0,29 · t 0,53 |
| C | +%44,0 · t 7,72 | +1,04 · t 3,45 |

Desen tam örneklemle aynı. Dönem farkları, hangi şirketlerin şablonu
kullandığındaki değişimden gelmiyor.

## 6. Hüseyin'in tespitleri, veriyle

| Tespit | Veri | Hüküm |
|---|---|---|
| "Bu koşullarda (yüksek faiz, spekülasyon, fonlar) yapılan ölçümler arınmış sayılmaz" | Hacim etkisi üç rejimde de var. Ortalama tepki gevşek parada daha da büyük. Piyasa çapı spekülasyon etkileri değiştirmiyor. | **Ana bulgular için hayır:** dönemin ürünü değiller. Bir alt bulgu için evet: oynak tahtada eksi ortalama tepki yalnız 2024–26'da. |
| "Seçim öncesi ralli farklı bir piyasaydı" | A2'de ortalama tepki +1,88 puan, C'nin 2,6 katı. Hacim etkisi benzer. | **Doğru.** Rallide duyurular fiyatta daha çok karşılık buldu. Mekanizma (iyimserlik, bireysel talep) bu veriyle ayrışmıyor. |
| "Seçim sonrası dönemde paylar fonlarla yükseltildi; ölçümler bundan etkilenir." Kastı içeriden bilgi değil, fon yoğunluğu. | Fonların yoğun tuttuğu 10 payda bildirimin hacim etkisi yarıya yakın düşük (+%20,2 / +%41). Oynak tahta etkisi fon yoğunluğuyla büyüyor. Oynak tahtada tepkinin eksiye dönmesi yalnız C'de. Ama o 10 pay çıkarılınca C'nin üç bulgusu da duruyor. 2020–24'te, bu fon dinamiği yokken, ana bulgular var. | **Doğru, etkisi sınırlı.** Fonların yoğun tuttuğu paylar ölçüyü yerel olarak bozuyor: hacim orada ilgiyi ölçmüyor, oynak tahta etkisi büyüyor. Ama bulguları onlar üretmiyor. |
| (ayrı itiraz) "Piyasa genel olarak çok hareketliydi" | Piyasa çapında limit-günü yoğunluğu tercillerinde hacim ve tepki aynı. Bu ölçüyle en hareketli aylar 2020, 2021 ve 2023'te. | **Etkisi yok.** Bu ölçü pay tezini sınamıyor: fonun kontrollü yükselttiği bir kağıt piyasa geneline limit günü olarak yansımaz. |

## 7. Öz-denetim: önceki çalışmada bulunan hatalar

1. **27.09 notunun özeti CAR3 için sınanmamış bir arındırmayı sınanmış
   gibi yazıyordu.** "Bu iki sonuç ... aynı pencerede yapılan başka
   açıklamalar ... arındırıldıktan sonra ayakta kalıyor" cümlesindeki
   ikinci sonuç ortalama CAR3'tü. Ama o notun tablosunda sıkı temiz
   satırının CAR3 hücresi boştu ("—"): sınav koşulmamıştı.
   - Şimdi koşuldu. C'de +0,43 puan, t 1,70, sonuçsuz. Yedi yıl birlikte
     +0,71, t 3,77.
   - Aynı ifade metodoloji makalesinin Sınırlar bölümüne de girmişti.
     İkisi düzeltildi.
2. **Makale IV'te "tekrarlananlar ... bilgi resmî açıklamadan önce hareket
   ediyor" diyordu.** Bu cümle 27.09 düzeltmesinden sonra da kalmıştı ve
   K1 ile çelişiyor. Düzeltildi.
3. **Bulgu 12 için 27.09'da yazılan "oynak tahtaların genel bir özelliği
   olarak okunmamalı" cümlesi ters yönde fazla.** Oynak tahtada daha zayıf
   tepki gevşek parada da var ve anlamlı. Genel olmayan kısım eksi
   ortalama.
4. **Makalenin yeniden üretilebilirlik bölümündeki veri sayıları ilk
   sürümden kalmıştı:** 613 bildirim, 111 hisse. Güncellendi.

Bu dördü de sayı hatası değil, cümlenin tablodan önde gitmesi. Ölçümler
doğru. Kaynak doğrulaması (§3) sitenin yayınladığı tepki sayılarını
bağımsız bir veriyle teyit etti.

## 8. Sınırlar

- **Seçim yalnız şablonla.** 2020'de ayda 11,6, 2024'te 57,5 şablonlu
  bildirim var. Eski yıllarda yeni işlerin bir kısmı "Özel Durum
  Açıklaması (Genel)" ile duyuruldu.
  - Aynı 57 şirketle bileşim kontrolü (§5) deseni değiştirmedi.
  - Ama şablonu kullanmayan şirketlerin duyurularının etkisi bilinmiyor.
  - ÖDA Genel özetlerinde sözleşme/ihale geçen ~2.600 bildirim ayrı bir
    kol olarak sınıflanabilir.
- **Skora dayanan sınavlar yok.** 2020–24 bildirimlerinden tutar
  çıkarılmadı (Gemini, ~1,43 USD, onay bekliyor). Bu yüzden Bulgu 3, 4, 5
  ve 11 bu turda sınanmadı. "Büyük haber daha çok fiyatlanıyor mu"
  sorusu hâlâ tek rejimli.
- **Oynaklık için vekil kullanıldı.** Devre kesici ve VBTS kayıtlarının
  2020 başlangıç tarihleri doğrulanmadı. Bütün dönemlerde limite yakın gün
  sayısı kullanıldı. C'de bu vekil 27.09'daki gerçek kayıtlı sonuca yakın
  (−0,24, t −3,29 / −0,20, t −3,1).
- **Temettü düzeltmesi yok.** Etkisi kaynak karşılaştırmasında ölçüldü:
  C'de ortalama fark 0,01 puan.
- **Çoklu sınama.** Bu notta 25 ana, onlarca keşif sınavı var. Hüküm tek
  p değerinden değil, dönemler boyunca tekrarlanmadan verildi. H1 ve H2'nin
  temiz kısmı bu ölçütü rahat geçiyor; H4'ün A dışındaki alt dönemleri
  geçmiyor.
- **Nedensellik yok.** Olay çalışması bildirimin çevresindeki ortalama
  hareketi ölçer. Rejimler arasındaki fark, rejimin kendisinden başka
  sebeplerden de gelebilir (katılımcı bileşimi, halka arz dalgası, bedelsiz
  modası).

## 9. Ürün için ne anlama geliyor

- **Site metinlerinde değişiklik gerekmiyor**, metodoloji makalesi dışında.
  - Tedbirli ve oynak tahta uyarısı ("fiyat hareketi bu haberle ilgili
    olmayabilir") artık yedi yıllık veriyle destekleniyor: oynak tahtada
    tepki her rejimde daha zayıf.
  - Tepki panelinin ortalamaları iki yıllık. Rejim farkı (gevşek parada
    iki kat) paneli okuyan için bir bağlam cümlesi olarak makalede duruyor.
- **Önerilmeyen:** Seri duyuru (birkaç gün içinde birden çok yeni iş)
  bayrağı. Büyük tepkinin çoğu pencere çakışmasından geliyor. Yeni bir
  bilgi değil.
- **Değer katacak tek genişleme ücretli:** 2020–24 bildirimlerinden tutar
  çıkarımı (~1,43 USD). Bununla hem skorun tepkiyle ilişkisi (Bulgu 3/11)
  üç rejimde sınanır, hem de tepki panelinin akran grupları iki yıllık
  değil yedi yıllık örneklemden kurulur (hücre başına ~2,5 kat gözlem).
  Hüseyin'in onayına bağlı.
