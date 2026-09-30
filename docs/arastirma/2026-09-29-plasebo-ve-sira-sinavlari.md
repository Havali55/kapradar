# Olay yokken ölçü ne diyor? Plasebo, sıra ve standardize sınavlar (D1-P, 2026-09-29)

**Ön kayıt:** `2026-09-29-arastirma-haritasi.md` §6 "D1-P" (commit
`df9a7f8`, sonuçlardan önce). Hat ve dönemler K1'den
(`2026-09-28-k1-on-kayit.md`, `2026-09-28-k1-rejim-sinamasi.md`).
**Yeniden üretim:** `python scripts/analiz_plasebo.py`. LLM yok, ücret yok,
ağa çıkmıyor, veritabanına yazmıyor. Süre 7,3 dakika (ön kayıtlı kısım
4,5 dakika). Kat 10 korundu; 30 dakika sınırına yaklaşılmadı.

## Özet

K1'in ölçüm aleti, aynı paylarda rastgele seçilen 20.354 "olaysız" günde
çalıştırıldı. Sahte olaylar gerçeklerle aynı koddan geçti. Ortalama tepki
ayrıca çarpıklığa dayanıklı dört sınavla yeniden sınandı.

- **Hat tuttu.** K1'in bütün olay rakamları birebir çıktı (olay başına fark
  < 10⁻¹⁵).
- **Olay yokken hacim ölçüsü sıfıra yakın.** Rastgele günlerde AV A +%1,2,
  B +%1,1, C +%3,6; hiçbiri anlamlı değil. Yedi yıl +%2,2 (t 1,03).
  - Haritanın AS2 tahmini (+0,08 … +0,14) gerçekleşmedi. Ortalamanın logu
    ile logların ortalaması arasındaki fark gerçekten var: +0,05 … +0,08
    log.
  - Ama olaysız bir günün log hacmi tabanın ortalama %4 altında. İki sapma
    birbirini büyük ölçüde götürüyor.
  - **Tek istisna A1 (2020–21): +%11,3 (t 2,55).** P1 tetiklendi.
- **Net hacim etkisi her dönemde duruyor.** Gerçek − plasebo: A +%27,4
  (t 6,15), B +%20,8 (t 3,83), C +%33,9 (t 7,78). A1 dahil H1'in bütün
  hükümleri aynı kaldı.
- **Olay yokken CAR3 her dönemde sıfır** (|t| < 0,9). Net: A +1,64 puan
  (t 4,30), B +0,76 (t 1,51, güç yetmedi), C +0,68 (t 2,98). H3'ün
  hükümleri aynı. A ile C arasındaki fark nete göre de duruyor
  (z −2,34 → −2,17).
- **Ön hacim olay yokken sıfır değil (P5).** Günlük log ölçüsü rastgele
  günlerde tabanın %3–5 altında.
  - K1'in "temiz olaylarda ön hacim sıfır" sonucu tabana göreydi.
    Rastgele günlere göre yedi yıl +%4,9 (t 2,06), C +%10,5 (t 2,79).
  - "Sızıntı izi yok" cümlesi C için zayıflıyor. Bir dışlama asimetrisi
    bunu kısmen açıklayabilir (§5); ölçülmedi.
- **Sıra ve standardize sınavlar hiçbir hükmü zayıflatmıyor.** Birincil
  sınav KP-BMP: A 5,53, A1 2,50, A2 4,91, C 5,19. B'nin "sonuçsuz" hükmü
  asimetri kuralı gereği yükseltilmedi (KP-BMP 2,36).
  - Ama bu sınavlar plasebo altında da C'de "anlamlı" çıkıyor (KP-BMP
    +2,09). Destekleri zayıf kanıt.
- **Beklenmedik iki şey:**
  - Betası tahmin edilemeyen (çoğu yeni halka arz) olaylarda rastgele
    günlerde de CAR3 +1,93 puan (t 3,64).
  - Sık bildirim yapan paylarda 10 kat için gün yetmedi. Etkin kat 6,6.

## 1. Veri ve yöntem

**Hat.** Olaylar, panel, getiri ve hacim serileri `analiz_k1_rejim`'den
içe aktarıldı. Hacim profili, piyasa hacmi ve karışan açıklama
`analiz_gecerlilik`'ten, beta ve Vasicek `tepki`'den geliyor. 3.091 gerçek
olay, 210 pay, 1.690 işlem günü. Dönemler K1'deki gibi: A, A1, A2, B, C ve
yedi yıl (7Y).

**Plasebo.**

- Gerçek olayı olan her (pay, A/B/C) çifti için, gerçek olay sayısının 10
  katı rastgele işlem günü. Tohum 20260929. Seçim iadesiz.
- Aday gün:
  - dönem içinde ve payın bültende satırı olan (listelenmiş) gün,
  - payın herhangi bir "Yeni İş İlişkisi" bildiriminin t0'ına 10 işlem
    gününden yakın değil,
  - dışlama penceresi arşivin içinde (t0+10 ≤ liste arşivinin son günü,
    2026-09-19).
- Sahte olayın t0'ı seçilen gün, dönemi o günün dönemi.
- **P-geniş:** bütün sahte olaylar. **P-temiz:** ayrıca K1'in `olay_temiz`
  tanımı ([t0−1, t0+2]'de açıklama yok; bkz. Sapma 2).

**Ölçüler (gerçek ve sahte olayda aynı kod):**

- AV = ln(ort. adet [t0, t0+2]) − ln(medyan adet [t0−60, t0−11]).
- Piyasaya göre AV: AV − piyasanın aynı ölçüsü.
- Ön hacim: k = −4 … −1 için ln adet(t0+k) − taban, ortalaması.
- AV_log = ort_k [ln adet(t0+k)] − taban, k = 0, 1, 2. Sıfır adetli gün
  AV'deki gibi düşer.
- CAR3 = Σ k=0..2 [r − α − β·r_m].
  - β: 120 gün, t0−10 tamponu, yetmezse 250 gün.
  - Tahminden dışlanan günler, payın **gerçek** olay pencereleri.
  - β dönem içinde Vasicek ile küçültülür. Sahte olaylarda havuz, o
    dönemin sahte olayları.
  - Betası olmayan olay: dönem çapası ve α = 0.
- Sermaye işlemi dışlaması K1'deki gibi: hacim için [t0−60, t0+2], CAR
  için [t0, t0+2] içinde marjı aşan gün.

K1'in `car3` fonksiyonu dışlamayı kendi girdisinden kuruyor. Bu yüzden
sahte olaylarla doğrudan çağrılamadı. Aynı akış, dışlama parametre olacak
biçimde `car3_dislamali` olarak yazıldı. Gerçek olaylarda `k1.car3` ile
farkı sıfır (hat kontrolünde sınanıyor).

**Sınav.** Gerçek ve sahte olaylar tek tabloda:
ölçü = a + b · 1[gerçek olay]. b net etki (gerçek − plasebo). Standart
hata pay ve ISO hafta düzeyinde iki yönlü kümeli (`ols_kumeli`). Plasebo
ortalaması da aynı kümelemeyle (`k1.ortalama`). MDE = 2,8 × SE.

Eşleştirme:

- H1 ve H3 neti: bütün gerçek olaylar − P-geniş.
- H5 neti: temiz gerçek olaylar − P-temiz.
- K1 kurallarında "C'deki etki" yerine C'nin **net** etkisi kullanıldı.

## 2. Hat kontrolü

| Dönem | AV | CAR3 | K1 notu | |
|---|---|---|---|---|
| A | +%28,9 · t 6,43 (n 806) | +1,66 · t 4,86 (n 964) | +%28,9 · 6,43 / +1,66 · 4,86 | tutuyor |
| A1 | +%29,1 · t 3,65 | +1,27 · t 2,99 | aynı | tutuyor |
| A2 | +%28,7 · t 5,27 | +1,88 · t 4,29 | aynı | tutuyor |
| B | +%22,0 · t 3,28 (n 755) | +0,85 · t 1,74 (n 843) | aynı | tutuyor |
| C | +%38,8 · t 9,39 (n 1.119) | +0,72 · t 3,32 (n 1.220) | aynı | tutuyor |

- Olay düzeyinde `data/ham_rejim/k1_olaylar.csv` ile de karşılaştırıldı.
  3.091 olayın 3.091'i aynı sırada. AV, piyasaya göre AV, ön hacim, CAR3
  ve β'da en büyük fark 10⁻¹⁵ mertebesinde. Eksik değerler aynı yerde.
- `car3_dislamali` ile `k1.car3`: 3.027 olay, CAR3 ve β farkı 0, beta
  kaynağı aynı.
- K1'in dönem farkları da çıktı: AV C−A z +1,40, C−B +1,83; CAR3 C−A
  −2,34.

## 3. Plasebo sonuçları

**Örneklem.**

| | Gerçek | P-geniş |
|---|---|---|
| Olay | 3.091 | 20.354 (hedef 30.910) |
| AV'li | 2.680 | 18.446 |
| CAR3'lü | 3.027 | 20.221 |
| Sermaye işlemi (hacim / CAR) | 183 / 11 | 1.092 / 52 |
| Çapa betalı | 348 (%11,5) | 1.651 (%8,2) |
| `olay_temiz` | %58,4 | %79,6 |

A 6.679, B 5.020, C 8.655 sahte olay. P-temiz 16.211.

### AV

İki yönlü kümeli t; parantezde netin MDE'si.

| Dönem | Gerçek | P-geniş | Net | P-temiz | Temiz net (H5) |
|---|---|---|---|---|---|
| A | +%28,9 · t 6,43 | +%1,2 · t 0,36 | +%27,4 · t 6,15 (11,6) | +%0,6 · t 0,19 | +%28,4 · t 6,66 |
| A1 | +%29,1 · t 3,65 | **+%11,3 · t 2,55** | +%16,1 · t 2,53 (17,9) | **+%10,6 · t 2,26** | +%20,9 · t 3,35 |
| A2 | +%28,7 · t 5,27 | −%5,0 · t −1,16 | +%35,6 · t 5,61 (16,4) | −%6,0 · t −1,34 | +%34,3 · t 4,93 |
| B | +%22,0 · t 3,28 | +%1,1 · t 0,20 | +%20,8 · t 3,83 (14,8) | +%0,7 · t 0,13 | +%18,8 · t 4,01 |
| C | +%38,8 · t 9,39 | +%3,6 · t 1,13 | +%33,9 · t 7,78 (11,1) | +%0,5 · t 0,15 | +%32,0 · t 7,24 |
| 7Y | +%30,9 · t 9,45 | +%2,2 · t 1,03 | +%28,1 · t 8,62 (8,4) | +%0,6 · t 0,27 | +%27,2 · t 9,11 |

### Piyasaya göre AV

| Dönem | Gerçek | P-geniş | Net |
|---|---|---|---|
| A | +%34,3 · t 7,72 | +%3,3 · t 1,50 | +%30,0 · t 6,43 (12,1) |
| A1 | +%28,6 · t 3,84 | **+%8,2 · t 2,61** | +%18,8 · t 2,74 (19,3) |
| A2 | +%37,3 · t 6,70 | +%0,1 · t 0,05 | +%37,1 · t 5,99 (15,9) |
| B | +%23,2 · t 4,75 | +%0,9 · t 0,34 | +%22,1 · t 4,02 (14,9) |
| C | +%36,1 · t 9,02 | +%2,5 · t 1,35 | +%32,7 · t 7,71 (10,8) |
| 7Y | +%31,8 · t 11,10 | **+%2,4 · t 2,01** | +%28,7 · t 9,11 (8,1) |

### AV_log (ikincil, P4: yalnız rapor)

Son sütun plasebo örnekleminde AV − AV_log, log birimi. Yani ortalamanın
logu ile logların ortalaması arasındaki fark: AS2'nin konusu.

| Dönem | Gerçek | P-geniş | Net | AV − AV_log |
|---|---|---|---|---|
| A | +%19,2 · t 4,74 | −%5,3 · t −1,67 | +%25,9 · t 6,18 | 0,066 |
| A1 | +%17,5 · t 2,34 | +%3,1 · t 0,73 | +%14,0 · t 2,30 | 0,077 |
| A2 | +%20,1 · t 3,99 | **−%10,5 · t −2,47** | +%34,2 · t 5,58 | 0,060 |
| B | +%15,6 · t 2,44 | −%3,9 · t −0,76 | +%20,2 · t 3,89 | 0,051 |
| C | +%29,0 · t 7,69 | −%2,3 · t −0,75 | +%32,0 · t 7,96 | 0,059 |
| 7Y | +%22,1 · t 7,54 | −%3,7 · t −1,78 | +%26,8 · t 8,91 | 0,059 |

- AS2'nin mekanizması var: fark +0,05 … +0,08 log. Tahmin aralığının
  (+0,08 … +0,14) altında. Günler arası korelasyon bekleneni küçültüyor.
- Ama olaysız günün log hacmi tabanın altında (AV_log plasebosu −%2 … −%11,
  A1 hariç). Günlük log hacim sola çarpık: ortalaması medyanının altında.
- Sonuç: AV'nin plasebosu iki sapmanın toplamı ve sıfıra yakın. Net
  etkiler AV ve AV_log'da neredeyse aynı (C +%33,9 / +%32,0).

### Ön hacim [t0−4, t0−1] (P5)

| Dönem | Havuz: gerçek | P-geniş | Net | Önceki 5 gün temiz: gerçek | P-geniş | Net |
|---|---|---|---|---|---|---|
| A | +%2,8 · t 0,81 | −%3,4 · t −1,16 | +%6,4 · t 2,01 | −%2,5 · t −0,51 | −%4,2 · t −1,37 | +%1,8 · t 0,43 |
| A1 | −%0,2 · t −0,03 | +%3,7 · t 0,94 | −%3,7 · t −0,68 | +%4,0 · t 0,52 | +%4,2 · t 0,98 | −%0,2 · t −0,03 |
| A2 | +%4,3 · t 1,05 | **−%7,9 · t −2,00** | +%13,3 · t 2,78 | −%6,6 · t −1,09 | **−%10,1 · t −2,42** | +%3,9 · t 0,66 |
| B | +%2,9 · t 0,54 | −%3,2 · t −0,64 | +%6,2 · t 1,56 | −%4,4 · t −0,78 | −%4,3 · t −0,82 | −%0,1 · t −0,04 |
| C | +%10,8 · t 3,62 | −%2,3 · t −0,78 | +%13,4 · t 4,30 | +%2,7 · t 0,81 | **−%7,0 · t −2,32** | **+%10,5 · t 2,79** (10,5) |
| 7Y | +%6,1 · t 2,77 | −%2,8 · t −1,46 | +%9,2 · t 4,53 | −%0,8 · t −0,29 | **−%5,4 · t −2,62** | **+%4,9 · t 2,06** (6,8) |

"Önceki 5 gün temiz" kolonlarının gerçek ve net satırları sonuçlar
görüldükten sonra eklendi (Sapma 13). P-geniş kolonu ön kayıtlı koşudan.

### CAR3

| Dönem | Gerçek | P-geniş | Net | P-temiz | Temiz net (H5) |
|---|---|---|---|---|---|
| A | +1,66 · t 4,86 | +0,03 · t 0,17 | +1,64 · t 4,30 (1,07) | +0,11 · t 0,74 | +1,01 · t 2,90 (0,97) |
| A1 | +1,27 · t 2,99 | −0,14 · t −0,86 | +1,41 · t 2,81 (1,41) | −0,00 · t −0,01 | +0,67 · t 1,21 (1,56) |
| A2 | +1,88 · t 4,29 | +0,14 · t 0,63 | +1,74 · t 3,73 (1,31) | +0,20 · t 0,82 | +1,25 · t 2,89 (1,21) |
| B | +0,85 · t 1,74 | +0,09 · t 0,44 | +0,76 · t 1,51 (1,41) | +0,15 · t 0,72 | +0,54 · t 1,09 (1,39) |
| C | +0,72 · t 3,32 | +0,04 · t 0,34 | +0,68 · t 2,98 (0,64) | −0,01 · t −0,04 | +0,43 · t 1,57 (0,77) |
| 7Y | +1,05 · t 5,26 | +0,05 · t 0,58 | +1,01 · t 4,72 (0,60) | +0,07 · t 0,82 | +0,64 · t 3,12 (0,57) |

Puan cinsinden. Plasebo hiçbir dönemde sıfırdan ayrılmıyor.

## 4. P1–P5 hükümleri

### P1 · AV

Plasebo AV'si |t| ≥ 1,96 olan yer: **A1** (AV +%11,3 · t 2,55; piyasaya
göre +%8,2 · t 2,61) ve **7Y piyasaya göre AV** (+%2,4 · t 2,01). A, A2,
B ve C'de tetiklenmedi. H1, kural gereği her dönemde nete göre yeniden
verildi:

| Dönem | K1 hükmü | Net AV | Net piyasaya göre | Yeni hüküm |
|---|---|---|---|---|
| A | Tekrarlandı | +%27,4 · t 6,15 | +%30,0 · t 6,43 | **Tekrarlandı** |
| A1 | Tekrarlandı | +%16,1 · t 2,53 | +%18,8 · t 2,74 | **Tekrarlandı** (P1 tetiklendi; net yazılır) |
| A2 | Tekrarlandı | +%35,6 · t 5,61 | +%37,1 · t 5,99 | **Tekrarlandı** |
| B | Tekrarlandı | +%20,8 · t 3,83 | +%22,1 · t 4,02 | **Tekrarlandı** |
| C | (referans) | +%33,9 · t 7,78 | +%32,7 · t 7,71 | Ayakta |
| 7Y | — | +%28,1 · t 8,62 | +%28,7 · t 9,11 | Ayakta |

H5 temiz alt kümede de AV her dönemde ayakta (temiz net en küçük B
+%18,8 · t 4,01).

A1'deki plasebo sapması 2020–21'e ait. Olaylı payların hacmi, bu dönemde
piyasanın medyan payından hızlı büyüdü: olaysız gün de 60 gün önceki
tabanın üstünde. Sebep ölçülmedi.

### P2 · Dönem farkları

| Ölçü | K1 (ham) C−A | Net C−A | K1 (ham) C−B | Net C−B |
|---|---|---|---|---|
| AV | +1,40 | +0,93 | +1,83 | +1,67 |
| AV, piyasaya göre | +0,26 | +0,37 | +1,78 | +1,35 |
| CAR3 | **−2,34** | **−2,17** | −0,24 | −0,15 |
| AV_log | +1,58 | +0,94 | +1,62 | +1,59 |

- İşaretler aynı. Büyüklük sıralaması aynı.
- AV'de C−A farkı nete göre küçülüyor (plasebo C'de +%3,6, A'da +%1,2).
  Zaten anlamlı değildi.
- CAR3'te "gevşek parada iki kattan fazla" nete göre de duruyor: A +1,64,
  C +0,68 puan.

### P3 · CAR3

Plasebo CAR3'ü hiçbir dönemde sıfırdan ayrılmıyor. P3 tetiklenmedi.
Hükümler kural gereği nete göre de verildi:

| Dönem | K1 hükmü | Net | Yeni hüküm |
|---|---|---|---|
| A | Tekrarlandı | +1,64 · t 4,30 (1,07) | **Tekrarlandı** |
| A1 | Tekrarlandı | +1,41 · t 2,81 | **Tekrarlandı** |
| A2 | Tekrarlandı | +1,74 · t 3,73 | **Tekrarlandı** |
| B | Yön aynı, güç yetmedi | +0,76 · t 1,51 (MDE 1,41 > C 0,68) | **Yön aynı, güç yetmedi** |
| C | (referans) | +0,68 · t 2,98 | Ayakta |
| 7Y | (keşif) | +1,01 · t 4,72 | Ayakta |

H5 (temiz − P-temiz): A +1,01 · t 2,90 ve A2 +1,25 · t 2,89 ayakta. A1
+0,67 · t 1,21 ve B +0,54 · t 1,09 güç yetmedi. C +0,43 · t 1,57
sonuçsuz. 7Y +0,64 · t 3,12 ayakta. K1'in H5 tablosuyla aynı desen.

### P4 · AV_log

Yalnız raporlandı (§3). Net etkiler AV'ninkine çok yakın. Ana ölçüyü
değiştirme kararı bu notta verilmiyor.

### P5 · Ön hacim

**Plasebo altında sıfır değil.** P-geniş'te yedi yıl −%2,8 (t −1,46), A2
−%7,9 (t −2,00). "Önceki 5 günde açıklama yok" alt kümesinde yedi yıl
−%5,4 (t −2,62), C −%7,0 (t −2,32), A2 −%10,1 (t −2,42).

Sebep AV_log'unkiyle aynı: günlük log hacmin ortalaması tabanın
medyanının altında. Olay yokken günlük log ölçülerin sıfır noktası
yaklaşık −%3 … −%5.

Anlamı:

- K1'in H2 ölçüleri tabana göre. "Temiz olaylarda sıfır" (yedi yıl −%0,8)
  rastgele günlere göre **+%4,9 (t 2,06)**. Bunun kaynağı C: **+%10,5
  (t 2,79, MDE 10,5)**. A +%1,8, B −%0,1, sıfır.
- Havuzda da net pozitif: A +%6,4 (t 2,01), C +%13,4 (t 4,30).
- Asimetri kuralı gereği H2'nin A'daki "tekrarlanmadı" hükmü yükseltilmez.
  P5 yeniden hüküm istemiyor, yalnız yazılmasını istiyor.
- Ama K1'in "sızıntı izi yok" okuması **C için zayıflıyor**.
- Olası mekanik açıklama, ölçülmedi: sahte olaylar her "Yeni İş İlişkisi"
  bildiriminden ±10 gün uzak. Gerçek temiz olaylar yalnız önceki 5 günde
  açıklamasız. [t0−10, t0−6]'daki bir önceki duyurunun hacmi gerçek
  olayın ön penceresine taşabilir, sahte olayınkine taşamaz. Bu Dalga 2
  için bir soru.

## 5. Sıra ve standardize sınavlar

**Örneklem.** CAR sınavındaki 3.027 olaydan **kendi betası olan 2.679'u**.
348 çapa betalı olayın tahmin penceresi yok (60 geçerli günden az). Yan
yana verilen kümeli t aynı alt örneklemde. Tahmin günü medyan 106, en az
60. 94 olay 250 günlük pencereye düştü.

**Tahmin kalıntıları.** `beta_tahmin`'in kullandığı günler yeniden kuruldu:
aynı pencere, aynı dışlamalar (payın diğer olay pencereleri, eksik gün,
|r| ≥ %50). Her olayda ham β ve α'nın bu günlerden birebir çıktığı
denetlendi. Kalıntı CAR3'ün modeliyle: e_it = r_it − α_i − β_i·r_mt
(β küçültülmüş, α ham). Olay günü AR'lerinin toplamı CAR3'e eşit
(denetlendi). L = 3, T_i = tahmin günü sayısı.

**Formüller.**

- **Genelleştirilmiş işaret (Cowan 1992), CAR'a uyarlı.** Tahmin
  penceresi baştan örtüşmeyen 3 günlük bloklara bölünür. Üç günü de
  kalıntılı bloklar sayılır. p̂_i = pozitif blok CAR payı,
  p̂ = ort_i p̂_i. w = CAR3 > 0 olan olay sayısı.
  Z = (w − N·p̂) / √(N·p̂·(1 − p̂)).
- **Çok günlü sıra sınavı.** Corrado (1989), Corrado-Zivney (1992)
  standartlaştırılmış sıraları ve Campbell-Wasley (1993) CAR uyarlaması.
  - Her olayda tahmin kalıntıları ve üç olay günü AR'si birlikte
    sıralanır (M_i gün, eşitlikte ortalama sıra).
  - U_it = sıra / (M_i + 1).
  - Olay-zamanı günü t için Z_t = Σ_i (U_it − ½) / √N_t.
  - S_U² = ort_t Z_t². N_t ≥ 30 olan tahmin günleri ve üç olay günü
    üzerinden.
  - T = (Z_0 + Z_1 + Z_2) / (√3 · S_U).
- **BMP (Boehmer, Musumeci, Poulsen 1991).**
  - s_i² = Σ e² / (T_i − 2).
  - S_i² = s_i² · [L + L²/T_i + (Σ_τ (R_mτ − R̄_m))² / Σ_t (R_mt − R̄_m)²].
    Piyasa modelinin tahmin hatası düzeltmesi, 3 günlük toplam için.
  - SCAR_i = CAR3_i / S_i. t = ort(SCAR) / (ss(SCAR) / √N).
- **Kolari-Pynnönen (2010) düzeltmesi.**
  t_KP = t_BMP · √((1 − r̄) / (1 + (N − 1)·r̄)).
  - r̄ = SCAR'lar arası ortalama korelasyon, bütün i ≠ j çiftleri
    üzerinden.
  - Olay pencereleri çakışmayan çiftte korelasyon 0: AR'ler farklı
    günlerde.
  - Çakışan çiftte (o_ij ortak olay günü, 1–3): (o_ij / 3) · ρ_ij.
  - ρ_ij: iki olayın tahmin kalıntılarının ortak takvim günlerindeki
    Pearson korelasyonu. En az 30 ortak gün; yoksa geçerli ρ'ların
    ortalaması.
  - KP'nin özgün formülü bütün olayların aynı gün olduğunu varsayar.
    Olayları dağınık bir örneklemde tahmin penceresi korelasyonunu
    N − 1 çifte uygulamak düzeltmeyi kat kat şişirir (Sapma 9).

### Tam örneklem

| Dönem | n | Ort. | Medyan | Pozitif | Kümeli t (K1 tam / bu örneklem) | İşaret Z (p̂) | Sıra T | BMP t | r̄ | KP-BMP t | Hüküm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 791 | +1,39 | +0,56 | %55,0 | 4,86 / 3,38 | 6,65 (0,433) | 4,15 | 6,29 | 0,00037 | **5,53** | Tekrarlandı; KP-BMP destekliyor |
| A1 | 252 | +0,68 | +0,33 | %52,0 | 2,99 / 1,43 | 2,47 (0,442) | 1,68 | 2,61 | 0,00039 | **2,50** | Tekrarlandı; KP-BMP destekliyor |
| A2 | 539 | +1,72 | +0,67 | %56,4 | 4,29 / 3,38 | 6,37 (0,428) | 4,58 | 5,78 | 0,00071 | **4,91** | Tekrarlandı; KP-BMP destekliyor |
| B | 728 | +0,56 | +0,06 | %50,4 | 1,74 / 1,05 | 3,20 (0,445) | 2,60 | 2,96 | 0,00079 | 2,36 | **Yön aynı, güç yetmedi** (asimetri: yükseltilmez) |
| C | 1.160 | +0,78 | +0,41 | %54,5 | 3,32 / 3,56 | 6,47 (0,450) | 3,57 | 5,91 | 0,00026 | **5,19** | Referans; KP-BMP destekliyor |
| 7Y | 2.679 | +0,90 | +0,35 | %53,5 | 5,26 / 4,01 | 9,53 (0,444) | 5,14 | 8,95 | 0,00014 | **7,64** | Keşif; KP-BMP destekliyor |

Pencereleri çakışan çift: A 2.632 (ρ ort. 0,080; 117'si aynı payın iki
olayı), B 4.459 (0,083), C 6.870 (0,046), 7Y 14.014 (0,064). Düzeltme
çarpanı √(1 / (1 + (N − 1)·r̄)) 0,80 (B) ile 0,95 (A1) arasında.

### H5 temiz alt küme

| Dönem | n | Ort. | Medyan | Pozitif | Kümeli t (K1 / bu örneklem) | İşaret Z | Sıra T | BMP t | KP-BMP t | Hüküm |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 450 | +0,95 | +0,43 | %54,0 | 3,45 / 2,74 | 4,37 | 2,67 | 4,31 | **4,21** | Ayakta; KP-BMP destekliyor |
| A1 | 178 | +0,49 | +0,43 | %52,8 | 1,25 / 0,92 | 2,17 | 1,44 | 1,99 | 1,99 | Sonuçsuz (değişmez) |
| A2 | 272 | +1,25 | +0,44 | %54,8 | 3,74 / 2,77 | 3,87 | 2,81 | 3,89 | **3,75** | Ayakta; KP-BMP destekliyor |
| B | 417 | +0,31 | −0,15 | %48,2 | 1,45 / 0,69 | 1,50 | 1,41 | 1,55 | 1,44 | Sonuçsuz (değişmez) |
| C | 708 | +0,49 | +0,14 | %51,8 | 1,70 / 1,98 | 3,77 | 1,91 | 3,24 | 3,14 | Sonuçsuz (değişmez, asimetri) |
| 7Y | 1.575 | +0,57 | +0,14 | %51,5 | 3,77 / 2,99 | 5,64 | 2,69 | 5,36 | **5,15** | Ayakta; KP-BMP destekliyor |

### Karar

- K1'de "tekrarlandı" ya da "ayakta" olan hiçbir dönemde KP-BMP |t| < 1,96
  değil. **"Standardize sınavda zayıflıyor" notu hiçbir yere düşmüyor.**
- B (tam) ve A1, B, C (temiz) "sonuçsuz" kalıyor. Bu sınavlarda KP-BMP
  1,96'yı aşsa da (B 2,36; C temiz 3,14) asimetri kuralı gereği
  yükseltilmiyor.
- Sıra sınavı en temkinlisi: A1 1,68, temiz A1 1,44, temiz C 1,91.

### Sınavların plasebo altında davranışı (sonradan eklendi, betimleme)

Aynı dört sınav, kendi betası olan 18.570 sahte olayda koşuldu:

| Dönem | n | Ort. | Pozitif | Kümeli t | İşaret Z (p̂) | Sıra T | BMP t | KP-BMP t |
|---|---|---|---|---|---|---|---|---|
| A | 5.611 | −0,32 | %43,2 | −2,31 | −0,78 (0,437) | −0,11 | −0,73 | −0,51 |
| A1 | 2.166 | −0,42 | %43,4 | −2,03 | −0,58 | +0,52 | −1,49 | −1,10 |
| A2 | 3.445 | −0,25 | %43,0 | −1,66 | −0,53 | −0,63 | +0,15 | +0,10 |
| B | 4.628 | −0,18 | %45,3 | −0,98 | +1,13 | **+2,99** | +0,58 | +0,33 |
| C | 8.331 | +0,05 | %46,4 | +0,37 | **+1,99** | +1,91 | **+3,37** | **+2,09** |
| 7Y | 18.570 | −0,12 | %45,1 | −1,44 | +1,47 | **+2,82** | **+2,22** | +1,39 |

- Standardize ve sıra sınavları olay yokken de "anlamlı" çıkabiliyor:
  C'de KP-BMP +2,09, BMP +3,37; B'de sıra +2,99. Boyutları bu veride
  bozuk ve sapma yukarı yönlü.
- Sahte örneklem gerçekten 7 kat büyük. Aynı sapma gerçek örneklemin
  boyutunda kabaca √(1.160 / 8.331) ≈ 0,37 ile küçülür: C'de KP-BMP'de
  ~0,8 birim. Kaba bir ölçek, kesitsel bağımlılık altında tam değil.
- Sonuç: bu sınavların hükümleri "desteklemesi" zayıf kanıt. Zaten yalnız
  zayıflatabilirler. Hiçbirini zayıflatmadılar.
- Kendi betası olan sahte olaylarda kümeli t de A ve A1'de sıfırdan
  ayrılıyor (−0,32, −0,42 puan). Aşağıdaki beta kaynağı bulgusuyla
  birlikte okunmalı.

### Beta kaynağına göre CAR3 (sonradan eklendi, betimleme)

| Dönem | Kendi betası: gerçek | plasebo | net | Çapa (α = 0): gerçek | plasebo | net |
|---|---|---|---|---|---|---|
| A | +1,39 · t 3,38 | −0,32 · t −2,31 | +1,71 · t 4,09 | +2,89 · t 3,63 | **+1,98 · t 2,79** | +0,91 · t 0,84 |
| A1 | +0,68 · t 1,43 | −0,42 · t −2,03 | +1,10 · t 2,11 | +2,88 · t 2,46 | +0,95 · t 2,53 | +1,93 · t 1,66 |
| A2 | +1,72 · t 3,38 | −0,25 · t −1,66 | +1,97 · t 4,03 | +2,91 · t 2,71 | +3,41 · t 2,27 | −0,50 · t −0,25 |
| B | +0,56 · t 1,05 | −0,18 · t −0,98 | +0,74 · t 1,40 | +2,67 · t 3,61 | **+3,37 · t 2,90** | −0,70 · t −0,52 |
| C | +0,78 · t 3,56 | +0,05 · t 0,37 | +0,73 · t 3,07 | −0,47 · t −0,32 | −0,12 · t −0,23 | −0,34 · t −0,23 |
| 7Y | +0,90 · t 4,01 | −0,12 · t −1,44 | +1,02 · t 4,52 | +2,24 · t 4,11 | **+1,93 · t 3,64** | +0,31 · t 0,42 |

- Çapa betalı olaylar (çoğu ilk aylarındaki halka arz) olay yokken de
  büyük pozitif CAR3 veriyor: 2020–24'te +2 … +3,4 puan. α = 0 modeli bu
  paylardaki halka arz sonrası yükselişi "anormal" sayıyor.
- Kendi betası olanlarda 2020–22 plasebosu hafif negatif: tahmin
  penceresindeki pozitif α olay penceresinde sürmüyor.
- İki sapma havuzda birbirini götürüyor (plasebo +0,03 … +0,14). Net
  etki iki alt grupta da aynı yönde. Hükümleri taşıyan, kendi betası
  olan olaylar: A +1,71 (t 4,09), C +0,73 (t 3,07).

### Kotası dolan paylarla (sonradan eklendi, betimleme)

Kotası dolan 321 (pay, dönem) çifti: 1.488 gerçek, 14.880 sahte olay.
Bileşim eşit.

| Dönem | AV plasebo | AV net | CAR3 plasebo | CAR3 net | Ön hacim net |
|---|---|---|---|---|---|
| A | +%2,7 · t 0,80 | +%34,4 · t 7,63 | −0,07 · t −0,63 | +0,95 · t 2,55 | +%7,2 · t 1,97 |
| A1 | +%11,5 · t 2,40 | +%23,4 · t 3,31 | −0,01 · t −0,08 | +0,86 · t 1,53 | +%0,2 · t 0,04 |
| A2 | −%2,6 · t −0,63 | +%42,0 · t 6,57 | −0,11 · t −0,71 | +1,02 · t 2,23 | +%12,0 · t 2,55 |
| B | +%2,2 · t 0,41 | +%35,1 · t 4,62 | −0,15 · t −0,73 | +1,43 · t 2,45 | +%13,5 · t 2,61 |
| C | +%3,8 · t 1,13 | +%37,7 · t 7,62 | +0,04 · t 0,35 | +0,49 · t 1,47 | +%13,5 · t 3,18 |
| 7Y | +%3,0 · t 1,40 | +%35,9 · t 10,79 | −0,05 · t −0,64 | +0,88 · t 3,67 | +%11,1 · t 4,49 |

- Hacim bulguları bu alt kümede daha güçlü.
- CAR3'te dönem deseni oynuyor: B +1,43 (t 2,45), C +0,49 (t 1,47).
  Sık bildirim yapan paylar çıkınca C zayıflıyor, B güçleniyor. Sonradan
  kurulmuş bir alt küme. Hüküm değiştirmez (B için asimetri, C için ön
  kayıt dışı).

## 6. Ne anlama geliyor

**Ölçüm aleti.** AV'nin sıfır noktası olay yokken sıfıra yakın. AS2'nin
korktuğu yapısal şişme ölçülen iki sapmanın toplamında kayboluyor. Hacim
bulgusu, rejim sırası ve büyüklükler nete göre de aynı. CAR3'ün havuz
plasebosu sıfır. Ama alt gruplarda (beta kaynağı) yapısal sapma var.
Günlük log ölçülerin (ön hacim, profil) sıfır noktası sıfır değil,
yaklaşık −%3 … −%5.

**Makaleye önerilen cümle değişiklikleri (UYGULANMADI; karar Hüseyin'in):**

1. `site/content/metodoloji.html:825` H1 satırı. Ham rakamların yanına net:
   "+%28,9 (rastgele günlere göre net +%27,4)", B "+%22,0 (net +%20,8)",
   C "+%38,8 (net +%33,9)". P1 yalnız A1'de tetiklendi. Makale A1'i
   ayrıca veriyorsa: "A1 +%29,1; rastgele günlerde de +%11,3, net
   +%16,1 (t 2,53)".
2. `:274` ve `:837` "Bilgi sızıyor yorumu hiçbir dönemde desteklenmiyor."
   Önerilen: "Temiz olaylarda ön hacim tabana göre sıfır (yedi yıl
   −%0,8). Olaysız günlerin aynı ölçüsü tabanın %5 altında. Buna göre
   2020–24'te iz yok, 2024–26'da temiz olaylarda bile +%10,5 (t 2,8)
   kalıyor. Bunun bir kısmı bir önceki duyurunun taşması olabilir;
   ayrıştırılmadı."
3. `:826` H2 satırı. Yanına "rastgele günler: A −%4,2, B −%4,3, C −%7,0"
   ya da bir dipnot.
4. `:836` "A ile C arasındaki fark anlamlı (z = −2,34)". Ek: "rastgele
   günlere göre net farkla z = −2,17".
5. H3'e (`:827`) bir cümle: "Medyan, işaret, sıra ve standardize (BMP,
   Kolari-Pynnönen) sınavlar aynı yönde; A, A1, A2 ve C'de KP-BMP
   t 2,5–5,5." Bu sınavların plasebo altında da hafif yukarı yanlı
   olduğu Sınırlar'a girmeli.
6. Harita §3 AS2'deki "Tahmin, ölçülmedi" artık ölçüldü: fark +0,05 …
   +0,08 log, ama sola çarpık günlük log hacim bunu götürüyor; net
   plasebo AV'si yedi yılda +%2,2 (t 1,03).

**Ürün için (öneri, uygulanmadı).** Çapa betalı olaylarda (yeni halka
arz, α = 0) rastgele günlerde de CAR3 +1,9 puan. Sitenin tepki paneli
aynı çapa kuralını kullanıyor. Yanlılık bu bülten hattında ölçüldü,
üretimdeki yfinance/XU100 hattında sınanmadı. Sınanana kadar çapa betalı
tepkilerin işaretlenmesi düşünülebilir.

**Dalga 2 için sorular.**

- Ön hacimde eşleştirilmiş plasebo: gerçek temiz olaylar da [t0−10, t0−6]
  duyurularından arındırılarak.
- Beta kaynağına göre yanlılık: halka arzlar için ayrı bir normal getiri
  modeli.
- Standardize sınavların boyutu: aynı pay-günlerinde tekrarlı plasebo
  çekilişleriyle ret oranı.

## 7. Sapmalar

Hepsi sonuç görülmeden kararlaştırıldı. Sonradan eklenenler 13'te.

1. **10 kat her payda sağlanamadı.** 390 (pay, dönem) çiftinin 69'unda
   aday gün yetmedi: her yeni iş duyurusunun ±10 günü dışlanınca sık
   bildirim yapan payda gün kalmıyor (GESAN A: 93 olay, 13 aday gün).
   Bu çiftlerde bütün adaylar alındı (kural kodda sonuçtan önce vardı).
   Sahte olay 20.354, hedef 30.910, etkin kat 6,6. Gerçek olayların
   1.603'ü kotası dolmayan çiftlerde. Kat 5'e inme kuralı işlemedi: süre
   4,5 dakika.
2. **P-temiz tanımı.** Harita iki şey söylüyor: "K1'deki `olay_temiz`
   tanımıyla aynı" ve "hiçbir KAP açıklaması yok". İkisi aynı değil. K1'in
   `olay_temiz`'i yalnız `KATEGORILER`'deki yedi türe bakıyor (finansal
   rapor, sermaye işlemi, geri alım, kâr payı, birleşme/edinim, ihale,
   başka yeni iş). "Özel Durum Açıklaması (Genel)" ve "Olağan Dışı Fiyat"
   sayılmıyor. H5 ile karşılaştırılabilirlik için K1'in kod tanımı
   uygulandı. Not: K1 notunun "başka hiçbir KAP açıklaması olmayan"
   ifadesi de kod tanımından geniş.
3. **Arşiv sonu.** Liste arşivi 2026-09-19'da, panel 2026-09-25'te
   bitiyor. Dışlama penceresi doğrulanabilsin diye aday t0 için
   t0+10 ≤ 2026-09-19 şartı kondu. Son aday gün 2026-09-04. C'nin son
   15 işlem günü (2026-09-07 → 09-25) plaseboya girmedi.
4. **Aday gün = payın listelendiği gün.** Harita "işlem günleri" diyor.
   Payın bültende satırı olmayan gün gerçek olay da olamaz.
5. **Sahte olaylarda Vasicek havuzu** dönemin sahte olayları. Ortak havuz
   gerçek olayların CAR3'ünü değiştirirdi (hat bozulurdu). Sahte olaylar
   paylara gerçeklerle orantılı dağıldığı için çapa benzer.
6. **`car3_dislamali`.** K1 `car3` akışının dışlaması parametreli
   kopyası. Gerekçe §1'de. Gerçek olaylarda fark 0.
7. **Eşleştirme.** H1/H3 neti bütün gerçek − P-geniş; H5 neti gerçek
   temiz − P-temiz. K1 kurallarındaki "C'deki etki" C'nin net etkisi.
8. **Sıra ve standardize sınavlarda örneklem** kendi betası olan 2.679
   olay. 348 çapa betalı olayın tahmin penceresi yok. Aynı alt örneklemin
   kümeli t'si yan yana verildi.
9. **Kolari-Pynnönen r̄'si.** KP'nin formülü ortak olay gününü varsayar.
   r̄ burada SCAR çiftlerinin ortalama korelasyonu: pencere çakışmayan
   çift 0, çakışan çift (o/3)·ρ (§5).
10. **Sıra sınavı uyarlaması.** Corrado-Zivney standart sıraları +
    Campbell-Wasley çok günlü toplam. S_U yalnız N_t ≥ 30 olan tahmin
    günlerinden ve olay günlerinden.
11. **Kalıntı modeli** CAR3'ün modeli (küçültülmüş β, ham α). Kalıntı
    ortalaması tam sıfır değil. Genelleştirilmiş işaret sınavı bunu p̂ ile
    emiyor. BMP'nin tahmin hatası terimi OLS varsayımıyla.
12. **İşaret sınavı blokları** tahmin penceresinin başından. **AV_log'da**
    sıfır adetli gün AV'deki gibi düşüyor.
13. **Sonuçlar görüldükten sonra eklenenler** (hüküm kurallarına
    girmiyor, betik çıktısında "SONRADAN" başlığıyla):
    - P5 tablosunda "önceki 5 gün temiz" alt kümesinin gerçek ve net
      satırları. İlk koşu yalnız plasebo ortalamasını veriyordu.
    - Kotası dolan çiftlerle net.
    - Beta kaynağına göre CAR3.
    - Sıra ve standardize sınavların plasebo altında davranışı.

## 8. Sınırlar

- **Plasebo günleri sessiz dönemlerden.** Her yeni iş duyurusunun ±10 günü
  dışlandı. Sahte olay, gerçek olaydan daha seyrek haber alan bir günü
  temsil ediyor olabilir. Ön hacim karşılaştırmasında bu asimetri
  önemli (§4 P5).
- **Bileşim farkı.** Sık bildirim yapan paylar plaseboda eksik temsil
  ediliyor. Kotası dolan alt küme hacim sonuçlarını değiştirmiyor, CAR3'te
  dönem desenini oynatıyor (§5).
- **Tek tohum.** Plasebo çekilişinin kendi değişkenliği tekrarlı
  çekilişlerle ölçülmedi. Plasebo ortalamasının SE'si kümeli ve n'si büyük.
- **Standardize sınavların boyutu bozuk.** Plasebo altında C'de KP-BMP
  +2,09. İşaret sınavı ve BMP kesitsel bağımlılığı düzeltmiyor. KP yalnız
  pencere çakışmasını düzeltiyor.
- **Çoklu sınama.** Bu notta onlarca sınav var. Hükümler yalnız ön
  kayıtlı kurallarla verildi. Sonradan eklenen bölümler hüküm değiştirmez.
- **Nedensellik yok.** Net etki, bildirim gününü rastgele bir günle
  karşılaştırır. Bildirimin neden olduğunu kanıtlamaz.
