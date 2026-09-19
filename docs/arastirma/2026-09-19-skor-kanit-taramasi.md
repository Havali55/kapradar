# Etki skoru — kanıt taraması

Tarih: 2026-09-19 · Girdi: 613 bildirim, 612 tepki, 27.581 kapanış, 85.032
arşivlenmiş KAP bildirimi · Kod: `scripts/ozellik_kur.py`, `analiz_skor.py`,
`analiz_beta.py`, `analiz_tahta.py`

Amaç: Adım 10'un ağırlıklarını (w1/w2/w3) masa başında değil veriyle kurmak.
Sonuç, ağırlıklardan önce **skorun ne olduğu** sorusunu değiştirdi.

---

## 1. Ölçüm aletinin denetimi

**Beta = 1 varsayımı tutmuyor.** Evrenin betası: ortalama 0,79 · medyan 0,82 ·
%10–%90 aralığı 0,49–1,02. Yalnızca 1 hissenin betası 1,3'ün üstünde, 37'si
0,7'nin altında (n = 111, olay pencereleri dışlanarak tahmin edildi).

Piyasa-düzeltilmiş (β=1) ile piyasa modeli arasındaki fark toplamda küçük
(+%0,69 → +%0,77, korelasyon 0,984) ama **tek tek bildirimlerde değil**:

- 601 bildirimin **202'sinde** fark 1 puandan büyük
- **50'sinde işaret değişiyor**

Sayfada bildirim başına tek sayı yayınlanacağı için **piyasa modeline geçilmeli**
(α ve β hisse başına, olay pencereleri dışlanarak, 120–250 işlem günlük tahmin
penceresi).

**Endeks bu hisseleri zaten açıklamıyor.** Piyasa modeli medyan R² = **0,12**;
106 hissenin 43'ünde 0,10'un, 19'unda 0,05'in altında. Literatürde küçük
şirketler için olağan aralık (0,02–0,10) — modeli geçersiz kılmaz ama "anormal
getiri"nin içinde haberle ilgisiz çok şey olduğunu söyler.

**Gecikmeli tepki var ama küçük.** Gecikmeli piyasa betası +0,08 (eşanlı 0,77);
tahta derinliğine göre değişmiyor (sığ +0,07, derin +0,10). Scholes-Williams
düzeltmesi etkili betayı ~0,85'e çıkarır; 3 günlük pencere bunu zaten yutuyor.

**Örneklemin içinde bir fon krizi var.** Endeksin günlük |getirisi| > %3 olan
12 gün; en serti **2026-09-16** (XU100 −%5,54) — Pusula/Tera Portföy fon
temerrütleri. 54 bildirimin tepki penceresi bir stres gününü kapsıyor.

**Aynı güne yığılma.** 613 bildirim 213 güne düşüyor, %8'i kendi gününde yalnız
(26.12.2025'te 17 bildirim). Gün düzeyinde kümelenince ortalama tepkinin t'si
2,46 → **2,24**. Bulgu ayakta ama olduğundan güçlü görünüyordu.

## 2. Tepkiyi ne öngörüyor

Tüm sinyaller birlikte (ticker düzeyinde kümelenmiş standart hata):

| Değişken | 1 gün | t | 3 gün | t |
|---|---|---|---|---|
| son 5 günde devre kesici | −2,18 | **−4,81** | −2,48 | **−3,13** |
| tutar / işlem hacmi oranı | +0,81 | **+4,04** | +0,29 | +0,88 |
| tutar açıklanmış (boyut sabitken) | −1,75 | **−3,35** | −0,87 | −1,02 |
| güncelleme bildirimi | −0,97 | **−2,11** | −1,33 | −1,40 |
| karşı taraf açıklanmış | +0,07 | +0,19 | +1,20 | +1,89 |
| log10 günlük ciro | +0,15 | +0,52 | +0,07 | +0,15 |
| bildirim öncesi sürüklenme | +4,26 | +1,43 | +9,51 | +1,66 |

**R² = 0,111 (1 gün) / 0,064 (3 gün).** Yani elimizdeki her şeyle bile tepkinin
%90'ından fazlası öngörülemiyor. **Skor bir getiri tahmini olarak kurulamaz.**

İki okuma:

- **Tutarı açıklamak iyi haber değil, tutarın büyük olması iyi haber.** Boyut
  sabitken açıklamış olmak −1,75 puan; oranın kendisi +0,81 puan. Küçük rakam
  hayal kırıklığı yaratıyor. `w1`'in lehine elimizdeki tek doğrudan kanıt bu.
- **Bildirim öncesi koşu güçlü ama güvenilmez.** Sonradan en iyi %10'luk küme
  öncesinde +%6,84 (medyan +%4,40) yapmış; ama ilk yarıda t = +3,34, ikinci
  yarıda t = +0,32. **Kalibrasyona girmemeli**, bağlam olarak gösterilebilir.

## 3. Kirlilik ölçüldü, tahmin edilmedi

Arşivdeki 85.032 bildirimin **14.013'ü Pay Bazında Devre Kesici**. (Not: devre
kesiciyi Borsa İstanbul yayınlıyor, yani hisse `stockCodes`'ta değil
`relatedStocks`'ta — iki alan birden okunmalı.)

- Bildirimlerin **%92'si** (566/612) son 90 günde tedbire düşmüş hisselerden
- **180'inde** bildirimden 5 gün önce devre kesici var
- 25'inde 5 gün içinde içeriden işlem bildirimi

Tedbir yoğunluğuna göre ortalama tepki:

| Tedbir (90g) | n | 1 gün | 3 gün | 20 gün (medyan) |
|---|---|---|---|---|
| az (≤2) | 220 | +1,09% (t 4,83) | +0,94% (t 2,35) | +0,73% (−2,51%) |
| orta (2–6) | 227 | +0,89% (t 3,29) | +1,23% (t 2,56) | +2,30% (−0,32%) |
| yoğun (>6) | 154 | +0,73% (t 2,08) | −0,47% (t −0,79) | +2,82% (+2,13%) |

**Modelin tek istikrarlı katsayısı bir temel veri değil, bir kirlilik işareti**:
kırpılmış örneklemde −2,25, ikinci altı ayda −3,15, 1 günlük pencerede −2,18.

**Tahta derinliği hipotezi doğrulanmadı.** Sığ tahtalar ilk gün en yüksek tepkiyi
veriyor (+%1,42) ama 5. günde +%0,18'e iniyor (medyan −%0,66); derin tahtalar
kazancını koruyor (+%1,22, medyan +%0,95). Çok değişkenli modelde derinlik
anlamsız; yalnızca tedbire düşmemiş tahtalarda anlamlı ve **pozitif** (+1,08,
t = 2,26).

## 4. Karşı taraf — bedava ve yapısal sinyal

| | n | 1 gün | 3 gün | medyan 3g |
|---|---|---|---|---|
| açık · ilk açıklama | 327 | +1,16% | **+1,23%** (sh ±0,39) | +0,69% |
| açık · güncelleme | 55 | +0,50% | +0,68% | +0,23% |
| gizli · ilk açıklama | 213 | +0,84% | **+0,02%** | −0,04% |
| gizli · güncelleme | 6 | −0,75% | −5,18% | −3,16% |

Karşı tarafı gizleyen bildirim ilk gün +%0,84 alıyor, üçüncü günde tamamını geri
veriyor. En sert 6 düşüşün 4'ünde karşı taraf gizli; en yüksek 10 yükselişin
**10'unda da açık**.

## 5. Karar önerisi

Spec §8'in tek sayısı iki işi karıştırıyor: bildirimin **büyüklüğü** ile
piyasanın **tepkisi**. Üçe ayrılmalı:

1. **Büyüklük skoru** (deterministik) — tutar ÷ TTM hasılat, karşı taraf tipi,
   süre. Getiri iddiası taşımaz.
2. **Geçmiş tepki paneli** (betimleyici) — tek sayı değil medyan + çeyreklik + n.
3. **Tahta kalitesi bayrağı** (uyarı) — devre kesici sayısı, içeriden işlem,
   öncesi sürüklenme. Skora karışmaz, yanında durur.

Ağırlıklara dair somut öneriler:

- **w2 (karşı taraf) 0,7 → 1,0.** Tepkinin kalıcılığıyla ilişkili tek yapısal
  alan; bedava ve halüsinasyona kapalı. "Gizli" durumunda skor düşürülmeli,
  sadece bileşen sıfırlanmamalı.
- **Güncelleme bildirimi çarpan değil etiket olmalı.** 3 günlük tepkisi
  ortalama +%0,10, yani olay değil.
- **w1 baskın kalsın** ama gerekçesi materyallik, tepki değil.
- **Öncesi sürüklenme skora girmesin.**

Yan fayda: bu ayrım spec §13'teki SPK riskini de azaltıyor. "Bu iş cironun
%18'i kadar" ölçülebilir bir olgu; "bu bildirim hisseyi yükseltir" zımni
tavsiye. Veri zaten ikincisini söyleyemeyeceğimizi gösteriyor.

## 6. Sınırlar

- Tutar bilgisi **regex tahmini** (LLM Adım 12'de) — yön göstergesi, kesin değil.
- Ciro oranının paydası yok (Adım 7); `w1`'in gerçek testi ondan sonra.
- Tek yıl, tek şablon, içinde bir fon krizi. İkinci yıl eklenmeden katsayılar
  kalıcı sayılmamalı.
- Evren, o dönemde "Yeni İş İlişkisi" açıklamış şirketler — BIST'in tamamı değil.

## Kaynaklar

- EventStudyTools — Expected Return Models: piyasa modeli varsayılan, piyasa-
  düzeltilmiş model bireysel menkul kıymette daha az hassas; tahmin penceresi
  120–250 gün; sığ hisselerde Scholes-Williams düzeltmesi.
- *A Guide on Data Analysis*, Event Studies bölümü: duyuru CAR'ı ex-post
  sonuçlarla büyük ölçüde ilişkisiz ("abnormal returns measure price reactions,
  not predictive value signals"); aynı güne düşen olaylarda kesitsel bağımlılık
  t değerlerini şişirir.
- Euronews / Cumhuriyet (17.09.2026): Pusula ve Tera Portföy fon temerrütleri,
  BIST 100 %5,5 düşüş.
