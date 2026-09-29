# Literatür taraması: bulgularımız nerede duruyor, yöntemimiz neyle karşılaşıyor (D1-L, 2026-09-29)

**Görev:** Araştırma haritası §6 D1-L (Y7).
**Yöntem:** Web taraması, 29.09.2026. Her kaynağın sayfası ya da PDF'i açıldı.
Erişim türü kaynakçada yazılı: *tam metin*, *özet*, *künye* (yalnız bibliyografik
kayıt) ya da *ikincil* (içerik başka bir açılmış kaynaktan). PDF'ler
scratchpad'e indirilip PyMuPDF ile metne çevrildi. LLM API'si, KAP isteği,
veritabanı yok. Yeniden üretim: kaynakçadaki bağlantılar.

**Kural:** Sayılar yalnız okunan metinden. Bizim hesabımız olan her sayı
"bizim hesap" diye işaretli. Doğrulanamayan künye alanı boş ya da
"doğrulanmadı".

## Özet

- **Duyuru günü getirisi olağan büyüklükte.** Kore'nin zorunlu "tek
  satış/tedarik sözleşmesi" açıklamasında duyuru günü +0,69 puan (6.072
  olay). ABD'de şirketler arası sözleşmede [−1, 0] +1,43, devlet
  sözleşmesinde +0,54. Bizim 3 günlük +0,72 … +1,66 aynı mertebede. Tanımlar
  farklı, birebir karşılaştırılamaz (§1).
- **Kore'de ertesi gün geri dönüş var, bizde 3 günlük toplam pozitif
  kalıyor.** Kore'de t+1 −0,24, t+2 −0,11. Günlük tablodan [0, +2] toplamı
  ≈ +0,34 (bizim toplama). Bizim C +0,72, A +1,66.
- **"Sızıntı yok" bulgumuz literatürde istisna.** Kore (t−2, t−1 anlamlı
  pozitif getiri), ABD (t−5 … t−2 pozitif), Avustralya madencilik ve BIST-30
  haberlerinde duyuru öncesi pozitif getiri raporlanıyor. Türkiye'de KAP
  imza zaman damgasıyla gün içi ön işlem de bulunmuş. Bizim bulgumuz hacim
  tabanlı ve günlük; getiri tabanlı ön-CAR ölçülmedi (§7).
- **"Büyük haber daha çok fiyatlanmıyor" literatürle çelişiyor.** ABD'de
  sözleşmenin varlığa oranı, savunma ilanlarında piyasa değerine oranı
  getiriyle pozitif ilişkili. Madencilikte kaynak artışının yüzdesi de öyle.
  Tek karşı örnek zayıf: Kore'de oranı iki kat büyük KOSDAQ'ta tepki
  KOSPI'den küçük. Bizim sonuç güç sınırlı (MDE ~0,6 puan/S). Makalede açık
  bir gerilim olarak yazılmalı.
- **Gevşek parada iki kat tepki, iyimserlik literatürüyle uyumlu.**
  İyimser dönemlerde iyi habere fiyat duyarlılığı daha yüksek. Etki küçük,
  genç, oynak paylarda güçlü (Mian ve Sankaraguruswamy 2012).
- **Oynak tahtada zayıf/eksi tepki beklenen yönde.** Oynak, küçük, dolaşımı
  düşük paylar hem iyimserliğe en duyarlı hem manipülasyona en açık grup
  (Baker-Wurgler 2006; İmişiker-Taş 2013). Fiyat limitine kilitlenme fiyat
  keşfini geciktiriyor (Bildik-Gülay 2006).
- **AS2: Hacim ölçümüzün tasarımı literatürdeki üç standarttan hiçbirine
  uymuyor.** Standart, günlük hacmin logaritmasını alıp ortalamak (Campbell
  ve Wasley 1996; DellaVigna ve Pollet). Bu sıfır altında sapmasız. Bizim
  "ortalamanın logu − medyanın logu" sıfır altında pozitif sapma üretir.
  Hirshleifer, Lim ve Teoh'un "günün logu − ortalamanın logu" tasarımı ise
  negatif sapma üretir. Sapma yönleri bizim hesabımız (§3.1), literatürden
  değil. Bu sapmayı açıkça tartışan bir kaynak **bulamadım**.
- **Yöntem önerileri kimliklerle:** Rastgele gün plasebosu (Brown-Warner
  simülasyonu) literatürün standart aracı → Y1, AS2. Çok günlü sıra sınavı
  için GRANK (Kolari-Pynnönen 2011) → Y2. Alt kuyruk iddiaları için
  genelleştirilmiş işaret → Y2, S5. Seyrek işlem betası kısa pencerede
  sonucu değiştirmiyor → S4 düşük öncelik.

## 1. Sözleşme ve yeni iş duyuruları

### Karşılaştırma tablosu

Getiri puan (yüzde puanı), hacim log puanı ya da oran farkı. **Hiçbir satır
bizimkiyle birebir karşılaştırılamaz:** pencere, kıyas modeli, hacim birimi
ve taban dönemi farklı. Fark sütunu bunları yazıyor.

| Çalışma | Piyasa, dönem, n | Getiri ölçüsü ve pencere | Getiri etkisi | Hacim ölçüsü | Hacim etkisi | Bizimkinden fark |
|---|---|---|---|---|---|---|
| **KAP·RADAR K1** | BIST, 2020–2026, 3.091 | Piyasa modeli, eşit ağırlıklı BIST, Vasicek β; CAR [t0, t0+2] | Ort. A +1,66, B +0,85, C +0,72. Medyan +0,64 / +0,17 / +0,34. Pozitif pay %52–56 | ln(ort. adet [t0, t0+2]) − ln(medyan adet [t0−60, t0−11]) | A +%28,9, B +%22,0, C +%38,8 | — |
| Woo ve Park 2017 | Kore KOSPI + KOSDAQ, 2006–2016, 6.072 | Piyasaya göre düzeltilmiş (KOSPI / KOSDAQ endeksi), günlük AR | AR[0] +0,69 (t 15,1). AR[−2] +0,17, AR[−1] +0,32, AR[+1] −0,24, AR[+2] −0,11. [0, +2] ≈ +0,34 (bizim toplama) | Piyasa dışı devir hızına göre düzeltilmiş devir hızı oranı: sonraki 5 gün / önceki 5 gün | +%40,4 (t 13,8). 10/10 gün +%31,0 | Beta yok, değer ağırlıklı endeks. Hacim oranı log değil. Taban duyurudan hemen önceki 5 gün: sızıntı dönemini içeriyor |
| Elayan, Pukthuanthong, Roll 2005 (çalışma kâğıdı) | ABD, 1990–2000. Yüklenici 984 (şirketler arası), 1.963 (devlet) | Piyasa modeli, CRSP değer ağırlıklı, tahmin [−250, −91]; standardize kesitsel Z; [−1, 0] | Şirketler arası +1,43, devlet +0,54. Sözleşmeyi veren taraf +0,03 (anlamsız). Eşleşik 441 çift: +1,94 | — | — | Haber tarihi gazeteden: olay çoğunlukla t−1'de. 2 günlük pencere. Büyük şirket ağırlıklı |
| TenderAlpha–HKU 2026 (sektör raporu) | ABD'de işlem gören savunma yüklenicileri, 2010–2025, 16.491 | Piyasaya göre; duyurudan **sonraki** kapanıştan itibaren 3 gün | Eşit ağırlıklı +0,04 (t 1,2). Piyasa değerine göre en büyük %5: +0,28 (t 2,18) | — | — | Duyuru günü tepkisini ölçmüyor, sonraki sürüklenmeyi ölçüyor. Hakemsiz |
| Yang, Lu, Zhou 2014 | Çin A payı, 2001–2012, 318 | Olay çalışması | Pozitif ve anlamlı; satış sözleşmesi > alım; ölçek etkisi pozitif. **Sayılar doğrulanmadı** (yayıncı sayfası 403) | — | — | Yalnız künye açıldı |
| Eyüboğlu ve Bulut 2016 | BIST-30, 2003–2012, 532 "operasyonel" haber | BIST-100'e göre düzeltilmiş, AAR | t0: 0,050 (t 3,47); metin "%5" diyor. **Birim doğrulanmadı**, büyük şirketler için olağandışı büyük | — | — | Tedarik anlaşması, kapasite artışı, yeni ürün ve işten çıkarma aynı sınıfta |
| DellaVigna ve Pollet 2005 (kıyas: kazanç duyurusu) | ABD | — | — | ort. ln(TL hacim) [olay günleri] − ort. ln(TL hacim) [−20, −11] | Cuma dışı: t0 %45, t+1 %58 | Başka olay türü. Hacim ölçüsünün ölçeği için |

### Okuma

- **Duyuru günü.** Kore ve ABD'deki tek-iki günlük tepki bizim 3 günlük
  tepkimizle aynı mertebede. Kore'de tepki t0'da yoğun, ertesi gün kısmen
  geri veriliyor. Yazarlar bunu "bilgi hızla emiliyor" diye okuyor. Bizde
  C'de 3 günlük toplam Kore'nin iki katı. Kıyas modeli farkı (piyasaya göre
  düzeltme, beta yok) bunun bir kısmını açıklayabilir; ölçülmedi.
- **Duyuru öncesi.** Dört bağımsız çalışmada ön getiri pozitif:
  - Kore: t−2 +0,17 (t 3,6), t−1 +0,32 (t 6,7). Yazarlar içeriden
    bilgiyle işlem olasılığını tartışıyor.
  - ABD: "t−5 … t−2 tekdüze pozitif, toplamda anlamlı".
  - Avustralya madencilik: "birkaç gün önceden öngörülüyor".
  - BIST-30: hemen bütün haber türlerinde olay öncesi ACAR pozitif ve
    anlamlı.

  Bizim H2 ön **hacim**; temiz olaylarda yedi yıl −%0,8 (t −0,3). Ön
  **getiri** ölçülmedi. Çelişki ölçü farkından da gelebilir (§7).
- **Hacim.** Kore'de sonraki 5 gün önceki 5 güne göre +%40. Bizim +%22 …
  +%39 ile aynı yönde. Ama Kore tabanı sızıntı günlerini içeriyor, bizim
  taban son 10 günü dışarıda bırakıyor. Kore hacmi log değil, oran.
- **Büyüklük.** Literatür büyüklüğün tepkiyi büyüttüğünü söylüyor:
  - Elayan vd.: sözleşme / varlık oranının katsayısı pozitif, anlamlı.
    Küçük yüklenici daha büyük sürpriz.
  - TenderAlpha: mutlak tutarla ayrışma zayıf; piyasa değerine
    oranlayınca en büyük %5 anlamlı. Rapor "önemlilik şirkete göre" diye
    okuyor.
  - Bird vd.: kaynak artışının yüzdesi büyüdükçe anormal getiri büyüyor.
  - Yang vd.: "ölçek etkisi" pozitif (doğrulanmadı).
  - Karşı örnek (zayıf): Kore'de sözleşme/hasılat KOSDAQ'ta %45,0,
    KOSPI'de %21,4. Tepki KOSPI'de daha büyük (+0,72 / +0,67). Şirket
    büyüklüğü karışık.

  Bizim Bulgu 3/11 (skor getiriyi öngörmüyor) bu çizgiye karşı. Güç de
  sınırlı: CAR3 ~ S eğiminde MDE ~0,6 puan/S.
- **Kore şablonu KAP'a en yakın örnek.** Zorunluluk eşiği hasılatın %5'i
  (KOSPI; büyük şirkette %2,5) ve %10'u (KOSDAQ). Eşik altı "gönüllü"
  açıklama ayrı bir kategori (KCMI 2013, dört yıllık örneklem: KOSDAQ'ta
  gönüllü 4.090, zorunlu 3.691 bildirim). KAP'ta böyle bir eşik yok; bizim r dağılımımız bu yüzden
  daha aşağıya uzanıyor (%0,25 tabanı).
- **Tayvan ve ASX'te sözleşme duyurusuna özgü bir çalışma bulamadım.**
  Avustralya için en yakın örnek madencilik kaynak duyuruları.

## 2. Borsa İstanbul

| Kaynak | Konu | Bulgu | Bizim için |
|---|---|---|---|
| Şimşir ve Şimşek 2022 | KAP'a e-imzalı yükleme ile yayın arasındaki süre, 2009–2017 | Yükleme ile yayın arasında anormal işlem var. Sonraki tepki pozitifse en güçlü; zayıf yönetişimli şirketlerde güçlü | H2 günlük ölçüyle bu gün içi ön işlemi göremez. Y6 |
| Ersan, Şimşir, Şimşek, Hasan 2021 | KAP duyurularına fiyat uyum hızı | Türkiye'de tepki gelişmiş piyasalardan yavaş. İyi habere daha hızlı. Olay güdümlü stratejilerde kâr fırsatı | [t0, t0+2] penceresinin gerekçesi; Y5 (sürüklenme) |
| Yılmaz, Aksoy, Çelik 2020 | Finansal rapor bildirim kuralları, 2003–2017 | Küçük şirketlerde anormallik büyük. Aynı gün bildirim sayısı anormal getiriyi etkiliyor. Cuma tepkisi farklı. XBRL etkisiz | Y6: aynı gün yığılma ve Cuma BIST'te var |
| Yılmaz 2022 | Pazartesi etkisi ve KAP bildirimlerinin gün dağılımı, 2020–2021 | Şirketler Cuma ve hafta sonu diğer günlerden daha çok KAP bildirimi yapıyor | Y6: Cuma seçimi rastgele değil |
| Eyüboğlu ve Bulut 2016 | BIST-30, 2.143 haber, 2003–2012 | En güçlü tepki operasyonel haberde; olay öncesi ACAR'lar pozitif ve anlamlı | §1 tablosu; H2 çelişkisi |
| Bildik ve Gülay 2006 | Fiyat limitleri, İMKB | Limitler oynaklık yayılımı, gecikmiş fiyat keşfi ve işlem engeli üretiyor. Kanıt limitte **kilitlenme** günlerinde daha güçlü | S9 (tabanda kilitli tahtalar), S5 |
| Aktaş, Kryzanowski, Zhang 2022 | Fiyat limitleri, BIST-50, saniyelik veri | Mıknatıs etkisi; limit olaylarında bilgi asimetrisi artıyor | S5, S9 |
| İmişiker ve Taş 2013 | Manipülasyon, 1998–2006 | Küçük, dolaşımı düşük, borçlu şirketler manipülasyona yatkın; manipüle edilen pay yeniden edilme olasılığı yüksek | Bulgu 12, fon kolu (S7, S8) |
| İmişiker, Özcan, Taş 2015 | Aracı kurum işlemleri, 2003–2006 | İşlemlerin önemli bir kısmı pompala-boşalt ile tutarlı | S8 parmak izi |
| Gemici, Cihangir, Yakut 2017 | SPK'nın tespit ettiği 273 işlem bazlı manipülasyon, 2001–2014 | Manipülasyon öncesi/sırası/sonrasında getiri, hacim, oynaklık, devir hızı farklı; getiri ve oynaklık en ayırt edici | S8 |
| Gemici ve Polat 2019 | 28 manipülasyon duyurusu, 2016–2018 | Duyurular getiriyi anlamlı etkiliyor | S7 (doğal deney) |
| Özdemir 2026 | BIST-100 hacim şokları (z ≥ 2), 2017–2025, 3.233 olay | Holm düzeltmesinden sonra tam örneklemde CAR anlamsız; eksi getirili şoklardan sonra anlamlı eksi CAR. Gece getirisi +%1,227, gün içi −%0,293 | Y8 için BIST'te çoklu sınama düzeltmesi örneği; Y6 (seans dışı) |

- **"Yeni İş İlişkisi" şablonuna özgü bir akademik çalışma bulamadım.**
  DergiPark'ta KAP özel durum açıklamaları üzerine çalışmalar var, ama
  sözleşme/ihale duyurularını ayrı ele alan yok. Bu, makalenin katkısı
  olarak yazılabilir. **YÖK Tez'i tarayamadım** (arama arayüzü betikle
  çalışıyor); boşluk açık.
- **VBTS ve devre kesiciye dair akademik çalışma bulamadım.** Kore'nin
  benzeri "단기과열 종목 지정" (kısa vadeli aşırı ısınma) üzerine bir çalışma
  var: Jeong ve Noh 2016. Bulgu: Kore'deki ölçü fiyat büyük ölçüde
  yükseldikten sonra devreye giren sonradan bir tedbir. Belirlemeden sonra
  CAR biraz düşüp duruluyor. Bu, oynak tahtadaki eksi tepkinin geri dönüş
  okumasıyla (S5) uyumlu. Kanıt değil.
- **Fiyat marjı rejimi ölçülen tepkiyi değiştirebiliyor.** Kore Haziran
  2015'te marjı ±%15'ten ±%30'a çıkardı. Sonrasında duyuru günü AR KOSDAQ'ta
  arttı, KOSPI'de azaldı (Woo ve Park 2017, Panel B/C). BIST'te marj 13 Mart
  2020'ye kadar ±%20'ydi (K1 §2); değişiklik A döneminin başında. → S10.

## 3. Yöntem

### 3.1 Anormal hacim tanımları (AS2, S3, Y1)

| Kaynak | Tanım | Taban | Sıfır altında beklenti (bizim hesap) |
|---|---|---|---|
| Campbell ve Wasley 1996; Ajinkya ve Jain 1989 (ikincil: Yezegel 2009) | Günlük V = log(100 · adet / dolaşımdaki pay + 0,000255); piyasa modeli artığı | Tahmin dönemi | 0 (günlük log, sonra toplanıyor) |
| DellaVigna ve Pollet 2005 | ort. ln(TL hacim) olay günleri − ort. ln(TL hacim) [−20, −11] | Log'ların ortalaması | 0 |
| Hirshleifer, Lim, Teoh 2006 (çalışma kâğıdı) | ln(TL hacim_gün + 1) − ln(ort. TL hacim [−41, −11] + 1); 2 günlük sürümde ln(ort. [0, 1]) | Ortalamanın logu | **Negatif** (σ = 0,6'da tek gün ≈ −0,17, 2 gün ≈ −0,09) |
| Woo ve Park 2017 | Devir hızı oranı (sonra / önce), piyasa oranı çıkarılarak | Önceki 5–10 gün | Log değil; oranın beklentisi 1'den büyük (bizim hesap değil, genel Jensen) |
| **KAP·RADAR AV** | ln(ort. adet [t0, t0+2]) − ln(medyan adet [t0−60, t0−11]) | Medyanın logu | **Pozitif** (σ 0,5 / 0,6 / 0,7'de ≈ +0,08 / +0,11 / +0,15) |

- **Sıfır altı sapma sütunu bizim hesabımız, literatür değil.** Günlük
  hacim bağımsız log-normal varsayımıyla 200.000 tekrarlı simülasyon
  (scratchpad). Delta yöntemiyle yaklaşık: (σ²/2) − (e^σ² − 1)/(2n), n = 3.
  Haritadaki kaba hesapla (+0,08 … +0,14) aynı. Günler arası korelasyon ve
  log hacmin çarpıklığı bunu değiştirir. **Ölçüm D1-P'nin işi.**
- **Doğrudan bu asimetriyi tartışan kaynak bulamadım.** En yakın üç ipucu:
  - **Eventus kılavuzu iki sırayı adıyla ayırıyor:** "log relative volume"
    (her pay önce log, sonra ortalama) ve "relative volume log" (ortalama,
    sonra log). Hangisinin sapmalı olduğunu tartışmıyor.
  - **Log dönüşümünün gerekçesi normallik ve güç** (Ajinkya ve Jain;
    Cready ve Ramanan 1991; ikincil). Günlük logdan sonra toplamak
    literatürün varsayılanı.
  - **Hacim ölçüleri birbirini tutmuyor.** Kang ve Lim 2021: altı yöntem
    aynı payın aşırı hacim gününü %5,9 ile %66,4 arasında farklı
    sınıflıyor.
- **Sonuç:** Bizim ölçü tanımı gereği pozitif sapma taşıyor. Hirshleifer
  tipi ölçü tersine negatif taşıyor. Literatürle karşılaştırırken bu fark
  yazılmalı. D1-P'nin P4'ündeki AV_log, DellaVigna-Pollet ve
  Campbell-Wasley'nin tanımıyla aynı aileden. Ana ölçü seçimi ayrı karar.
- **S3 (devir hızı):** Campbell-Wasley ve Woo-Park dolaşımdaki paya oranlı
  hacim kullanıyor. Bizim AV pay içi bir oran. Pay sayısı taban ile olay
  arasında değişmedikçe (bedelsiz, bölünme) adet ile devir hızı aynı sonucu
  verir (bizim çıkarım). Fark kesitsel karşılaştırmada ve sermaye işlemli
  olaylarda çıkar. K1 bu olayları hacim sınavından zaten dışlıyor.

### 3.2 Plasebo: rastgele gün simülasyonu (Y1, AS2)

- **Brown-Warner simülasyonu literatürün standart aracı** (Kothari ve Warner
  2006). Rastgele paylar ve rastgele tarihler seçilir. Doğru ölçü bu
  örneklerde ortalama sıfır verir. Sınavın sıfır altında ne sıklıkta
  reddettiği buradan ölçülür. Güç de yapay etki eklenerek ölçülür. D1-P'nin
  tasarımı tam bu.
- **Kothari ve Warner'ın iki uyarısı D1-P için doğrudan geçerli:**
  - Sınavların özellikleri takvim dönemine ve örneklemin oynaklığına göre
    değişiyor. Tabakalı örneklem öneriyorlar. → Plasebo sonuçları dönem
    (A, B, C) ve V90 tabakasına göre ayrı raporlanmalı (Y1, S5).
  - Olayla varyans artışı, sınavları fazla reddettirir. → §3.3.
- Campbell ve Wasley 1996 ve Cready ve Ramanan 1991 hacim ölçülerini aynı
  simülasyon çerçevesinde sınamış. Ayrıntılı ret oranları metinlerine
  erişemediğim için aktarılamadı.

### 3.3 Sınavlar (Y2)

| Sınav | Ne düzeltiyor | Kaynak ve erişim | Öneri |
|---|---|---|---|
| BMP (standardize kesitsel) | Olayla gelen varyans artışı | BMP 1991 (künye); içerik Eventus kılavuzu, Dutta 2014, Kothari-Warner | D1-P planındaki gibi. Varyans artışının bütün paylarda aynı olduğunu varsayar (Dutta) |
| Kolari-Pynnönen 2010 | Olay tarihi kümelenmesinde kesitsel korelasyon. Düşük korelasyon bile ciddi fazla ret üretiyor | Özet | Birincil sağlamlık sınavı olarak doğru seçim. Bizde olaylar hafta içinde kümeleniyor |
| Genelleştirilmiş işaret (Cowan 1992) | Sıfır hipotezinde pozitif oranı 0,5 değil, tahmin dönemindeki oran | İkincil (Eventus, Dutta) | Varyans artışında da iyi tanımlı. Seyrek işlemde **alt kuyrukta** en iyisi (Cowan-Sergeant 1996) → Bulgu 12'nin eksi iddiası için (Y2, S5) |
| Corrado sıra sınavı | Normal olmayan dağılım | İkincil | Tek gün için. Varyans artarsa bozulur (Cowan-Sergeant) |
| Çok günlü sıra: Cowan 1992 / Campbell-Wasley 1993 | Günlük sıraları pencerede toplar | İkincil (Dutta; estudy2 belgesi) | Eventus bu uyarlamada günlük sıraları bağımsız varsayıyor. Seri bağımlılığı yok sayar |
| GRANK (Kolari-Pynnönen 2011) | CAR için genelleştirilmiş sıra; seri korelasyona ve olay oynaklığına dayanıklı; güç daha yüksek | Özet | **D1-P "hangi uyarlama" sorusuna öneri: GRANK.** Kullanılmazsa adıyla Cowan uyarlaması |
| Hall (1992) çarpıklık düzeltmeli sınav | Sağa çarpık CAR | İkincil (Eventus) | CAR3 sağa çarpık; ek sınav olarak (Y2) |

- **Gelişmekte olan piyasa kanıtı:** Corrado ve Truong 2008, Asya-Pasifik
  verisinde parametrik sınavların yanlış tanımlandığını buldu. En iyi
  sonuç: **eşit ağırlıklı endeksle** piyasa modeli artıkları üzerinde
  sıra ve işaret sınavları. Bizim kıyas seçimimizi (eşit ağırlıklı BIST)
  destekliyor ve Y2'yi güçlendiriyor.
- **Seyrek işlem (Cowan ve Sergeant 1996):** Standart standardize yaklaşım
  seyrek işlem gören paylarda kötü. BMP üst kuyrukta doğru ama güçsüz.
- **Çok günlü CAR'da kesitsel korelasyon uzun ufukta t'yi şişirir.**
  Kothari-Warner'ın örneği: ortalama ikili korelasyon 0,02, n = 100 ise
  standart hata 1,73 kat küçük görünür. Takvim zamanlı portföy öneriyorlar.
  → Y5.

### 3.4 Seyrek işlem betası (S4)

- Eventus kılavuzu Campbell-Wasley (1993) ve Cowan-Sergeant (1996) adına
  aktarıyor: günlük veri ve kısa pencerede sınav tanımı ve gücü
  Scholes-Williams ile OLS arasında duyarsız.
- El Ghoul vd. 2022: Dimson düzeltmesi kısa pencereli olay çalışmalarında
  uzun ufuktakinden daha önemli.
- **Öneri:** S4 düşük öncelik. Ucuz bir sağlamlık satırı yeter
  (Dimson, 1 gecikme, 1 öncül). Sonucu değiştirmesi beklenmiyor.

### 3.5 Çoklu sınama (Y8)

Romano-Wolf ya da BH üzerine olay çalışması kaynağı açmadım. BIST
bağlamında Özdemir 2026 Holm düzeltmesi kullanıyor ve düzeltme sonucu
değiştiriyor (tam örneklem CAR anlamsızlaşıyor). Y8 için örnek, yöntem
kaynağı değil.

## 4. Karşı taraf ve müşteri kimliği (AS1, D1-K)

- **Gizlilik rasyonel bir tercih olabilir.** Ellis, Fee, Thomas 2012:
  büyük müşteri bilgisini açıklamama kararı rakibe bilgi verme maliyetiyle
  açıklanıyor. Gizli karşı taraf kendiliğinden "az güvenilir" demek değil.
- **Doğrulanabilir bilgi iyi habere inanılırlık katıyor.** Hutton, Miller,
  Skinner 2003: kötü haber tahmini her zaman bilgilendirici; iyi haber
  tahmini yalnız doğrulanabilir ileriye dönük açıklamayla birlikteyse.
  K'nın mantığını (açık karşı taraf = doğrulanabilir) destekleyen en yakın
  kaynak. Konu kazanç tahmini, sözleşme değil.
- **Gizlilik içeriden satışla ilişkili olabilir.** Huang, Bai, Luo 2024
  (Çin, gönüllü müşteri açıklaması): müşteriyi gizleyen şirketlerde
  içeriden satış daha kârlı. İçeriden kişiler kişisel işlem güdüsüyle
  gizliyor olabilir. → D1-K'ya bir alternatif okuma; içeriden işlem verisi
  bizde yok.
- **Sözleşmeyi veren tarafın tepkisi yok.** Elayan vd.: veren taraf +0,03
  (anlamsız), yüklenici +1,43. KAP'ta karşı taraf çoğunlukla halka açık
  değil; yalnız yüklenici tarafı ölçülebilir.
- **Düzenleyiciler gizliliği bir risk işareti sayıyor:**
  - Kore (Kasım 2024): karşı taraf ve tutarın **ikisi birden** gizlenemez.
    Gizleyen, bildirime yatırımcı uyarısı yazar. Sözleşme feshedilir ya da
    ilk tutarın %50'sinden azı yerine getirilirse şirket "özensiz açıklama"
    ile işaretlenir. KOSDAQ'ta bu türün ihlal payı 2020'de %6,2, 2021'de
    %21,2.
  - Çin (CSRC Hunan 2017): "hayali büyük sözleşme" uyarısı. Örnek:
    dört yıllık hasılatı kadar 2 milyar yuanlık sipariş duyurusu, 1 milyon
    yuanı gerçekleşti. Yatırımcıya karşı tarafı doğrulama tavsiyesi.
- **Öneriler:**
  - AS1 / D1-K: Literatür K'nın yönünü (gizli = daha az inanılır) ne
    doğruluyor ne yalanlıyor. Hutton vd. yönü destekliyor, Ellis vd.
    gizliliğin masum sebebini veriyor. K'nın ampirik sağlaması D1-K'ya
    bırakılmalı.
  - Y4 ve S6: Kore'nin "fesih ya da %50 altı gerçekleşme açıklanır" kuralı,
    güncelleme ve düzeltme bildirimlerini ayrı sınamak için bir model.
  - S12: Kore ve Çin kaynaklarının ikisi de şişirilmiş tutarı düzenleyici
    sorunu olarak anıyor. KDV dahil tutar ve tekrarlar aynı ailede.

## 5. Rejim ve iyimserlik

- **Mian ve Sankaraguruswamy 2012:** İyimserlik yüksekken iyi kazanç
  haberine fiyat duyarlılığı daha yüksek, kötü habere daha düşük. Etki
  küçük, genç, oynak, temettü dağıtmayan paylarda güçlü. **Bizim A'daki
  iki kat tepkiyle uyumlu.** Gevşek para ve bireysel akın dönemi
  iyimserliğin yüksek olduğu dönem. Bizim örneklem de küçük paylardan
  oluşuyor.
- **Baker ve Wurgler 2006:** İyimserlik, değerlemesi öznel ve arbitrajı zor
  paylarda (küçük, genç, oynak, kârsız, temettüsüz) en büyük etkiyi yapıyor.
  Yüksek iyimserlikten sonra bu paylar düşük getiri veriyor. → Bulgu 12 ve
  Y5 (geri dönüş).
- **Baker, Wurgler, Yuan 2012:** Küresel ve yerel iyimserlik; özel sermaye
  akımları yayılma kanalı. → Yabancı akımı BIST rejimleri için bir vekil
  adayı.
- **Titman, Wei, Zhao 2021:** Çin'de "şüpheli" bölünmelerden sonra fiyat
  geçici sıçrıyor, sonra bölünme öncesinin altına iniyor. Bireysel
  yatırımcı alıyor; bilgili yatırımcı duyurudan önce girip sonra çıkıyor;
  içeriden kişiler satıyor. → 2023 bedelsiz dalgası ve S8 için benzer
  mekanizma.
- **K1 "piyasa havası" sınaması iyimserlik ölçmüyor.** Limit günü payı bir
  hareketlilik ölçüsü. Literatürdeki iyimserlik vekilleri (halka arz ilk gün
  getirisi, işlem hacmi, akımlar) K1'de denenmedi. Haritada kimliği yok;
  Dalga 2'de yeni kimlik olarak önerilir (Y7'nin çıktısı).
- **Yüksek enflasyon ve gelişmekte olan piyasada duyuru tepkisine dair
  doğrudan bir kaynak açamadım.** Boşluk.

## 6. Dikkat sınırlılığı (Y6)

- **DellaVigna ve Pollet 2009:** Cuma kazanç duyurularında anlık tepki %15
  düşük, gecikmiş tepki %70 yüksek, hacim %8 düşük.
- **Hirshleifer, Lim, Teoh 2009:** Aynı gün başka şirketlerin çok duyurusu
  varsa anlık fiyat ve hacim tepkisi zayıf, sonraki sürüklenme güçlü.
  Sektör dışı haber ve büyük sürprizler daha çok dikkat dağıtıyor.
- **Michaely, Rubin, Vedrashko 2016:** Seçim yanlılığı düzeltilince Cuma
  etkisi kayboluyor. Cuma duyuran şirketler her gün daha zayıf tepki
  alıyor; ortak gözlenmeyen özellikleri var.
- **deHaan, Shevlin, Thornock 2015:** Yöneticiler kötü haberi seans
  sonrasına, yoğun günlere ve kısa haberli tarihlere koyuyor; o
  koşullarda dikkat gerçekten düşük. Cuma'da dikkat düşüşü yok.
- **BIST:** Şirketler Cuma ve hafta sonu daha çok bildirim yapıyor (Yılmaz
  2022). Finansal raporlarda aynı gün bildirim sayısı ve Cuma tepkiyi
  etkiliyor (Yılmaz vd. 2020).
- **Seans dışı:** TenderAlpha savunma ilanlarının çoğunun seans dışında
  yapıldığını ve seans sonrası ilanların ertesi kapanışla girildiğini
  yazıyor. Bizim t0 kuralı (18:10) aynı mantık.
- **Y6 tasarım önerileri:**
  - Cuma karşılaştırması **şirket içi** yapılmalı (pay sabit etkisi ya da
    aynı şirketin Cuma ve diğer gün bildirimleri). Yoksa Michaely vd.'nin
    seçim yanlılığı sonucu üretir.
  - Aynı gün yığılma: o gün KAP'taki toplam özel durum açıklaması sayısı.
    Hirshleifer vd.'deki gibi diğer şirketlerin duyuruları; bizim H5
    şirketin **kendi** diğer açıklamalarını sayıyordu, bu farklı bir ölçü.
  - Seans içi / sonrası: KAP zaman damgası zaten var. Şimşir ve Şimşek'in
    e-imza zaman damgası verisi bizde yok.

## 7. Makale için öneriler

| İddia (metodoloji) | Literatür | Hüküm | Nereye | Kimlik |
|---|---|---|---|---|
| Bildirim günü hacim artıyor (Bulgu 1) | Kore +%40 (sonra/önce devir hızı); Beaver ve Kim-Verrecchia zaten atıflı | **Destekleniyor**, tanım farkıyla | IV Bulgu 1 ve rejim bölümüne Woo-Park kıyası | — |
| AV tanımı "kasıtlı asimetri" | Standart: günlük log sonra ortalama (Campbell-Wasley, DellaVigna-Pollet). Asimetri sıfır altında pozitif sapma (bizim hesap) | **Literatürden sapıyor.** Gerekçe metinde yok | II/IV "Ölçü" kutusuna not; D1-P sonucu gelince net değer | AS2, Y1 |
| Ortalama 3 günlük tepki pozitif (H3) | Kore t0 +0,69, ABD [−1, 0] +1,43 / +0,54 | **Destekleniyor**, büyüklük olağan | Rejim bölümü, bir cümle ve tablo | — |
| Sızıntı yok (Bulgu 2 düzeltmesi) | Kore, ABD, Avustralya, BIST-30'da ön getiri pozitif; KAP'ta gün içi ön işlem (Şimşir-Şimşek) | **Çelişiyor gibi.** Bizimki hacim tabanlı ve temiz olaylarda. Ön-CAR [t0−4, t0−1] ölçülmeden "yok" demek fazla | Bulgu 2 metnine "hacim ile ölçüldü; getiri ve gün içi ölçülmedi" | H2'nin getiri ayağı (kimlik yok; Y1 plasebosuna eklenebilir), Y6 |
| Büyüklük skoru getiriyi öngörmüyor (Bulgu 3/11) | ABD'de göreli büyüklük pozitif; savunmada piyasa değerine oran pozitif; madencilikte yüzde artış pozitif | **Çelişiyor.** Güç sınırlı; skor getiri tahmini iddia etmiyor ama "büyük haber daha çok fiyatlanmıyor" cümlesi literatüre karşı | IV Bulgu 3'e gerilim notu ve MDE; Sınırlar'a | S1 (2020–24 tutar çıkarımıyla güç artar) |
| Gevşek parada tepki iki kat | Mian-Sankaraguruswamy; Baker-Wurgler | **Destekleniyor** (mekanizma sınanmadı) | Rejim bölümü | Yeni kimlik önerisi (iyimserlik vekili) |
| Oynak tahtada zayıf/eksi tepki (Bulgu 12) | Baker-Wurgler (oynak paylar), İmişiker-Taş (küçük, düşük dolaşım), Titman vd. (geri dönüş), Bildik-Gülay (kilitlenme), Kore aşırı ısınma tedbiri | **Destekleniyor**, mekanizma belirsiz | Bulgu 12 ve VII "mekanizma bilinmiyor" maddesi | S5, S9, Y5 |
| K çarpanı (gizli karşı taraf) | Hutton vd. yönü destekliyor; Ellis vd. gizliliğin masum sebebi; Huang vd. içeriden satış; Kore düzenlemesi | **Kararsız** | II "K" bölümüne üç atıf; ampirik hüküm D1-K'dan | AS1 |
| Eşit ağırlıklı endeks, piyasa modeli | Corrado-Truong 2008 | **Destekleniyor** | II/IV "kıyas endeksi" | Y2 |
| Standart hata pay × hafta kümeli | Kolari-Pynnönen 2010 (olay kümelenmesi fazla ret) | **Destekleniyor**; KP-BMP ek sınav | Çıkarım paragrafı | Y2 |
| "Yeni İş İlişkisi" şablonu üzerine ilk çalışma | DergiPark'ta şablona özgü çalışma bulunamadı | Katkı olarak yazılabilir, YÖK Tez taranmadan kesinleştirilmemeli | Giriş | Y7 |

**Kaynakçaya en değerli ekler (öncelik sırasıyla):** Woo ve Park 2017;
Elayan vd. 2005; Kothari ve Warner 2006; Campbell ve Wasley 1996;
DellaVigna ve Pollet 2009; Kolari ve Pynnönen 2010, 2011; Corrado ve Truong
2008; Mian ve Sankaraguruswamy 2012; Şimşir ve Şimşek 2022; Hutton vd. 2003;
Ellis vd. 2012.

## 8. Kaynakça

Erişim: **tam metin** (PDF ya da tam sayfa okundu), **özet** (özet sayfası
okundu), **künye** (yalnız bibliyografik kayıt; içerik başka kaynaktan),
**ikincil** (içerik başka bir açılmış kaynakta geçiyor; hangisi yazılı).

### 8.1 Sözleşme duyuruları

1. Woo, Min-Chul (우민철); Park, Soo-Chul (박수철) (2017). 중요 공시에 대한 시장반응: 단일판매 공급계약 공시를 대상으로 [Market Reactions to Major Disclosure: Focused on Contract for Sales or Supply Disclosure]. *경영연구* 32(1), 205–229. doi:10.22903/jbr.2017.32.1.205. https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002199510 — **tam metin** (KCI PDF). Not: KCI İngilizce özeti "2006–2011" diyor; tam metin tablosu 2006–2016, 11 yıl.
2. Son, Seong-jin (손성진) (2022). 단일판매·공급계약의 공시효과: 내부자 거래와 ESG 경영활동을 중심으로. Doktora tezi, Pukyong National University. https://m.riss.kr/search/detail/DetailView.do?p_mat_type=be54d9b8bc7cdb09&control_no=16a2d6b3f855fb48ffe0bdc3ef48d419 — **özet**.
3. Yang, Jin Young (2013). Continuous Disclosure Practices in the Korean Equity Market. *Capital Market Perspective* 5(2), Korea Capital Market Institute. https://www.kcmi.re.kr/kcmifile/webzine_content/perspective_eng/3445/webzinepdf_3445.PDF — **tam metin**.
4. Elayan, Fayez A.; Pukthuanthong, Kuntara; Roll, Richard (2005). The Valuation Effect and Determinants of Corporate Contracting. Çalışma kâğıdı, 24.07.2005 taslağı. https://www.anderson.ucla.edu/documents/areas/fac/finance/20-05.pdf — **tam metin**. Yayımlanmış sürümü doğrulanmadı.
5. Yang, Jun; Lu, Wei; Zhou, Chunhui (2014). The immediate impact of purchasing/sales contract announcements on the market value of firms: An empirical study in China. *International Journal of Production Economics* 156, 169–179. doi:10.1016/j.ijpe.2014.06.002. https://api.crossref.org/works?query.bibliographic=The+immediate+impact+of+purchasing%2Fsales+contract+announcements — **künye** (Crossref). Özet ve sayılar açılamadı (ScienceDirect, ResearchGate 403).
6. TenderAlpha; HKU (2026). Defense Contract Announcements (Global; US Returns): Return Analysis. Sektör raporu, 10.01.2026. Yazar adları belgede yok. https://www.tenderalpha.com/wp-content/uploads/2026/02/White-Paper-Defense-Contract-Announcements-TenderAlpha-HKU-1.pdf — **tam metin**. Hakemsiz.
7. Rogerson, William P. (1989). Profit Regulation of Defense Contractors and Prizes for Innovation. *Journal of Political Economy* 97(6), 1284–1305. doi:10.1086/261654. https://ideas.repec.org/a/ucp/jpolec/v97y1989i6p1284-1305.html — **özet**. Borsa verisiyle 12 havacılık projesinin "ödül" değerini ölçüyor; duyuru tepkisi sayısı özette yok.
8. Bird, Ron; Grosse, Matthew; Yeung, Danny (2013). The market response to exploration, resource and reserve announcements by mining companies: Australian data. *Australian Journal of Management* 38(2), 311–331. doi:10.1177/0312896212473401. https://ideas.repec.org/a/sae/ausman/v38y2013i2p311-331.html — **özet**.
9. Eyüboğlu, Kemal; Bulut, Halil İbrahim (2016). Şirketlere Özgü Haberlerin Hisse Performansına Etkisi: BİST-30 Şirketleri Örneği. *Uluslararası İktisadi ve İdari İncelemeler Dergisi* (16), 113–138. https://dergipark.org.tr/tr/download/article-file/202106 — **tam metin**.

### 8.2 Borsa İstanbul

10. Şimşir, Şerif Aziz; Şimşek, Koray D. (2022). The market impact of private information before corporate announcements: evidence from Turkey. *Journal of International Financial Markets, Institutions and Money* 80, 101624. doi:10.1016/j.intfin.2022.101624. https://research.sabanciuniv.edu/id/eprint/44293/ — **özet**.
11. Ersan, Oğuz; Şimşir, Şerif Aziz; Şimşek, Koray D.; Hasan, Afan (2021). The speed of stock price adjustment to corporate announcements: Insights from Turkey. *Emerging Markets Review* 47. doi:10.1016/j.ememar.2020.100778. https://ideas.repec.org/a/eee/ememar/v47y2021ics1566014120305872.html — **özet**.
12. Yılmaz, Mustafa Kemal; Aksoy, Mine; Çelik, Tankut T. (2020). Market reaction to regulatory policy changes in financial statements filings: evidence from Turkey. *Eurasian Economic Review* 10(4), 567–605. doi:10.1007/s40822-020-00142-5. https://openaccess.ihu.edu.tr/entities/publication/0188288f-0b98-4be9-81ab-527073a29e5b — **özet**.
13. Yılmaz, Cihan (2022). Borsa İstanbul'da Pazartesi Sendromu: Getiri, İşlem Hacmi ve Kamuyu Aydınlatma Platformu Bildirimleri Çerçevesinde Bir İnceleme. *Uluslararası Muhasebe ve Finans Araştırmaları Dergisi* 4(2), 154–184. https://dergipark.org.tr/en/pub/ijafr/issue/76152/1192429 — **tam metin**. Not: PDF üstbilgisi "Aralık 2022", dergi sayfası 2023 gösteriyor.
14. Bildik, Recep; Gülay, Güzhan (2006). Are Price Limits Effective? Evidence from the Istanbul Stock Exchange. *Journal of Financial Research* 29(3), 383–403. doi:10.1111/j.1475-6803.2006.00185.x. https://ideas.repec.org/a/bla/jfnres/v29y2006i3p383-403.html — **özet**.
15. Aktaş, Osman Ulaş; Kryzanowski, Lawrence; Zhang, Jie (2022). Price-limit effectiveness: evidence from the Borsa Istanbul (BIST). *International Journal of Islamic and Middle Eastern Finance and Management* 15(3), 527–568. doi:10.1108/IMEFM-04-2020-0151. https://www.emerald.com/imefm/article-abstract/15/3/527/431096/Price-limit-effectiveness-evidence-from-the-Borsa — **özet**.
16. İmişiker, Serkan; Taş, Bedri Kamil Onur (2013). Which firms are more prone to stock market manipulation? *Emerging Markets Review* 16, 119–130. doi:10.1016/j.ememar.2013.04.003. https://ideas.repec.org/a/eee/ememar/v16y2013icp119-130.html — **özet**.
17. İmişiker, Serkan; Özcan, Rasim; Taş, Bedri Kamil Onur (2015). Price Manipulation by Intermediaries. *Emerging Markets Finance and Trade* 51(4), 788–797. doi:10.1080/1540496X.2015.1046349. https://ideas.repec.org/a/mes/emfitr/v51y2015i4p788-797.html — **özet**.
18. Gemici, Eray; Cihangir, Mehmet; Yakut, Emre (2017). Trade-Based Manipulation: The Case of Turkey. *Ege Academic Review* 17(3), 369–380. https://dergipark.org.tr/en/pub/eab/issue/39978/475187 — **özet**.
19. Gemici, Eray; Polat, Müslüm (2019). Manipülasyon Duyurularının Pay Senedi Getirileri Üzerindeki Etkisinin İncelenmesi. *Hacettepe Üniversitesi İİBF Dergisi* 37(3), 471–488. doi:10.17065/huniibf.437420. https://dergipark.org.tr/en/pub/huniibf/article/437420 — **özet**.
20. Özdemir, Kemal (2026). Borsa İstanbul'da Olağan Dışı İşlem Hacmi Artışları Sonrasında Kısa Vadeli Fiyat Davranışı. *İşletme Araştırmaları Dergisi* 18(3), 2684–2700. doi:10.20491/isarder.2026.2314. https://www.isarder.org/index.php/isarder/article/view/2695 — **özet**.
21. Jeong, Seong-hoon (정성훈); Noh, Sang-soo (노상수) (2016). 단기과열 종목 지정 공시가 주가에 미치는 영향: 3요인 모형을 이용하여. *자산운용연구* 4(2), 36–59. https://journal.kci.go.kr/capm/archive/articlePdf?artiId=ART002183138 — **tam metin** (özet ve giriş okundu). Latin harfli yazımı doğrulanmadı.

### 8.3 Yöntem

22. Kothari, S. P.; Warner, Jerold B. (2006). Econometrics of Event Studies. B. E. Eckbo (ed.), *Handbook of Corporate Finance: Empirical Corporate Finance*, Cilt A, Bölüm 1. Elsevier/North-Holland. 19.05.2006 taslağı. https://www.bu.edu/econ/files/2011/01/KothariWarner2.pdf — **tam metin**.
23. Campbell, Cynthia J.; Wasley, Charles E. (1996). Measuring Abnormal Daily Trading Volume for Samples of NYSE/ASE and NASDAQ Securities Using Parametric and Nonparametric Test Statistics. *Review of Quantitative Finance and Accounting* 6(3), 309–326. doi:10.1007/BF00245187. https://ideas.repec.org/a/kap/rqfnac/v6y1996i3p309-26.html — **özet**. Formül **ikincil** (Yezegel 2009; Eventus kılavuzu).
24. Yezegel, Ari (2009). *Three Essays on Stock Recommendations*. Doktora tezi, Rutgers University–Newark. https://rucore.libraries.rutgers.edu/rutgers-lib/26117/PDF/1/play/ — **tam metin**; Ajinkya-Jain, Cready-Ramanan ve Campbell-Wasley hacim formülü için ikincil kaynak.
25. Cowan Research (2007). *Eventus 8.0 User's Guide, Standard Edition 2.1*. A. R. Cowan. https://www.eventstudy.com/Eventus-Guide-8-Public.pdf — **tam metin**. BMP, genelleştirilmiş işaret, çok günlü sıra, Scholes-Williams, hacim sırası için ikincil kaynak.
26. Dutta, Anupam (2014). Parametric and Nonparametric Event Study Tests: A Review. *International Business Research* 7(12), 136 vd. doi:10.5539/ibr.v7n12p136. https://ccsenet.org/journal/index.php/ibr/article/download/38913/23293 — **tam metin**. Cowan 1992, Corrado, BMP için ikincil kaynak.
27. Kolari, James W.; Pynnönen, Seppo (2010). Event Study Testing with Cross-sectional Correlation of Abnormal Returns. *Review of Financial Studies* 23(11), 3996–4025. doi:10.1093/rfs/hhq072. https://econpapers.repec.org/RePEc:oup:rfinst:v:23:y:2010:i:11:p:3996-4025 — **özet**.
28. Kolari, James W.; Pynnönen, Seppo (2011). Nonparametric rank tests for event studies. *Journal of Empirical Finance* 18(5), 953–971. doi:10.1016/j.jempfin.2011.08.003. https://ideas.repec.org/a/eee/empfin/v18y2011i5p953-971.html — **özet**.
29. Cowan, Arnold R.; Sergeant, Anne M. A. (1996). Trading frequency and event study test specification. *Journal of Banking & Finance* 20(10), 1731–1757. https://ideas.repec.org/a/eee/jbfina/v20y1996i10p1731-1757.html — **özet**.
30. Corrado, Charles J.; Truong, Cameron (2008). Conducting event studies with Asia-Pacific security market data. *Pacific-Basin Finance Journal* 16(5), 493–521. doi:10.1016/j.pacfin.2007.10.005. https://ideas.repec.org/a/eee/pacfin/v16y2008i5p493-521.html — **özet**.
31. Kang, Min; Lim, Ji-Eun (2021). 비정상 거래량의 측정 방법론에 관한 연구 [Abnormal trading volume ölçüm yöntemleri]. *재무관리연구* 38(4), 147–173. doi:10.22510/kjofm.2021.38.4.006. https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002787306 — **özet**.
32. El Ghoul, Sadok; Guedhami, Omrane; Mansi, Sattar A.; Sy, Oumar (2022). Event studies in international finance research. *Journal of International Business Studies*. Cilt ve sayfa doğrulanmadı. https://pmc.ncbi.nlm.nih.gov/articles/PMC9264305/ — **tam metin**.

### 8.4 Karşı taraf

33. Ellis, Jesse A.; Fee, C. Edward; Thomas, Shawn E. (2012). Proprietary Costs and the Disclosure of Information About Customers. *Journal of Accounting Research* 50(3), 685–727. doi:10.1111/j.1475-679X.2012.00441.x. https://ideas.repec.org/a/bla/joares/v50y2012i3p685-727.html — **özet**.
34. Hutton, Amy P.; Miller, Gregory S.; Skinner, Douglas J. (2003). The Role of Supplementary Statements with Management Earnings Forecasts. *Journal of Accounting Research* 41(5), 867–890. doi:10.1046/j.1475-679X.2003.00126.x. https://ideas.repec.org/a/bla/joares/v41y2003i5p867-890.html — **özet**.
35. Huang, Wan; Bai, Yufan; Luo, Hong (2024). Customer identity concealing and insider selling profitability: Evidence from China. *Journal of Corporate Finance* 85, 102566. doi:10.1016/j.jcorpfin.2024.102566. https://ideas.repec.org/a/eee/corfin/v85y2024ics0929119924000282.html — **özet**.

### 8.5 Rejim ve iyimserlik

36. Mian, G. Mujtaba; Sankaraguruswamy, Srinivasan (2012). Investor Sentiment and Stock Market Response to Earnings News. *The Accounting Review* 87(4), 1357–1384. doi:10.2308/accr-50158. https://api.crossref.org/works?query.bibliographic=Investor+Sentiment+and+Stock+Market+Response+to+Earnings+News — **özet** (Crossref kaydındaki özet).
37. Baker, Malcolm; Wurgler, Jeffrey (2006). Investor Sentiment and the Cross-Section of Stock Returns. *Journal of Finance* 61(4), 1645–1680. doi:10.1111/j.1540-6261.2006.00885.x. https://ideas.repec.org/a/bla/jfinan/v61y2006i4p1645-1680.html — **özet**.
38. Baker, Malcolm; Wurgler, Jeffrey; Yuan, Yu (2012). Global, local, and contagious investor sentiment. *Journal of Financial Economics* 104(2), 272–287. doi:10.1016/j.jfineco.2011.11.002. https://ideas.repec.org/a/eee/jfinec/v104y2012i2p272-287.html — **özet**.
39. Titman, Sheridan; Wei, Chishen; Zhao, Bin (2021). Corporate Actions and the Manipulation of Retail Investors in China: An Analysis of Stock Splits. NBER Working Paper 29212. https://www.nber.org/papers/w29212 — **özet**. Dergi sürümü (JFE) künyesi doğrulanmadı.

### 8.6 Dikkat

40. DellaVigna, Stefano; Pollet, Joshua M. (2009). Investor Inattention and Friday Earnings Announcements. *Journal of Finance* 64(2), 709–749. doi:10.1111/j.1540-6261.2009.01447.x. https://ideas.repec.org/a/bla/jfinan/v64y2009i2p709-749.html — **özet**. Hacim tanımı ve %45 / %58 sayıları çalışma kâğıdından: *Investor Inattention, Firm Reaction, and Friday Earnings Announcements*, NBER WP 11683 (2005), https://www.nber.org/system/files/working_papers/w11683/w11683.pdf — **tam metin**. Dergi sürümünün tanımı aynı mı, doğrulanmadı.
41. Hirshleifer, David; Lim, Sonya Seongyeon; Teoh, Siew Hong (2009). Driven to Distraction: Extraneous Events and Underreaction to Earnings News. *Journal of Finance* 64(5), 2289–2325. doi:10.1111/j.1540-6261.2009.01501.x. https://ideas.repec.org/a/bla/jfinan/v64y2009i5p2289-2325.html — **özet**. Hacim tanımı 25.10.2006 çalışma kâğıdından: http://www.econ.yale.edu/~shiller/behfin/2006-11/hirshleifer.pdf — **tam metin**. Dergi sürümünün tanımı doğrulanmadı.
42. Michaely, Roni; Rubin, Amir; Vedrashko, Alexander (2016). Are Friday announcements special? Overcoming selection bias. *Journal of Financial Economics* 122(1), 65–85. doi:10.1016/j.jfineco.2016.05.006. https://ideas.repec.org/a/eee/jfinec/v122y2016i1p65-85.html — **özet**.
43. deHaan, Ed; Shevlin, Terry; Thornock, Jacob (2015). Market (in)attention and the strategic scheduling and timing of earnings announcements. *Journal of Accounting and Economics* 60(1), 36–55. doi:10.1016/j.jacceco.2015.03.003. https://ideas.repec.org/a/eee/jaecon/v60y2015i1p36-55.html — **özet**.

### 8.7 Yalnız künyesi doğrulanan klasikler (içerik ikincil)

İçerikleri yukarıdaki açılmış kaynaklardan aktarıldı; kendi özetleri ya da
metinleri açılamadı (IDEAS'ta özet yok, yayıncıda abonelik).

44. Brown, Stephen J.; Warner, Jerold B. (1980). Measuring security price performance. *Journal of Financial Economics* 8(3), 205–258. https://ideas.repec.org/a/eee/jfinec/v8y1980i3p205-258.html — **künye**; ikincil: Kothari-Warner.
45. Brown, Stephen J.; Warner, Jerold B. (1985). Using daily stock returns: The case of event studies. *Journal of Financial Economics* 14(1), 3–31. https://ideas.repec.org/a/eee/jfinec/v14y1985i1p3-31.html — **künye**; ikincil: Kothari-Warner, Eventus.
46. Boehmer, Ekkehart; Musumeci, Jim; Poulsen, Annette B. (1991). Event-study methodology under conditions of event-induced variance. *Journal of Financial Economics* 30(2), 253–272. https://ideas.repec.org/a/eee/jfinec/v30y1991i2p253-272.html — **künye**; ikincil: Eventus, Dutta.
47. Corrado, Charles J. (1989). A nonparametric test for abnormal security-price performance in event studies. *Journal of Financial Economics* 23(2), 385–395. https://ideas.repec.org/a/eee/jfinec/v23y1989i2p385-395.html — **künye**; ikincil: Eventus, Dutta.
48. Cowan, Arnold R. (1992). Nonparametric event study tests. *Review of Quantitative Finance and Accounting* 2(4), 343–358. — **ikincil** (künye Dutta 2014 ve estudy2 belgesinden: https://irudnyts.github.io/estudy2/reference/car_rank_test.html).
49. Ajinkya, Bipin B.; Jain, Prem C. (1989). The behavior of daily stock market trading volume. *Journal of Accounting and Economics* 11(4), 331–359. https://ideas.repec.org/a/eee/jaecon/v11y1989i4p331-359.html — **künye**; ikincil: Yezegel 2009.
50. Cready, William M.; Ramanan, Ramachandran (1991). The power of tests employing log-transformed volume in detecting abnormal trading. *Journal of Accounting and Economics* 14(2), 203–214. https://econpapers.repec.org/article/eeejaecon/v_3a14_3ay_3a1991_3ai_3a2_3ap_3a203-214.htm — **künye**; ikincil: Yezegel 2009.
51. Dimson, Elroy (1979). Risk measurement when shares are subject to infrequent trading. *Journal of Financial Economics* 7(2), 197–226. https://ideas.repec.org/a/eee/jfinec/v7y1979i2p197-226.html — **künye**; ikincil: El Ghoul vd.
52. Scholes, Myron; Williams, Joseph (1977). Estimating betas from nonsynchronous data. *Journal of Financial Economics* 5(3), 309–327. https://ideas.repec.org/a/eee/jfinec/v5y1977i3p309-327.html — **künye**; ikincil: Eventus.
53. Bamber, Linda Smith; Barron, Orie E.; Stevens, Douglas E. (2011). Trading volume around earnings announcements and other financial reports: Theory, research design, empirical evidence, and directions for future research. *Contemporary Accounting Research* 28(2), 431–471. doi:10.1111/j.1911-3846.2010.01061.x. https://pure.psu.edu/en/publications/trading-volume-around-earnings-announcements-and-other-financial-/ — **künye**. Hacim tasarımı için en kapsamlı derleme olabilir; içeriği okunmadı.

### 8.8 Kurumsal bağlam (hakemsiz)

54. 비즈워치 (Business Watch), 06.11.2024. 주가 흔드는 '단일판매‧공급계약'…공시 사전·사후 관리 강화한다. https://news.bizwatch.co.kr/article/market/2024/11/06/0008 — **tam metin** (haber).
55. 전자신문 (Electronic Times), 06.11.2024. 금감원-거래소 '단일판매·공급계약' 공시 기준 강화. https://www.etnews.com/20241106000161 — **tam metin** (haber).
56. 한경 경제용어사전: 단일판매·공급계약 체결 공시. https://dic.hankyung.com/economy/view/?seq=14327 — **tam metin** (sözlük maddesi).
57. 中国证监会湖南监管局 (CSRC Hunan), 30.10.2017. "违规信披"主题（三）：追求稳稳的幸福 警惕莫须有"重大合同". http://www.csrc.gov.cn/hunan/c105684/c1293764/content.shtml — **tam metin** (yatırımcı eğitimi notu).

## Ek: Sapmalar ve erişilemeyenler

- **Kaynak sayısı hedefin (20–40) üstünde.** Ana kaynak 43; 44–53 yalnız
  künye, 54–57 kurumsal bağlam. Künye satırları, içerikleri başka bir
  kaynaktan aktarıldığı için şeffaflık amacıyla ayrı listelendi.
- **Açılıp listelenmeyenler (konu dışı çıktı):** Mun ve Kwon 2010 (KCI,
  sözleşme duyurusu içermiyor), Çalış vd. 2024 (tahsisli sermaye
  artırımı), Samunderu ve Yordanova 2024 (zayıf dergi, 12 şirket), Brown
  2007 (Avustralya geri alımları), Xiao 2004 (Çin; sözleşme değil),
  EventStudyTools sayfaları (formül yok).
- **Erişilemeyen önemli kaynaklar:**
  - Yang, Lu, Zhou 2014 (Çin sözleşme duyuruları): özet ve sayılar 403.
  - Campbell-Wasley 1996, Cready-Ramanan 1991, Ajinkya-Jain 1989, BMP
    1991, Corrado 1989, Cowan 1992 tam metinleri (abonelik). Özellikle
    Campbell-Wasley ve Cready-Ramanan'ın sıfır altı ret oranları AS2 için
    değerli olurdu.
  - Karafiath 2009, "Detecting cumulative abnormal volume" (Applied
    Economics Letters 16(8)): çok günlü log devir hızı; açılamadı.
  - Bamber vd. 2011: künye açıldı, özet sayfada yok.
  - Tayvan ve ASX'te sözleşme duyurusuna özgü çalışma bulunamadı. Çince
    (CNKI) ve Tayvanca akademik veri tabanlarına erişilmedi.
  - YÖK Tez taranamadı.
  - Yüksek enflasyonda duyuru tepkisi: ilgili görünen "Inflation Surprise
    and Stock Returns: Türkiye During a Period of High Inflation" (2026,
    ScienceDirect) açılmadı.
