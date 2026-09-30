# Araştırma haritası: ne sınandı, ne sınanmadı, sıradaki dalgalar (2026-09-29)

**Durum: ARAŞTIRMA KAPANDI (2026-09-30).** Dalga 1 tamamlandı. Dalga 2 ve
3 yapılmayacak; proje ürün ve vitrin odağına döndü (§9). Aşağıdaki metin
29.09'daki hâliyle duruyor.

*(Önceki durum satırı: DALGA 1 TAMAMLANDI, 2026-09-29 akşamı. Dört notun
çıktısı ve yarın için bekleyen kararlar §8'de. D1-P ve D1-K'nın rakamları
betikler bağımsız olarak yeniden koşularak doğrulandı. Dalga 2, §8'deki
kararlardan sonra başlayacak.)*

*(İlk durum satırı: DALGA 1 BAŞLADI, 2026-09-29, Hüseyin: "haritayı yaz,
sonra dalga 1'i başlat".)* Bu belge iki işe yarıyor. Birincisi 19–28 Eylül
arasındaki araştırmanın envanteri. İkincisi Dalga 1 ajanlarının brifingi.
§6'daki tanımlar ve karar kuralları, sonuçlara bakılmadan önce yazıldı ve
commit'lendi.

## 1. Nasıl çalıştık

Dört aşama. Her biri bir öncekinin zayıf yerinden doğdu.

| Tarih | Aşama | Not | Ne öğretti |
|---|---|---|---|
| 19–23.09 | Keşif: 613 bildirim, tek yıl, Bulgu 1–12 | `2026-09-19-skor-kanit-taramasi.md`, metodoloji IV | Eşikler sonuç görüldükten sonra seçildi |
| 24.09 | Örneklem dışı: önceki 12 ay, 690 bildirim | metodoloji IV, commit `979b557` | Bulgu 7 ve 10 çöktü. İkisi de eşik denenerek kurulmuştu |
| 26–27.09 | Denetim ve arındırma | `2026-09-26-veri-denetimi.md`, `2026-09-27-gecerlilik-degerlendirmesi.md` | "Sızıntı" yorumu zayıfladı. 2024 paydası bozuktu |
| 28.09 | Ön kayıtlı rejim sınaması, 2020–2026 | `2026-09-28-k1-on-kayit.md`, `2026-09-28-k1-rejim-sinamasi.md` | Ana bulgular dönemin ürünü değil |

Döngü:

1. Bir itiraz ya da ürün kararı soruyu doğuruyor.
2. Not yazılıyor, seçenekler Hüseyin'e "K" kararı olarak gidiyor.
3. Onaydan sonra uygulanıyor.
4. Düzeltmeler tarihiyle metinde kalıyor, eski metin silinmiyor.

İlkeler:

- Point-in-time: payda, bildirimden önce yayınlanmış raporlardan.
- Önce LLM'siz ve bedava olan.
- Standart hata pay ve ISO hafta düzeyinde iki yönlü kümeli.
- Sonuçsuzlukta MDE (%80 güç, iki yönlü %5) raporlanır.
- Hüküm tek p değerinden değil, dönemler boyunca tekrarlanmadan.

**Ders:** Eşikle kurulan keşif bulguları (7, 10) çöktü. Eşiksiz ve ön
kayıtlı olanlar ayakta kaldı. Dalga planı (§5) bu derse göre kuruldu.

## 2. Sınananlar

| Konu | Hüküm | Kapsam | Kaynak |
|---|---|---|---|
| Bildirim günü hacmi (Bulgu 1) | Her rejimde artıyor: A +%28,9 (t 6,4), B +%22,0 (t 3,3), C +%38,8 (t 9,4) | 7 yıl | K1 §4 H1 |
| Ön hacim (Bulgu 2) | Tabana göre artış yok (temiz, 7 yıl −%0,8, t −0,3). Rastgele günlere göre +%4,9 (t 2,06). Sızıntı ne doğrulanıyor ne dışlanıyor | 7 yıl | K1 §4 H2, D1-P |
| Ortalama CAR3 | A +1,66 (t 4,9), B +0,85 (t 1,7), C +0,72 (t 3,3). Temiz olaylarda C +0,43 (t 1,70), 7 yıl +0,71 (t 3,77) | 7 yıl | K1 §4 H3, H5 |
| Oynak tahta (Bulgu 12) | Zayıf tepki genel (1 SS: A −0,70, C −0,85). Eksi ortalama yalnız C'de, fon yoğunluğuyla büyüyor | 7 yıl | K1 §4 H4, §5 |
| Skor getiri tahmini değil (Bulgu 3, 11) | Tekrarlandı | Yalnız C | metodoloji IV |
| Skor ~ hacim (Bulgu 4) | Kurulamadı. MDE ~0,068/S | Yalnız C | geçerlilik §4 |
| Taban (5), tavan (6) | Taban %1 → %0,25 düzeltildi; tavan işlevsiz, dokunulmadı | Yalnız C | metodoloji IV |
| Boyut yanlılığı (8) | Yok | Yalnız C | metodoloji IV |
| Beta (9) | β = 1 yanlış; piyasa modeli + Vasicek | C | metodoloji IV |
| Yorgunluk (7), tahta ayrışması (10) | Tekrarlanmadı, üründen çıkarıldı | 2 yıl | metodoloji IV |
| K çarpanı | Örneklem dışında dört iddianın hiçbiri tekrarlanmadı. Şeffaflık ayarı olarak yeniden konumlandı (§9) | 2 yıl | D1-K |
| Halka arz, ilk 30 gün | Ort. −%4,01, anlamsız (kümeli t −1,73) | C | metodoloji VII |
| Fonlar, niş kağıtlar | 10 pay çıkarılınca C bulguları duruyor; o paylarda AV +%20,2 | Yalnız C | K1 §5 |
| Piyasa havası | Ay tercillerinde fark yok (eğim t −0,1) | 7 yıl | K1 §5 |
| Aynı şirketler (57 pay) | Desen tam örneklemle aynı | 7 yıl | K1 §5 |
| Söz ve gerçek | Üst üçte bir +%20,8; ρ 0,24 (t 1,91) | Tek dönem | `2026-09-27-soz-ve-gercek.md` |
| Veri kalitesi | Altın küme %94; sahada 10 kesin hata; 18 aynı iş + 7 düzeltme bağlandı | C | veri denetimi |
| Kaynak | Bülten ve yfinance olay bazında 0,996 | C | K1 §3 |

## 3. Bu okumada çıkan iki açık sorun

**AS1 · K çarpanının sağlaması örneklem dışında ters.** Metodolojinin K
bölümü (`site/content/metodoloji.html:387`) "n ≥ 55 olan üç hücrede
anormal hacim sıralaması K sıralamasıyla birebir uyumlu" diyor. 24.09
örneklem dışı tablosunda (`:511`) aynı sağlama TERS: öbür yılda gizli +
ilk bildirim 0,397, açık + ilk 0,317. K bölümüne düzeltme notu düşülmedi,
K skorda aynen duruyor. K'nın 19.09'daki asıl gerekçesi (gizli karşı
tarafta tepkinin üçüncü günde sıfırlanması) öbür yılda raporlanmadı.
→ Dalga 1, D1-K.

**Sonuç (D1-K, 29.09):** Örneklem dışı yılda dört iddianın hiçbiri
tekrarlanmadı. Dördü de sonuçsuz, üçünde nokta tahmini ters. Asıl
gerekçe (açık + ilk > gizli + ilk, CAR3) −0,16 puan (t −0,29). İlk yıl
+1,21'di. Ayrıca 25.09'daki karşı taraf düzeltmesi (`bbac018`) ilk yılın
123 bildiriminin sınıfını değiştirdi. K = 0,50'nin tek dayanağı olan
−5,18 (n 6) kayboldu. Makalenin "birebir uyumlu" cümlesi bugünkü veriyle
ilk yılda bile doğru değil. Ayrıntı:
`2026-09-29-k-carpani-sinamasi.md`.

**AS2 · Hacim ölçüsünün sıfır noktası ölçülmedi.** AV = ln(ort. adet
[t0, t0+2]) − ln(medyan adet [t0−60, t0−11])
(`scripts/skor_gecerlilik.py:243`, kodda "kasıtlı asimetri"). Ortalamanın
logaritması logaritmaların ortalamasından büyük olduğu için, olay olmayan
günde de AV'nin beklentisi sıfırın üstünde. Kaba hesap (günlük ln adet
SS'si 0,5–0,7, günler bağımsız): +0,08 … +0,14. Günler arası korelasyon
bunu küçültür. Etkinin varlığını bozmaz: gün gün ölçülen profil (log
ortalaması, sapmasız) t0'da sıçrıyor, temiz ön hacim sıfır. Büyüklüğü ve
rejim karşılaştırmasını etkileyebilir, çünkü sapma hacmin oynaklığına
bağlı. **Tahmin, ölçülmedi.** → Dalga 1, D1-P.

**Sonuç (D1-P, 29.09): Tahmin büyük ölçüde yanlış çıktı.** Ortalamanın
logu kaynaklı sapma gerçekten var: +0,05 … +0,08 log. Ama günlük log hacim
sola çarpık, yani ortalaması medyanın altında. İki sapma birbirini
götürüyor. Olay yokken AV yedi yılda +%2,2 (t 1,03). Yalnız A1'de
(2020–21) anlamlı: +%11,3. Net etkiler: A +%27,4, B +%20,8, C +%33,9.
Hükümlerin hiçbiri değişmedi. Bunun yerine başka bir sıfır noktası
sorunu çıktı: günlük log ölçülerin (ön hacim) olaysız günde değeri
−%3 … −%5. Ayrıntı: `2026-09-29-plasebo-ve-sira-sinavlari.md`.

## 4. Sınanmayanlar

Kimlikler envanter (D1-E) ve sonraki ön kayıtlar içindir.

**Notlarda sınır olarak yazılı olanlar:**

| # | Soru | Nerede yazılı |
|---|---|---|
| S1 | Skor sınavları (Bulgu 3, 4, 5, 11) 2020–24'te. Tutar çıkarımı ~1,43 USD, onay bekliyor | K1 §8, §9 |
| S2 | "Özel Durum Açıklaması (Genel)" içindeki ~2.600 sözleşme duyurusu. Şablonu kullanmayanlar ölçülmedi | K1 §8 |
| S3 | Dolaşımdaki paya oranlı hacim (turnover) | metodoloji VII |
| S4 | Seyrek işlem betası (Dimson, Scholes-Williams) | geçerlilik §7 |
| S5 | Bulgu 12'nin mekanizması: geri dönüş mü, alıcı azlığı mı | metodoloji VII |
| S6 | Söz ve gerçek: gecikme (çok yıllık sözleşme), ikinci dönem (9A2026, Kasım), sektör | söz ve gerçek, Sınırlar |
| S7 | Tasfiye baskısı altındaki payların sonraki seyri (ileriye dönük doğal deney) | bağlam katmanı |
| S8 | "Sakin yükseliş" parmak izi: fon birikimi + düşen oynaklık + sürekli yükseliş | bağlam katmanı |
| S9 | Tabanda kilitli tahtalar Bulgu 10–12 sınavlarında nasıl sınıflandı | metodoloji VII |
| S10 | Devre kesici ve VBTS başlangıç tarihleri; halka arzlarla büyüyen evrene göre normalizasyon | geçerlilik §7, K1 §8 |
| S11 | Akran grubunda sektör ya da büyüklük bandı | metodoloji VII |
| S12 | KDV dahil tutarlar (31), bayraksız aynı tutarlı tekrarlar (13) | veri denetimi |

**Hiç konuşulmamış yaklaşımlar:**

| # | Soru | Neden |
|---|---|---|
| Y1 | Plasebo: aynı hisselerde rastgele günler | Olay yokken ne ölçtüğümüzü bilmiyoruz (AS2) |
| Y2 | Parametrik olmayan ve standardize sınavlar | CAR3 sağa çarpık; yalnız t kullanıldı |
| Y3 | Bildirimin içeriği: para birimi, kamu/özel, yurt dışı, süre | Yüksek enflasyonda döviz sözleşme farklı karşılanabilir |
| Y4 | İki adımlı duyurular (ihale → sözleşme), güncelleme ve düzeltmelerin kendi tepkisi | İkinci adımın bilgi içeriği bilinmiyor |
| Y5 | Uzun ufuk, t+3 … t+60: geri dönüş mü sürüklenme mi | 3 günden sonrası hiç ölçülmedi; S5'i de ayırır |
| Y6 | Zamanlama: seans içi / kapanış sonrası, Cuma akşamı, aynı güne yığılma | Dikkat sınırlılığı literatürü |
| Y7 | Literatür kıyası | Makalenin kaynakçası ince; etki büyüklüğümüz olağan mı bilinmiyor |
| Y8 | Bütün sınav ailesi için biçimsel çoklu sınama düzeltmesi (Romano-Wolf ya da BH) | Şimdiye kadar yalnız tekrarlanma ölçütü |

## 5. Dalgalar

Beş ajanı aynı veride "bulgu aramaya" salmak, Bulgu 7 ve 10'un başına
geleni ölçekli üretir. Bu yüzden:

1. **Dalga 1, yeni bulgu aramayan işler (paralel).** Literatür, ölçüm
   aletinin denetimi, mevcut bir iddianın (K) sınanması, veri ve maliyet
   envanteri. D1-P ve D1-K sayı üretiyor. Tanımları ve karar kuralları
   §6'da, sonuçtan önce sabit.
2. **Dalga 2, ön kayıt.** Dalga 1'in çıktısına göre sorular Hüseyin'le
   seçilir. Her soru için hipotez, tanım ve karar kuralı sonuçtan önce
   commit'lenir.
3. **Dalga 3, paralel analiz.** Her ajan yalnız kendi ön kaydını koşar.
   Her sonuç makaleye girmeden önce bağımsız olarak yeniden koşulur.

**Asimetri kuralı (bütün dalgalar):** Sağlamlık sınavları bir hükmü
yalnız zayıflatabilir, güçlendiremez. "Sonuçsuz" bir dönem, en iyi sonucu
veren sınav seçilerek "tekrarlandı"ya yükseltilmez.

## 6. Dalga 1 tanımları

### D1-L · Literatür taraması (Y7)

Çıktı: `docs/arastirma/2026-09-29-literatur-taramasi.md`.

Konular:

1. Sözleşme ve yeni iş duyurularının olay çalışmaları. Kore'nin zorunlu
   "tek satış/tedarik sözleşmesi" açıklaması (KAP şablonuna en yakın
   örnek), Çin, Tayvan, Avustralya, ABD savunma sözleşmeleri. Etki
   büyüklükleri: CAR ve anormal hacim.
2. Borsa İstanbul: KAP özel durum açıklamaları, ihale ve sözleşme
   duyuruları, fiyat marjı ve devre kesici, manipülasyon çalışmaları.
   DergiPark ve YÖK Tez dahil.
3. Yöntem: anormal hacim tanımları (log, ortalama/medyan; Ajinkya-Jain,
   Campbell-Wasley), rastgele gün simülasyonları (Brown-Warner), BMP,
   Corrado, genelleştirilmiş işaret, Kolari-Pynnönen, seyrek işlem betası.
4. Karşı tarafın açıklanması ve müşteri kimliği (doğrulanabilirlik,
   gizlilik maliyeti).
5. Rejim ve duyarlılık: yatırımcı iyimserliğinin duyuru tepkisine etkisi
   (K1'de gevşek parada tepkinin iki kat olmasıyla karşılaştırmak için).
6. Dikkat sınırlılığı: Cuma, aynı gün yığılması (Y6 için).

Kurallar: Yalnız sayfası gerçekten açılan kaynak listelenir, bağlantısıyla.
Her kaynağın yanında "tam metin / özet / ikincil atıf" yazılır. Etki
büyüklükleri bizimkilerle bir tabloda karşılaştırılır; tanım farkları
yazılır. Her yöntem önerisi §4'teki bir kimliğe bağlanır.

### D1-P · Plasebo ve sıra sınavları (AS2, Y1, Y2)

Çıktı: `scripts/analiz_plasebo.py`,
`docs/arastirma/2026-09-29-plasebo-ve-sira-sinavlari.md`.

Hat: K1 hattı (`scripts/analiz_k1_rejim.py`) ve onun içe aktardığı
tanımlar. Kopyalanmaz, içe aktarılır. Veri: Borsa İstanbul bülten paneli
(`data/ham_rejim/panel.pkl`), K1 olayları. LLM yok, veritabanı gerekmiyor.

**Plasebo tanımı:**

- Gerçek olayı olan her pay için, aynı dönemde (A, B, C) rastgele işlem
  günleri. Pay başına sahte olay sayısı, gerçek olay sayısının 10 katı.
  Tohum 20260929.
- Dışlama: O payın herhangi bir "Yeni İş İlişkisi" olayının
  [t0−10, t0+10] aralığı.
- Taban, sermaye işlemi ve beta kuralları gerçek olaylarla aynı.
- İki küme:
  - **P-geniş:** yalnız yukarıdaki dışlama.
  - **P-temiz:** ayrıca K1'deki `olay_temiz` tanımıyla aynı pencerede
    ([t0−1, t0+2]) hiçbir KAP açıklaması yok.
- Çalışma 30 dakikayı aşarsa kat 5'e iner ve sapma olarak yazılır.

**Ölçüler:** AV, piyasaya göre AV, CAR3, ön hacim. İkincil olarak
AV_log = ortalama_k [ln adet(t0+k)] − ln(medyan taban), k = 0, 1, 2.

**Sınav:** Gerçek ve sahte olaylar tek tabloda. Ölçü, "gerçek olay"
göstergesine regresyon. Pay ve ISO hafta iki yönlü kümeli
(`analiz_gecerlilik.ols_kumeli`). Katsayı = net etki (gerçek − plasebo).
Plasebo ortalamasının kendisi de aynı kümelemeyle raporlanır.

**Karar kuralları:**

- **P1.** Plasebo AV'si sıfırdan ayrılıyorsa (|t| ≥ 1,96) bu, ölçünün
  yapısal sapması sayılır. H1'in hükmü her dönemde net etkiye göre K1
  kurallarıyla yeniden verilir. Makaledeki AV rakamlarının yanına net
  değer yazılır.
- **P2.** Rejimler arası fark (C−A, C−B) nete göre yeniden hesaplanır,
  K1'deki z'lerle yan yana konur.
- **P3.** CAR3 için aynısı. Plasebo CAR3'ü sıfırdan ayrılıyorsa H3 nete
  göre yeniden hükme bağlanır.
- **P4.** AV_log yalnız raporlanır. Ana ölçüyü değiştirmek ayrı bir
  karar, bu notta verilmez.
- **P5.** Ön hacim (günlük log ortalaması) plasebo altında sıfır
  beklenir. Değilse ayrıca yazılır.

**Sıra ve standardize sınavlar** (CAR3; A, A1, A2, B, C ve yedi yıl;
ayrıca H5'in temiz alt kümesi):

- Genelleştirilmiş işaret sınavı (Cowan 1992). Sıfır altındaki pozitif
  oranı, tahmin penceresinin 3 günlük örtüşmeyen CAR'larından.
- Çok günlü sıra sınavı (Corrado 1989'un CAR uyarlaması; hangi uyarlama
  kullanıldıysa notta adıyla).
- BMP (Boehmer, Musumeci, Poulsen 1991) ve Kolari-Pynnönen (2010)
  kesitsel korelasyon düzeltmesi.

**Karar:** Birincil sağlamlık sınavı Kolari-Pynnönen düzeltmeli BMP.
K1'de "tekrarlandı" denen bir dönemde KP-BMP |t| < 1,96 ise K1 hükmü geri
alınmaz, yanına "standardize sınavda zayıflıyor" yazılır. §5'teki asimetri
kuralı geçerli: B'nin "sonuçsuz" hükmü bu sınavlarla yükseltilmez.

### D1-K · K çarpanının sınanması (AS1)

Çıktı: `scripts/analiz_k_carpani.py`,
`docs/arastirma/2026-09-29-k-carpani-sinamasi.md`.

Veri: Veritabanının yayın evreni (bugünkü hâli), yfinance hattının CAR'ları
(`car_1g`, `car_3g`, `car_5g`), AV `skor_gecerlilik.anormal_hacim` ile.
Dönemler `skor_gecerlilik.donem_suz` ile: **analiz** (2025-09-22 →, K'nın
türetildiği yıl) ve **sınama** (öncesi). Hücreler `kt_acik × guncelleme_mi`,
`skor_gecerlilik` §7 ile aynı. LLM yok, veritabanına yazılmaz.

**Hipotezler (19.09'daki ilk yıl iddiaları):**

| # | Hipotez | İlk yıl |
|---|---|---|
| K-H1 | Açık + ilk CAR3 > gizli + ilk CAR3 | +%1,23 / +%0,02 |
| K-H2 | Gizli + ilk'te tepki geri veriliyor: CAR3 − CAR1 < 0 | +%0,84 → +%0,02 |
| K-H3 | Açık + ilk CAR3 > açık + güncelleme CAR3 | +%1,23 / +%0,68 |
| K-H4 | AV sıralaması: gizli + ilk < açık + güncelleme < açık + ilk | 0,259 < 0,317 < 0,351 |

Gizli + güncelleme (n ≈ 6) yalnız raporlanır.

**Sınav:** Farklar hücre göstergeleriyle regresyonla. Pay ve hafta iki
yönlü kümeli. MDE raporlanır. İkincil: skorlu bildirimlerde
CAR3 ~ gizli + güncelleme + f(r), aynı kümeleme.

**Karar:** K1 kuralları (tekrarlandı / yön aynı, sonuçsuz / tekrarlanmadı).
Önce sınama yılı (örneklem dışı) hükme bağlanır; iki yıl birlikte ayrıca
raporlanır.

**Ek:** 25.09'daki karşı taraf düzeltmesi (`bbac018`) sınıflamayı
değiştirdi. İlk yılın tablosu bugünkü veriyle yeniden hesaplanır, 19.09
rakamlarıyla farkı yazılır. Not K'yı değiştirmez. Seçenekleri yazar,
karar Hüseyin'in.

### D1-E · Veri ve maliyet envanteri (S1–S12, Y1–Y8)

Çıktı: `docs/arastirma/2026-09-29-veri-envanteri.md`.

Her kimlik için:

- Gereken veri, repodaki ya da veritabanındaki yeri (yol, tablo, kolon)
- Kapsam (tarih aralığı, satır sayısı) ve eksikler
- KAP'tan çekim gerekiyorsa istek sayısı ve 2 sn aralıkla süre
- LLM gerekiyorsa girdi token ve USD tahmini (mevcut çıkarım maliyetlerinden)
- Riskler ve kabaca iş büyüklüğü

KAP'a istek atılmaz; sayılar yerel arşivden ve veritabanından çıkarılır.
Dalga 2 için sıralama önerisiyle biter: bedava ve hazır olan önce.

## 7. Ajan kuralları (Dalga 1)

- Önce bu belgeyi ve kendi görevinin kaynak notlarını oku.
- Yalnız §6'da adı verilen yeni dosyaları oluştur. Mevcut hiçbir dosyayı
  değiştirme (`src/`, `site/`, mevcut betikler ve notlar dahil). Geçici
  dosyalar yalnız scratchpad'e.
- Veritabanına yazma. LLM API'si çağırma. KAP'a istek atma (WAF IP'yi bir
  kez engelledi).
- Tanımları mevcut koddan içe aktar, kopyalama.
- §6'daki bir tanım yazıldığı gibi uygulanamıyorsa sessizce değiştirme.
  Sonuca bakmadan en yakın seçeneği seç, notun "Sapmalar" bölümüne
  gerekçesiyle yaz.
- Notlar Türkçe, repodaki not üslubuyla: kısa cümleler, tablolar, en üstte
  yeniden üretim komutu, ondalık virgül.
- Commit atma. Bitince özet, dosya yolları, sapmalar ve şüpheli gördüğün
  her şeyi raporla.

## 8. Dalga 1 sonuçları ve bekleyen kararlar (2026-09-29 akşamı)

### Çıktılar

| İş | Not | Betik | Doğrulama |
|---|---|---|---|
| D1-L | `2026-09-29-literatur-taramasi.md` | — | Kore çalışmasının rakamları kaynak metinle karşılaştırıldı |
| D1-P | `2026-09-29-plasebo-ve-sira-sinavlari.md` | `scripts/analiz_plasebo.py` | Yeniden koşuldu, rakamlar birebir |
| D1-K | `2026-09-29-k-carpani-sinamasi.md` | `scripts/analiz_k_carpani.py` | Yeniden koşuldu, birebir. Mutabakat adımı 19.09 tablosunu sıfır farkla üretiyor |
| D1-E | `2026-09-29-veri-envanteri.md` | — | WAF kotası ve sektör alanı yerinde kontrol edildi |

Üç ajan oturum limiti yüzünden yarıda kesildi ve kaldıkları yerden
sürdü. Çıktılar bundan etkilenmedi.

### Öne çıkanlar

1. **Ana bulgular ölçüm aletinin ürünü değil.** Rastgele günlere göre
   net hacim etkisi A +%27,4, B +%20,8, C +%33,9. Net CAR3 A +1,64,
   C +0,68 puan. Gevşek paradaki iki kat fark nete göre de duruyor
   (z −2,17).
2. **K çarpanının örneklem dışında ampirik dayanağı yok** (§3 AS1).
3. **"Sızıntı izi yok" okuması zayıfladı.**
   - Temiz olaylarda ön hacim tabana göre sıfır. Ama olaysız günlerin
     aynı ölçüsü tabanın %3–5 altında.
   - Rastgele günlere göre fark yedi yılda +%4,9 (t 2,06), C'de +%10,5
     (t 2,79). A ve B'de sıfır.
   - Mekanik bir açıklaması olabilir: bir önceki duyurunun hacmi ön
     pencereye taşıyor olabilir. Bu ölçülmedi.
   - Literatür Kore, ABD, Avustralya ve BIST-30'da duyuru öncesi pozitif
     getiri buluyor. Bizde getiri tabanlı ön-CAR sınavı yok (19.09'daki
     betimleyici "öncesi sürüklenme" dışında).
4. **Standardize ve sıra sınavları bu veride olay yokken de yukarı
   yanlı.** C'de KP-BMP plaseboda +2,09. Verdikleri destek zayıf. Hiçbir
   hükmü zayıflatmadılar.
5. **Halka arz çapası (α = 0) 2020–24'te olay yokken +1,9 puan veriyor.**
   C'de bu sapma yok (−0,12, t −0,23), yani sitedeki panel için acil
   değil.
6. **Etki büyüklüğümüz literatürde olağan** (Kore, duyuru günü +%0,69,
   6.072 olay). "Büyük haber daha çok fiyatlanmıyor" literatürle
   çelişiyor. Bizim gücümüz sınırlı (MDE ~0,6 puan/S).
7. **Envanter.**
   - 2020–24 için detay metni yok. S1 paketi ~4.400 KAP isteği (kota
     hızıyla ~17 saat) ve ~1,43 USD.
   - Devre kesici ve VBTS kayıtları 2020'den beri var.
   - `sirket.sektor` boş.

### Hüseyin'in kararını bekleyenler

| # | Karar | Seçenekler | Öneri |
|---|---|---|---|
| Ka | K çarpanı | A: makaleye not · B: K = 1 · C: yalnız güncelleme ekseni · D: yedi yılda sına | Şimdi A, sonra D (S1 paketiyle). S1 onaylanmazsa B |
| Kb | Makale düzeltmeleri | K bölümü; Bulgu 2 "sızıntı yok"; H1'e net rakamlar; sıra sınavlarının boyutu Sınırlar'a | Hepsi tarihli notla. K ve Bulgu 2 önce, çünkü biri yanlış, öteki fazla iddia |
| Kc | S1 paketi | ~4.400 KAP isteği, ~1,43 USD, çekim hızı (kota ~17 saat / güvenli ~55 saat) | Onay. K'yı, skor sınavlarını ve Y3/Y4'ü yedi yıla taşıyor |
| Kd | Dalga 2 soruları | Aşağıdaki liste | — |
| Ke | `arastirma/dalga-1` dalının master'a alınması | — | Kararlardan sonra |

### Dalga 2 adayları (öneri sırası)

1. **S7 · Tasfiye baskısı doğal deneyi.** Sonuç her gün birikiyor. Ön
   kayıt hemen yazılmalı.
2. **H2-bis · Sızıntı sorusunu düzgün sınamak.** Bedava, yedi yıl.
   - Eşleştirilmiş plasebo: gerçek temiz olaylar da [t0−10, t0−6]
     duyurularından arındırılır.
   - Getiri tabanlı ön-CAR [t0−4, t0−1].
   - Seans içi / seans sonrası ayrımı.
3. **Y5 + S5 · Uzun ufuk ve Bulgu 12'nin mekanizması.** t+3 … t+60.
   Oynak tahtada fiyat geri dönüyor mu? 19.09'daki 20 günlük bakış ön
   kayıtta beyan edilir.
4. **S10 · Oynak tahta (H4) gerçek devre kesici ve VBTS kayıtlarıyla**,
   V90 vekili yerine. Bedava.
5. **Y6 · Zamanlama:** Cuma, aynı gün yığılması, seans sonrası. Şirket
   sabit etkisiyle.
6. **S6 · Söz ve gerçek, ikinci dönem.** Ön kayıt 9A2026 raporlarından
   önce (~30 Ekim).
7. **Y3, Y4 · 2024–26 kısmı.** n küçük. S1 paketi gelirse yedi yıla.
8. **Y9 (yeni, D1-L önerisi) · Yatırımcı iyimserliği vekili.** Rejim
   farkının mekanizması için.
9. **Ücretli ya da çekimli olanlar:**
   - S1 paketi
   - S2, ÖDA Genel (~2,2–3,4 USD)
   - S8, fon geçmişi (~21.400 istek)

## 9. Kapanış (2026-09-30)

Hüseyin'in yönlendirmesi: proje bir veri ürünü ve bir mühendislik vaka
çalışması. Akademik makaleye dönüşecek işlerden (uzun çekimler, yeni
ekonometrik sınavlar) bilinçli olarak geri çekiliniyor. Araştırmanın
çıktıları siteye ve makaleye yansıtılıyor.

| # | Karar | Sonuç |
|---|---|---|
| Ka | K çarpanı | A. Değerler aynı; anlatım düzeltildi. K bir tepki tahmini değil, şeffaflık ayarı |
| Kb | Makale düzeltmeleri | Uygulandı, metodoloji sürüm 3.0 |
| Kc | S1 paketi | Red. Makalede "bilerek yapılmadı" |
| Kd | Dalga 2 | Yapılmıyor. Adaylar makalenin VII "Açık sorular" listesinde |
| Ke | Dal birleştirme | İçerik revizyonundan sonra |
| Kf | Fon ve soruşturma bağlamında şirket adları | Makaleden çıktı, araştırma notlarında duruyor |
| Kg | Eski özet ve K'nın 19.09 tablosu | Makalede açılır "Sürüm geçmişi" kutusunda |

Uygulama planı: `docs/superpowers/plans/2026-09-30-icerik-revizyonu.md`.
