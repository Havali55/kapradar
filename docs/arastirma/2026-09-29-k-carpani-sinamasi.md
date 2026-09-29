# K çarpanı örneklem dışında: ilk yılın dört iddiası (D1-K, 2026-09-29)

**Ön kayıt:** `2026-09-29-arastirma-haritasi.md` §6 "D1-K" (commit
`df9a7f8`, sonuçlardan önce). Karar kuralları K1 ön kaydından
(`2026-09-28-k1-on-kayit.md`).
**Yeniden üretim:** `python scripts/analiz_k_carpani.py --mutabakat`. LLM
yok, ücret yok, veritabanına yazmıyor, KAP'a gitmiyor. `--mutabakat`
19.09'un olay matrisini okur (`data/ozellikler.csv`, commit `19f630e`).

## Özet

K (karşı taraf açık/gizli × ilk bildirim/güncelleme: 1,00 / 0,85 / 0,70 /
0,50) 19.09'da ilk yılın 2×2 tablosundan kuruldu. Tablonun dört iddiası,
bulgular kurulurken hiç görülmemiş yılda (2024-09 → 2025-09-21, 663 olay,
109 pay) aynı hatla ve bugünkü sınıflamayla yeniden ölçüldü.

- **Örneklem dışı yılda dört iddianın hiçbiri tekrarlanmadı.** Dördü de
  K1 kuralıyla "sonuçsuz". Üçünde nokta tahmini ters yönde.
  - K-H1, açık + ilk > gizli + ilk (CAR3): −0,16 puan, t −0,29. İlk yıl
    +1,21.
  - K-H2, gizli + ilk tepkiyi geri veriyor (CAR3 − CAR1): −0,09 puan,
    t −0,29. İlk yıl −0,82.
  - K-H3, açıkta ilk > güncelleme (CAR3): −0,35 puan, t −0,30. İlk yıl
    +0,55.
  - K-H4, hacim sıralaması: gözlenen açık + ilk (0,314) < gizli + ilk
    (0,353) < açık + güncelleme (0,376). İddianın neredeyse tersi. Hiçbir
    fark anlamlı değil.
- **"Güç yetmedi" burada "belki aynı büyüklükte vardır" demek değil.**
  K-H1 ve K-H2'de ilk yılın büyüklüğü sınama yılının %95 aralığının
  dışında (K-H1 [−1,22; +0,91], K-H2 [−0,69; +0,51]). Bu okuma ön kayıtta
  yok, hükmü değiştirmiyor.
- **İki yıl birlikte:** K-H1 +0,57 (t 1,40), K-H2 −0,21 (t −0,90). K1
  kuralıyla ikisi de "tekrarlanmadı: etki ilk yıl iddiasından küçük"
  (sınırda: MDE 1,15 / 1,21 ve 0,64 / 0,82). K-H3 ve K-H4 sonuçsuz.
- **İlk yılın kendi tablosu da bugün farklı.** 19.09 tablosu birebir
  yeniden üretildi, sonra değişiklikler tek tek eklendi (§3):
  - K-H1 ilk yılda duruyor, büyüyor: +1,80 / +0,33, fark +1,47 (t 2,27).
    Ama bu K'nın türetildiği yıl, sınav değil.
  - K-H2'nin "üçüncü günde tamamını geri veriyor" hâli zayıfladı:
    +0,65 → +0,33 (−0,32, t −0,88).
  - K = 0,50'nin tek dayanağı olan −5,18 (n 6) kayboldu: 17 olayla +0,31.
  - AV sıralaması ilk yılda da tutmuyor: açık + güncelleme 0,289 < gizli
    + ilk 0,292 < açık + ilk 0,320.
- **Farkın kaynakları ayrıldı:**
  1. **bbac018 sınıflama düzeltmesi** en büyüğü. İlk yılın 612
     bildiriminden 123'ü "açık"tan "gizli"ye geçti. Gizli + güncelleme 6
     → 18 olay, −5,18 → +0,26. K-H2 −0,82 → −0,51.
  2. **21.09'daki AV sağlaması kısa fiyat geçmişiyle hesaplanmıştı.**
     Fiyat serisi 2025-09-07'de başlıyordu; ilk yılın ilk iki ayındaki
     olaylar AV'siz kaldı (601'in 512'si ölçülmüştü). Tam geçmişle,
     sınıflama değişmeden bile sıralama bozuluyor.
  3. **Piyasa modeli** (β = 1 XU100 → EW piyasa modeli, Vasicek). K-H1'i
     değiştirmiyor, K-H2'yi −0,51 → −0,36'ya küçültüyor.

  Yeni olaylar ve yayın süzgecinin etkisi küçük.
- **24.09'daki ters AV sağlaması bbac018'den sonra da ters** (sınama:
  gizli + ilk 0,353 > açık + ilk 0,314).
- **İkincil (skorlu bildirimler, CAR3 ~ gizli + güncelleme + f(r)):**
  gizli katsayısı sınamada +0,75 (t 1,50), analiz yılında −1,45
  (t −2,03), iki yılda −0,24 (t −0,54). Güncelleme üçünde de −0,9 ile
  −1,1 arası, hiçbirinde anlamlı değil.
- **Sonuç:** K'nın değerlerinin örneklem dışında ampirik dayanağı yok.
  Metodolojinin "birebir uyumlu" cümlesi bugünkü veriyle ilk yılda bile
  doğru değil. Karar Hüseyin'in, seçenekler §6'da.

## 1. Soru ve neden şimdi

Skor `S = clamp(5 · f(r) · K, 0, 5)`. K'nın iki dayanağı var:

1. **CAR3 (19.09, kanıt taraması §4):** Karşı tarafı gizli ilk bildirim
   ilk gün +0,84 alıyor, üçüncü günde +0,02'ye iniyor. Açık + ilk +1,23.
   Gizli + güncelleme −5,18 (n 6).
2. **AV sağlaması (21.09, metodoloji K bölümü):** "n ≥ 55 olan üç hücrede
   anormal hacim sıralaması K sıralamasıyla birebir uyumlu" (0,259 < 0,317
   < 0,351).

24.09 örneklem dışı tablosunda ikinci dayanak ters çıktı (gizli + ilk
0,397 > açık + ilk 0,317). K bölümüne not düşülmedi. Birinci dayanak öbür
yılda hiç raporlanmadı. 25.09'da karşı taraf sınıflaması değişti (`bbac018`:
"dolu alan isim demek değil"). Harita bunu AS1 olarak kaydetti.

## 2. Veri ve yöntem

- **Olaylar:** `skor_gecerlilik.yukle` ile aynı sorgu (bildirim ⋈ son
  çıkarım ⟕ tepki), sonra yayın evrenine (`akis` görünümü: kapı, bağ,
  elle karar) süzüldü. 1.317 bildirimden 1.269'u yayında. Tekilleştirme
  yok (`skor_gecerlilik` §7 gibi).
- **Dönemler** (`donem_suz`, `ANALIZ_BASI` = 2025-09-22, İstanbul):

  | Dönem | Aralık | Olay | Pay | CAR3'lü |
  |---|---|---|---|---|
  | Sınama (örneklem dışı) | 2024-09-02 → 2025-09-21 | 663 | 109 | 659 |
  | Analiz (K'nın yılı) | 2025-09-22 → 2026-09-28 | 606 | 112 | 598 |
  | İki yıl | | 1.269 | 145 | 1.257 |

  Fiyat serisi 2026-09-25'te bitiyor; son günlerin olaylarında CAR3 yok.
- **Hücreler:** `bildirim.karsi_taraf_acik` (bbac018 sınıflayıcısı) ×
  `guncelleme_mi`. K değerleri `kap_radar.skor.guvenilirlik`'ten.
- **Ölçüler:**
  - CAR1, CAR3, CAR5: `tepki` tablosu. Model "ew": eşit ağırlıklı BIST'e
    karşı piyasa modeli, 120 gün, Vasicek küçültmesi. 64 olayda beta yok,
    evren ortalaması.
  - AV: `skor_gecerlilik.anormal_hacim`, ln(ort. hacim [t0, t0+2]) −
    ln(medyan hacim [t0−60, t0−11]).
- **Sınav:** Doygun hücre modeli. Dört hücrenin üçü gösterge, sabit taban
  hücre, aranan fark son katsayı. Standart hata pay ve ISO hafta (t0)
  düzeyinde iki yönlü kümeli (`analiz_gecerlilik.ols_kumeli`). MDE = 2,8 ×
  SE.
  - K-H2: gizli + ilk hücresinde CAR3 − CAR1 ortalaması, aynı kümeleme
    (`_sabit`).
  - K-H4: üç ikili AV farkı. Bütün hüküm: üçü tekrarlandıysa tekrarlandı,
    biri tekrarlanmadıysa tekrarlanmadı, gerisi sonuçsuz.
  - Her ölçünün kendi örneklemi: CAR_k'si ya da AV'si olan olaylar.
    Hücre tablolarındaki AV ise §7 gibi CAR3'lü olaylar üzerinden.
- **Karar kuralları:** K1 (tekrarlandı / yön aynı, sonuçsuz /
  tekrarlanmadı). "İlk yıl etkisi" haritadaki 19.09 rakamları. K1'in iki
  tanımının örtüştüğü durumda (aynı işaret, |t| < 1,96, MDE < ilk yıl
  etkisi) "tekrarlanmadı: etki daha küçük" seçildi (K1 notunun H2/A
  uygulamasıyla aynı).
- **Sağlamlık (sınama yılı):** yayın süzgeci olmadan; (pay, t0) tekil
  (K1 kuralı). Asimetri kuralı geçerli.

## 3. İlk yıl, bugünkü veriyle

### 19.09 ve bugün

| Hücre | K | n 19.09 → bugün | CAR1 | CAR3 | CAR3 medyan | AV |
|---|---|---|---|---|---|---|
| açık + ilk | 1,00 | 327 → 217 | +1,16 → +1,59 | +1,23 → **+1,80** | +0,69 → +1,53 | 0,351 → 0,320 |
| açık + güncelleme | 0,85 | 55 → 45 | +0,50 → +0,49 | +0,68 → +0,69 | +0,23 → +0,64 | 0,317 → 0,289 |
| gizli + ilk | 0,70 | 213 → 319 | +0,84 → +0,65 | +0,02 → **+0,33** | −0,04 → +0,36 | 0,259 → 0,292 |
| gizli + güncelleme | 0,50 | 6 → 17 | −0,75 → +0,70 | **−5,18 → +0,31** | −3,16 → +0,83 | 0,615 → 0,578 |

CAR puan. Bugün = analiz dönemi, yayın evreni.

### Adım adım (CAR3; hücrede n · ortalama)

| Adım | açık + ilk | açık + güncelleme | gizli + ilk | gizli + güncelleme | gizli + ilk CAR1 |
|---|---|---|---|---|---|
| 19.09 tablosu | 327 · +1,23 | 55 · +0,68 | 213 · +0,02 | 6 · −5,18 | +0,84 |
| M0 · 19.09 matrisi (β = 1, "alan dolu") | 327 · +1,23 | 55 · +0,68 | 213 · +0,02 | 6 · −5,18 | +0,84 |
| M1 · + bugünkü sınıflama (bbac018) | 218 · +1,59 | 43 · +0,04 | 322 · +0,19 | 18 · +0,26 | +0,70 |
| M2 · + bugünkü CAR (EW piyasa modeli) | 220 · +1,73 | 45 · +0,51 | 328 · +0,31 | 18 · +0,24 | +0,67 |
| M2b · yalnız model (eski sınıflama) | 330 · +1,34 | 57 · +1,01 | 218 · +0,19 | 6 · −5,09 | +0,78 |
| M3 · bugünkü olay seti, aynı pencere | 220 · +1,73 | 46 · +0,67 | 328 · +0,31 | 18 · +0,24 | +0,67 |
| M4 · + 19.09 sonrası olaylar | 223 · +1,87 | 46 · +0,67 | 331 · +0,36 | 18 · +0,24 | +0,71 |
| M5 · + yayın evreni (ana tablo) | 217 · +1,80 | 45 · +0,69 | 319 · +0,33 | 17 · +0,31 | +0,65 |

M0, 19.09 tablosunu birebir üretiyor. Farklar:

| Adım | K-H1 farkı | K-H2 (CAR3 − CAR1) | K-H3 farkı |
|---|---|---|---|
| M0 · 19.09 | +1,21 | −0,82 | +0,55 |
| M1 · bbac018 | +1,40 | −0,51 | +1,55 |
| M2 · + model | +1,42 | −0,36 | +1,22 |
| M2b · yalnız model | +1,15 | −0,59 | +0,33 |
| M5 · ana | +1,47 | −0,32 | +1,11 |

Okuma:

- **bbac018:** 612 bildirimin 123'ü açıktan gizliye geçti (açık + ilk →
  gizli + ilk 111, açık + güncelleme → gizli + güncelleme 12). K-H1'i
  büyüttü, K-H2'yi üçte bir küçülttü. K = 0,50 hücresinin −5,18'ini
  tümüyle sildi: yeni gelen 12 olayla hücre +0,26.
- **Piyasa modeli:** K-H1'e dokunmuyor. K-H2'yi −0,51 → −0,36'ya
  küçültüyor. Olay bazında β = 1 ile bugünkü CAR3'ün korelasyonu 0,957;
  600 olayın 356'sında fark 1 puandan büyük.
- **Olay seti:** Aynı pencerede bugün 1 bildirim fazla (açık +
  güncelleme; tek başına hücre ortalamasını +0,51 → +0,67 taşıyor). 19.09
  sonrası 6 olay, yayın süzgeci 20 olay çıkarıyor. Etkileri küçük.

### AV (parantezde AV'si olan olay)

| Adım | açık + ilk | açık + güncelleme | gizli + ilk | gizli + güncelleme |
|---|---|---|---|---|
| 21.09 (metodoloji K bölümü) | 0,351 | 0,317 | 0,259 | 0,615 |
| A0 · 19.09 seti, fiyat 2025-09-07 →, eski sınıflama | 0,351 (286) | 0,317 (46) | 0,259 (174) | 0,614 (6) |
| A1 · + tam fiyat geçmişi (2024-01 →) | 0,324 (317) | **0,343** (54) | 0,294 (209) | 0,613 (6) |
| A2 · + bbac018 | 0,327 (213) | 0,287 (42) | 0,302 (313) | 0,564 (18) |
| A5 · bugünkü ana tablo | 0,320 (212) | 0,289 (44) | 0,292 (310) | 0,578 (17) |

- A0, 21.09'daki sağlamayı birebir üretiyor. O gün 601 CAR3'lü olayın
  512'sinde AV vardı. Eksik 89'un 75'i Eylül–Kasım 2025 olayları: taban
  penceresi (t0−60) fiyat serisinin başından önceye düşüyordu.
- Tam fiyat geçmişiyle (A1), sınıflamaya dokunmadan, açık + güncelleme
  açık + ilk'i geçiyor. Sağlama kısmi bir örneklemin ürünüydü.
- Bugünkü sınıflamayla (A2, A5) sıra açık + güncelleme < gizli + ilk <
  açık + ilk. K'nın sırası (gizli + ilk en altta) ilk yılda da yok.

### 24.09'un ters sağlaması bugünkü sınıflamayla

| Sınama yılı | açık + ilk | açık + güncelleme | gizli + ilk | gizli + güncelleme |
|---|---|---|---|---|
| AV, eski sınıflama (24.09'u üretiyor) | 0,317 | 0,318 | **0,397** | 0,188 |
| AV, yeni sınıflama | 0,320 | 0,370 | **0,364** | 0,045 |
| AV, yeni sınıflama, yayın evreni | 0,314 | 0,376 | **0,353** | 0,123 |
| CAR3, eski sınıflama | 409 · +0,68 | 71 · +0,65 | 202 · +0,36 | 5 · +2,09 |
| CAR3, yeni sınıflama | 291 · +0,51 | 61 · +0,74 | 320 · +0,63 | 15 · +0,79 |

Ters AV sağlaması bbac018'den sonra da duruyor. CAR3 tarafında ise
eski sınıflamayla sınama yılında K-H1'in yönü tutuyordu (+0,32).
Sınıflama düzeltilince tersine döndü: sınamada açık + ilk'ten gizliye
geçen 118 "dolu ama anonim" bildirimin CAR3 ortalaması ~+1,1, kalanların
+0,51. İlk yılda aynı düzeltme K-H1'i
büyütmüştü. İki yılda ters yönde çalışan bir düzeltme, hücre farkının
küçük ve gürültülü olduğunu gösteriyor.

## 4. Hipotezler

İki yönlü kümeli t. Fark puan (K-H4'te log). "Analiz" satırı referans:
K'nın türetildiği yıl, sınav değil.

### Hücreler

| Dönem | Hücre | n | Pay | CAR1 | CAR3 | CAR3 medyan | CAR5 | AV |
|---|---|---|---|---|---|---|---|---|
| Sınama | açık + ilk | 281 | 75 | +1,27 | +0,49 | −0,02 | +0,42 | 0,314 |
| | açık + güncelleme | 60 | 24 | +1,12 | +0,84 | +0,12 | +1,14 | 0,376 |
| | gizli + ilk | 304 | 61 | +0,74 | +0,65 | +0,27 | +0,35 | 0,353 |
| | gizli + güncelleme | 14 | 7 | −0,10 | +1,23 | −0,04 | +0,76 | 0,123 |
| İki yıl | açık + ilk | 498 | 96 | +1,41 | +1,06 | +0,60 | +1,17 | 0,317 |
| | açık + güncelleme | 105 | 34 | +0,85 | +0,78 | +0,31 | +1,13 | 0,339 |
| | gizli + ilk | 623 | 89 | +0,69 | +0,49 | +0,29 | +0,31 | 0,322 |
| | gizli + güncelleme | 31 | 16 | +0,34 | +0,72 | +0,27 | +0,72 | 0,381 |
| Analiz | açık + ilk | 217 | 65 | +1,59 | +1,80 | +1,53 | +2,16 | 0,320 |
| | açık + güncelleme | 45 | 18 | +0,49 | +0,69 | +0,64 | +1,12 | 0,289 |
| | gizli + ilk | 319 | 71 | +0,65 | +0,33 | +0,36 | +0,26 | 0,292 |
| | gizli + güncelleme | 17 | 11 | +0,70 | +0,31 | +0,83 | +0,69 | 0,578 |

CAR1 ve CAR5 medyanları betikte.

### K-H1 · Açık + ilk CAR3 > gizli + ilk CAR3 (ilk yıl +1,21)

| Dönem | Fark | t | %95 | MDE | Hüküm |
|---|---|---|---|---|---|
| **Sınama** | −0,16 | −0,29 | [−1,22; +0,91] | 1,52 | **Yön ters, sonuçsuz (güç yetmedi)** |
| İki yıl | +0,57 | +1,40 | [−0,23; +1,38] | 1,15 | Tekrarlanmadı: etki daha küçük (sınırda) |
| Analiz | +1,47 | +2,27 | [+0,20; +2,73] | 1,80 | (örneklem içi) |

- Dönem farkı z = +1,93. İşaret tutarsız.
- Betimleme, hipotez değil: CAR1 farkı sınamada +0,53 (t 1,55), analizde
  +0,99 (t 2,61). CAR5 farkı sınamada +0,06, analizde +1,90.

### K-H2 · Gizli + ilk'te tepki geri veriliyor: CAR3 − CAR1 < 0 (ilk yıl −0,82)

| Dönem | CAR1 → CAR3 | Fark | t | %95 | MDE | Hüküm |
|---|---|---|---|---|---|---|
| **Sınama** | +0,74 → +0,65 | −0,09 | −0,29 | [−0,69; +0,51] | 0,85 | **Yön aynı, sonuçsuz (güç yetmedi; MDE sınırda)** |
| İki yıl | +0,69 → +0,49 | −0,21 | −0,90 | [−0,66; +0,24] | 0,64 | Tekrarlanmadı: etki daha küçük |
| Analiz | +0,65 → +0,33 | −0,32 | −0,88 | [−1,03; +0,39] | 1,02 | (örneklem içi) |

- Dönem farkı z = −0,49.
- Betimleme, hipotez değil: sınamada geri verme açık + ilk hücresinde
  görülüyor (CAR3 − CAR1 −0,78, t −2,74). Analiz yılında açık + ilk'te
  yok (+0,21). "Geri verme gizli karşı tarafa özgü" okuması örneklem
  dışında desteklenmiyor.

### K-H3 · Açık + ilk CAR3 > açık + güncelleme CAR3 (ilk yıl +0,55)

| Dönem | Fark | t | %95 | MDE | Hüküm |
|---|---|---|---|---|---|
| **Sınama** | −0,35 | −0,30 | [−2,63; +1,93] | 3,26 | **Yön ters, sonuçsuz (güç yetmedi)** |
| İki yıl | +0,28 | +0,53 | [−0,77; +1,34] | 1,51 | Yön aynı, sonuçsuz (güç yetmedi) |
| Analiz | +1,11 | +0,75 | [−1,79; +4,01] | 4,15 | (örneklem içi) |

Açık + güncelleme hücresi 45–60 olay. MDE ilk yıl farkının 3–8 katı. Bu
hipotez hiçbir örneklemde sınanabilecek güçte değil.

### K-H4 · AV sıralaması: gizli + ilk < açık + güncelleme < açık + ilk

| Dönem | gizli + ilk | açık + güncelleme | açık + ilk | Gözlenen sıra |
|---|---|---|---|---|
| 21.09 | 0,259 | 0,317 | 0,351 | K ile aynı |
| **Sınama** | 0,353 | 0,376 | 0,314 | açık + ilk < gizli + ilk < açık + güncelleme |
| İki yıl | 0,325 | 0,330 | 0,316 | aynı; en büyük fark 0,014 |
| Analiz | 0,298 | 0,269 | 0,318 | açık + güncelleme < gizli + ilk < açık + ilk |

AV'si olan bütün olaylar üzerinden (hücre tablosundan en çok 0,02 farklı).

| İkili fark | İlk yıl | Sınama (t; MDE) | İki yıl (t; MDE) | Analiz (t) |
|---|---|---|---|---|
| açık + ilk − gizli + ilk | +0,092 | −0,039 (−0,67; 0,162) | −0,009 (−0,21; 0,125) | +0,019 (+0,23) |
| açık + ilk − açık + güncelleme | +0,034 | −0,062 (−0,80; 0,217) | −0,014 (−0,20; 0,200) | +0,049 (+0,38) |
| açık + güncelleme − gizli + ilk | +0,058 | +0,023 (+0,27; 0,239) | +0,005 (+0,06; 0,224) | −0,030 (−0,22) |

- **Hüküm, sınama: sonuçsuz.** Üç farktan ikisinin işareti ters. Hiçbiri
  anlamlı değil. İki yıl birlikte de sonuçsuz.
- MDE'ler ilk yıl farklarının 1,4–6 katı. 21.09'daki "birebir uyum"
  0,03–0,09'luk farklara dayanıyordu. Bu farkları ayırt edecek güç ne o
  yılda ne iki yılda var.
- Dönem farkı z: +0,56 / +0,73 / −0,33.

### Gizli + güncelleme (yalnız rapor)

Sınamada 14 olay, CAR3 +1,23 (medyan −0,04). Analiz yılında 17 olay,
+0,31. İki yılda 31 olay, +0,72. K = 0,50'nin dayanağı olan −5,18 hiçbir
dönemde yok.

### Sağlamlık (sınama yılı)

| Deneme | Olay | K-H1 t | K-H2 t | K-H3 t | K-H4 |
|---|---|---|---|---|---|
| Ana (yayın evreni) | 663 | −0,29 | −0,29 | −0,30 | sonuçsuz |
| Yayın süzgeci yok | 691 | −0,22 | −0,30 | −0,19 | sonuçsuz |
| (pay, t0) tekil | 629 | −0,24 | −0,21 | −0,23 | sonuçsuz |

Hiçbir hüküm değişmiyor.

## 5. İkincil regresyon

Skorlu bildirimlerde CAR3 ~ gizli + güncelleme + f(r). f(r)
`kap_radar.skor.f_oran` (taban %0,25). Katsayı puan; parantezde t ve MDE.
K'ya göre gizli ve güncelleme negatif olmalı.

| Örneklem | n (pay) | gizli | güncelleme | f(r) |
|---|---|---|---|---|
| **Sınama** | 467 (76) | **+0,75** (1,50; 1,41) | −0,91 (−1,37; 1,87) | +1,20 (0,90; 3,72) |
| İki yıl | 942 (92) | −0,24 (−0,54; 1,23) | −0,95 (−1,75; 1,52) | +0,32 (0,31; 2,94) |
| Analiz | 475 (71) | −1,45 (−2,03; 2,01) | −1,07 (−0,94; 3,20) | −0,36 (−0,21; 4,71) |

- **Gizli:** Yalnız analiz yılında negatif ve anlamlı. Sınamada ters.
  İki yıl birlikte sıfırdan ayrılmıyor. K-H1 ile aynı desen.
- **Güncelleme:** Üç örneklemde de −0,9 ile −1,1 arası. Hiçbirinde
  anlamlı değil. MDE 1,5–3,2 puan. Tutarlı işaret, yetersiz güç. Hücre
  karşılaştırması (K-H3) sınamada ters çıkmıştı; buradaki fark skorlu alt
  örneklem ve gizli kontrolü. İkisi birlikte "güncellemenin tepkisi
  küçük" iddiasını ne destekliyor ne çürütüyor.
- **f(r):** Her yerde sıfır. Bulgu 3 ve 11 ile tutarlı: büyüklük tepkiyi
  öngörmüyor.

## 6. Ne anlama geliyor

Bu not K'yı değiştirmez. Karar Hüseyin'in. Önce olgular:

- K'nın iki ampirik dayanağından (CAR3 tablosu, AV sağlaması) hiçbiri
  örneklem dışında tekrarlanmadı.
- AV sağlaması bugünkü veriyle ilk yılda da tutmuyor. Metodolojinin K
  bölümündeki (`site/content/metodoloji.html:387`) "birebir uyumlu"
  cümlesi ve tablosu bbac018 ve tam fiyat geçmişi öncesinin rakamları.
  Hangi seçenek seçilirse seçilsin bu cümle düzeltilmeli.
- K = 0,50'nin dayanağı (−5,18, n 6) sınıflama düzeltmesiyle kayboldu.
  Değer 25.09'da yeniden değerlendirilmedi. İlk yılda 12 bildirim bu
  hücreye geçti; yayındaki 22 skorlu bildirim bugün 0,50 alıyor.
- İki not çelişiyor. Skor formülü notu (`2026-09-19-skor-formulu-onerisi.md`
  §2) "2×2 tablodan türetildi" diyor. Metodoloji "tepki sütunları K'yı
  türetmez" diyor.
- Tek destek: ilk yılda (örneklem içi) K-H1 bugünkü veriyle anlamlı
  (+1,47, t 2,27). İkincil regresyonda da gizli yalnız o yılda anlamlı.

Yayındaki 947 skorlu bildirimin 608'inde K < 1 (0,70: 518, 0,85: 68,
0,50: 22). Saklı skorların hepsi 5 · f(r) · K(bugünkü sınıf) ile tutarlı.

| Seçenek | Ne yapılır | Sitedeki etkisi | Dayanağı / riski |
|---|---|---|---|
| **A · K'yı koru, not düş** | K değerleri aynı. Metodolojide K bölümüne 29.09 düzeltmesi: tablo bugünkü veriyle, örneklem dışı sonuç, K'nın ilkesel (doğrulanabilirlik) bir ayar olduğu açıkça. :511'deki satır güncellenir. Skor formülü notundaki "türetildi" düzeltilir. | Skor değişmez. Yalnız metodoloji metni. | K'nın değerleri (0,70 / 0,85 / 0,50) veriye değil yargıya dayanır. 608 skor bu yargıyı taşır. Ölçeklemenin neden %30 ve %15 olduğu açıklanamaz. |
| **B · K'yı 1'e çek** | S = 5 · f(r). Karşı taraf ve güncelleme kartta olgu/etiket olarak kalır (kanıt taraması §5'in "güncelleme çarpan değil etiket olmalı" önerisi). | 608 bildirimin S'i artar, ortalama 1,88 → 2,30. S kademesi 225'inde değişir (rutin → önemli 161, önemli → mega 48, rutin → mega 16). Rutin / önemli / mega etiketi, renk, filtre ve "En büyük iş" **değişmez** (24.09'dan beri r'den). Değişenler: detaydaki S, hisse ve özet medyan skorları, tepki panelinin akran grupları (S kademesiyle kuruluyor), metodoloji II–III. Kodda `skor.py` / `skor.ts` sabitleri, `tests/test_skor.py`, ardından `skor_yenile.py --yaz`. | En sade ve veriyle en uyumlu. Risk: ilk yıldaki örneklem içi K-H1 sonucu atılmış olur. Etiket bunu kullanıcıya olgu olarak taşır. |
| **C · Yalnız güncelleme eksenini kaldır** | 0,85 → 1,00, 0,50 → 0,70. Karşı taraf ekseni kalır. | 90 skor artar (68 + 22). Etkinin geri kalanı A gibi. | K-H3 hiçbir örneklemde sınanabilecek güçte değil; 0,50'nin dayanağı yok. Ama karşı taraf ekseninin de örneklem dışı dayanağı yok (K-H1 sınamada ters). A'dan güçlü değil, yarım adım. |
| **D · Kararı ertele, gücü artır** | 2020–24'ün ~2.040 "Yeni İş İlişkisi" bildiriminin detay sayfası çekilir, karşı taraf kural tabanlı sınıflanır. K-H1…K-H3 yedi yılda, yeni ön kayıtla. | Şimdilik yok. Metodoloji düzeltmesi yine gerekir. | K1 hattında bu olayların karşı taraf alanı yok (yalnız liste API'si). KAP'a ~2.040 istek, 2 sn aralıkla ~70 dk. LLM gerekmez. Maliyet ve risk D1-E'de. K-H1'de güç sınırdaydı. 2020–24 tek başına sınama yılının ~3 katı olay: MDE kabaca 1,5 → 0,9 puan (pay kümelenmesi yüzünden √n'den yavaş inebilir). |

## 7. Sapmalar

Hepsi sonuçlara bakılmadan karara bağlandı.

1. **Evren.** Görev "skor_gecerlilik ile aynı yoldan" ve "yayın evreni"
   diyor. `skor_gecerlilik` sorgusunda yayın süzgeci yok. Harita "yayın
   evreni" dediği için olaylar aynı sorgudan alınıp `akis`'e süzüldü.
   Süzgeçsiz hâl sağlamlık olarak raporlandı (§4), hüküm değişmiyor.
2. **K-H4 bütün hükmü.** Harita ikili farkları istiyor, birleştirme
   kuralı yazmıyor. Kural §2'de. Sonuç kurala bağlı değil: üç fark da
   sonuçsuz.
3. **K1 kurallarının örtüştüğü durum.** Aynı işaret, |t| < 1,96 ve MDE <
   ilk yıl etkisi: "tekrarlanmadı: etki daha küçük" seçildi. Yalnız iki
   yıl birlikte K-H1 ve K-H2'yi etkiliyor. Öbür okumayla ikisi "yön aynı,
   sonuçsuz: etki bu dönemde daha küçük" olurdu. Sınama hükümlerini
   etkilemiyor.
4. **"İlk yıl etkisi"** olarak haritadaki 19.09 rakamları kullanıldı.
   Bugünkü analiz yılının rakamları kullanılsaydı da sınama hükümleri
   aynı kalırdı (her birinde MDE bugünkü analiz etkisinden büyük).
5. **AV iki örneklemde.** Hücre tabloları §7 gibi CAR3'lü olaylar
   üzerinden, K-H4 sınavı AV'si olan bütün olaylar üzerinden. Fark en çok
   0,02.
6. **Mutabakat için 19.09 matrisi** (`data/ozellikler.csv`, 613
   bildirimin ticker'lı 612'si) ve 21.09 AV'sinin taklidi (hacim
   2025-09-07 → 2026-09-19'a kırpılarak) kullanıldı. İkisi de yayımlanan
   rakamları birebir üretiyor (M0, A0).
7. **Ön kayıtta olmayan iki okuma** raporlandı, hükme girmiyor: %95
   aralığı ve betimleme satırları (CAR1, CAR5 farkları; açık hücrelerde
   CAR3 − CAR1). Dönem farkı z'si K1 kurallarında var.

## 8. Sınırlar

- **Güç.** Güncelleme hücreleri küçük (açık 45–60, gizli 14–17). K-H3 ve
  K-H4 için MDE ilk yıl etkilerinin 1,4–7,5 katı. Bu veriyle, iki yılla
  da, sınanamazlar. K-H1 ve K-H2'de güç sınırda.
- **Tek para rejimi.** İki yıl da aynı sıkı para dönemi. 2020–24'te
  karşı taraf alanı yok (§6 D).
- **Sınıflama kural tabanlı** (`karsi_taraf.py`), "isim" tarafına yatık.
  Doğruluğu bu notta ölçülmedi. §3'teki düzeltme iki yılda ters yönde
  çalıştı: sınıflamadaki küçük değişiklikler hücre farklarını
  sürükleyebiliyor.
- **Tek CAR modeli** (EW piyasa modeli). Sınama yılı β = 1 ile
  ölçülmedi. İlk yılda model K-H1'i değiştirmedi.
- **Güncelleme tanımı** KAP şablonunun bayrağı (`guncelleme_mi`).
  `bildirim_bag`'deki "guncelleme" bağı (67 bildirim) ayrı bir tanım,
  kullanılmadı.
- **AV'nin sıfır noktası** (AS2) hücre farklarını ancak hacim oynaklığı
  hücreler arasında farklıysa etkiler. D1-P'nin sonucuyla okunmalı.
- **Çoklu sınama.** 4 hipotez × 2 örneklem, üç ikili fark, ikincil
  regresyon. Hüküm tek p değerinden değil, örneklem dışı desenden verildi.
