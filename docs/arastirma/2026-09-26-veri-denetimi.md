# Veri seti denetimi — bulgu ve karar notu (2026-09-26)

**Durum: UYGULANDI (2026-09-26, Hüseyin: "hepsini yap").** Dal
`fix/veri-denetimi`. Kapıya dört kontrol eklendi (A7, B4–B6), 23 bildirim
için elle karar verildi, güncelleme ve düzeltmeler önceki bildirime
bağlandı, açık pencere hatası kapandı, tahta etiketine piyasa taban oranı
eklendi. Denetim artık her günlük koşunun sonunda tekrarlanıyor
(`scripts/veri_denetimi.py --kati`).

## Tetikleyici

Bir kullanıcı sitedeki ARDYZ kartını (25.09.2026) okurken iki şey sordu:
neredeyse her kartta "Çok oynak" yazması normal mi, ve bu içerik doğru
mu? Kart "Bu iş şirketin cirosunun %5,5'i · Önemli iş" diyordu. KAP
metni:

> Şirketimiz, Tokat Erbaa Belediyesi tarafından **muhammen bedeli**
> 430.320.000 TL olan "… EDS … İşinin **Kiraya Verilmesi**" ihalesinde,
> **gelir paylaşımı modeli** kapsamında en avantajlı teklifi vererek …
> **10 yıl süreli** ihale sözleşmesini imzalamıştır.

430 mn TL idarenin tahmini bedeli; ARDYZ'nin geliri değil ve payı
açıklanmamış. Kapı bunu geçirdi, çünkü A1–A3 sayının metinde
**geçtiğini** denetler, **neyin sayısı olduğunu** denetlemez. Soru bu
hata sınıfının veri setinde ne kadar yaygın olduğuydu.

## Yöntem

Yayındaki 1.272 bildirimin (962'si skorlu) tamamı kural tabanlı bir
tarayıcıdan geçirildi; işaretlenen 453 bildirimin ~150'si elle okundu ve
gerçek hata / yanlış alarm olarak ayrıldı. LLM kullanılmadı. Kontrol
aileleri:

| Aile | Soru |
|---|---|
| Anlam | Tutarın geçtiği cümlede muhammen, yatırım, alım, çerçeve, opsiyon, birim fiyat, ortaklık payı, dönemsel ifade var mı? KAP karşı taraf niteliği "Tedarikçi" mi? |
| Sayısal | Oran %50 üstü; şirketin TTM'inde 3 kattan büyük sıçrama |
| Kaçan tutar | Skorsuz ama metinde para tutarı var |
| Çift sayım | Aynı skorlu tutar aynı hissenin önceki bildiriminde; bir bildirimde iki skorlu kalem |
| Özet / bağlam | Özetteki sayı metinde var mı; sıklık sayımı DB ile tutuyor mu; "açık" karşı taraf adı kurum eki taşıyor mu; aşırı CAR |

## Bulgular

### 1. Yanlış büyüklük — 10 kesin hata

Skorlu bildirimlerin %1,0'ı. **Onunun onu da "önemli" ya da "mega"
kademesindeydi** (sitenin öne çıkardığı 410 bildirimin %2,4'ü): bu hata
tipi tutarı hep büyütüyor.

| Tür | Vaka | Eski → yeni |
|---|---|---|
| Şirket alıcı | ASTOR 30.01.2026 (Trench'ten bushing alımı) | %9,03 → skorsuz |
| | OFSYM 31.08.2026 (ABD'den DDGS alımı) | %6,28 → skorsuz |
| | GEREL 30.09.2024 (yazılım firmasına 700 mn TL ödeyecek) | %38,92 → skorsuz |
| Şirketin yatırımı | TOASO 08.09.2025 (256 mn EUR üretim yatırımı) | %8,06 → skorsuz |
| | YEOTK 29.12.2025 (ESCO; yatırım ve finansman şirkette) | %9,66 → skorsuz |
| Tahmini ihale bedeli | ARDYZ 25.09.2026 | %5,46 → skorsuz |
| Artış + yeni toplam | FORTE 18.11.2024 (7.112.290 = 6.184.600 + 927.690) | %20,56 → %2,37 |
| | ORGE 06.02.2025 (249,9 mn = 209,8 mn + 40,1 mn) | %18,15 → %1,16 |
| | ORGE 18.03.2025 (360 mn = 213,2 mn + 146,8 mn) | %14,78 → %4,28 |
| İmzasız iş | ORGE 05.02.2025 ("görüşmelere başlanmıştır") | %10,41 → skorsuz |

Sınır vakalar: CVKMD'nin üç Trafigura anlaşması (tutar satış bedeli
değil ön ödeme; "alt sınır" notuyla onaylandı), GESAN 08.04.2026 (205 mn
USD projelerin toplam yatırım bedeli; skorsuz), EFOR 02.04.2025 ve ARDYZ
01/03.12.2025 (KAP'ta karşı taraf tedarikçi, metinde yön belirsiz;
skorsuz).

**Model tutarsız, kurallar değil.** Prompt'un 4. ve 5. kuralı (şirketin
ödediği bedel, hedef/beklenti tutarı) bu vakaları zaten yasaklıyor. Model
aynı şirketin aynı tip metninde bir kez uydu, bir kez uymadı:

| Şirket | Doğru dışarıda bıraktı | Yanlış saydı |
|---|---|---|
| YEOTK | 31.10.2024, 100 mn USD ESCO yatırımı | 29.12.2025, 28 mn USD ESCO yatırımı |
| TOASO | 04.11.2024, 232 mn EUR yatırım | 08.09.2025, 256 mn EUR yatırım |
| OFSYM | 09.09.2025, 5 mn USD DDGS alımı | 31.08.2026, 27 mn USD DDGS alımı |

Altın kümedeki %94 doğruluğun sahadaki karşılığı bu. Kaçan tutar ailesi
(48 bildirim) ise temizdi: model yatırımları, beklentileri ve görüşmeleri
tutarlı biçimde dışarıda bırakmış.

### 2. Aynı iş iki kez — 25 bağ (18 aynı iş, 7 düzeltme)

- **Kamu ihalelerinde iki adım.** Önce "ihale üzerimizde kaldı", sonra
  aynı tutarla "sözleşme imzalandı"; ikisi de skorlanıyordu. PLTUR'da 7
  kez (İBB'nin 3,4 mr TL'lik işi %54 ile iki "mega iş"); ORGE, CEOEM
  (üç halkalı zincir), ONRYT, LINK, SMART.
- **Düzeltme ve asıl bildirim birlikte yayında:** ONCSM, VBTYZ, KAYSE
  (%19,5), BVSAN; skorsuz olarak TRILC, CWENE, ALTNY.
- `bildirim.ilgili_kap_id` (KAP'ın relatedDisclosureOid'i) hiçbir satırda
  dolu değil.

Bayraksız 13 aynı-tutar tekrarının okunanları ayrı işti: KAYSE 12 ve
13.02.2025'te iki ayrı 7,07 mr TL anlaşma ("toplam satışlarımız 14,14
mr'a ulaştı"), MACKO farklı müşterilerle aynı fiyattan reklam
sözleşmeleri, HRKET yuvarlak tutarlı farklı projeler.

### 3. "Çok oynak" etiketi — hata değil, bağlam eksik

Etiketli bildirim payı 2025'te %5–20 iken 2026 Temmuz/Ağustos/Eylül'de
%58 / %63 / %66 (Eylül'de %13 de resmî tedbir). Sayım doğrulandı: Borsa
İstanbul duyuru ifadesini Ocak 2026'da değiştirmiş ("Başlamıştır" →
"devreye girmiştir") ama seans başına sayı o ay sıçramıyor (Aralık 31,2,
Ocak 29,2). İki gerçek neden:

- **Piyasa ısındı.** Bütün hisselerde aynı kuralın payı çoğu ay %20–35,
  Eylül 2026'da %44; seans başına devre kesici 106,9 ile Ekim 2023'ten
  beri en yüksek.
- **Bildirim yapan hisseler değişti.** V90 > 8: piyasa %30 / %32 / %41,
  bildirim yapanlar %54 / %65 / %75. 2025'te bildirim yapanlar piyasadan
  sakindi. İlk 5 sık bildirimci çıkarılınca %62, hisse başına %63.

Etiket doğru bir olguyu söylüyor ama bugünkü rejimde ayırt edici değil;
eşiği değiştirmek yerine taban oranı gösteriliyor.

### 4. Küçükler

- **Açık pencere:** son iki günün KAP listesi çekiliyor ama (yarım
  olduğu için) arşive yazılmıyordu; bağlam hesabı yalnız arşivi okuyordu.
  En taze bildirim kendi sıklığına girmiyordu (ARDYZ kart 43, DB 44).
- **Özette uydurma yıl:** EUREN 30.07.2026 "Ağustos 2024'te", KONTR
  20.03.2025 "2024 yılı 2. çeyreği"; iki metinde de yıl yok.
- **KDV dahil tutar:** 31 skorlu bildirim; oran ~%20 şişik, 3'ünde kademe
  değişir. **Düzeltilmedi** — KDV oranı işe göre değişiyor (%1/%10/%20),
  tek katsayı yanlış olurdu. Sınır olarak duruyor.
- Sitede yazım: "%46'i", "%-4,71".

### Temiz çıkanlar

Karşı taraf sınıflandırıcısı ("kurum eki taşımayan" 80 adın hepsi gerçek
kurum), çok para birimli sözleşmeler, oranı %50 üstündeki bildirimlerin
çoğu (ASTOR 769 mn USD ABD siparişi, PATEK, PLTUR İBB). CWENE'nin
düzeltmesi tasarımın bir kararını doğruladı: şirket kendi TL çevrimini
yanlış yazmıştı (400 mn yerine 124 mn), ama TL çevrimi TCMB kuruyla
yapıldığı için hata bize geçmemişti.

## Kararlar ve uygulama

| # | Karar | Nerede |
|---|---|---|
| 1 | Kapıya A7 (özette metinde olmayan yıl → üst model) ve B4–B6 (tedarikçi niteliği, anlam kalıpları, artış+toplam aritmetiği → elle kuyruk) | `cikarim.py`, `yayin.py` |
| 2 | Elle kararlar repoda, gerekçesiyle; `cikarim`'a model='elle', katman=3 satırı eklenir (append-only korunur); site gerekçeyi gösterir | `data/elle_duzeltmeler.json`, `elle.py`, `scripts/elle_duzelt.py` |
| 3 | Güncelleme/düzeltme bağı: KAP'ın "önceki açıklama tarihleri" + ortak tutar; düzeltilen bildirim yayından kalkar, aynı tutarı tekrarlayan güncelleme "önceden duyurulan iş" olur | `bag.py`, `scripts/bag_kur.py` |
| 4 | Açık pencere geçici klasöre; bağlam ve VBTS onu da okur | `arsiv.py`, `backfill.py` |
| 5 | Tahta notunda aynı günün piyasa taban oranı | `baglam.piyasa_oynak_orani` |
| 6 | Denetim her günlük koşunun sonunda | `scripts/veri_denetimi.py` |

B5'in kalıpları gerçek bildirimlerle ayarlandı. **"İmzalamak için davet
edildi" bilerek dışarıda:** kamu ihalesinde işi kazandın demek (ALVES'in 4
bildirimi meşru). "Yatırımla" gibi geniş kalıp ANELE'de otelin niteliğini
("turizm yatırımları arasında") yakalıyordu, çıkarıldı. Kurallar mevcut
veride 24 bildirimi elle kuyruğa attı; 23'ü karara bağlandı (12 skorsuz,
3 düzeltme, 8 onay), biri (EFOR 19.12.2024) A7'nin yanlış alarmıydı —
şirket yılı "2 024" yazmış; karşılaştırma normalize metne alındı.

**Prompt değiştirilmedi (v3).** Çelişkili "revize tutar → tek seferlik"
kuralı düzeltilmeli, ama prompt değişikliği altın kümede yeniden
ölçülmeden (ücretli koşu) yayına girmemeli. O zamana kadar B6 yakalıyor.

## Etki

| | Denetim öncesi | Sonrası |
|---|---|---|
| Yayında | 1.272 | 1.267 (5 düzeltilen asıl bildirim kalktı) |
| Önemli ve üstü (tekil iş) | 410 | 379 |
| Mega (tekil iş) | 145 | 130 |
| Elle kararlı bildirim | 0 | 23 |
| Bağlı güncelleme/düzeltme | 0 | 92 (18 aynı iş, 7 düzeltme) |

## Sınırlar ve açık işler

- Anlam kontrolleri kalıp tabanlı; kalıbın görmediği bir biçimde yazılmış
  alım ya da yatırım geçebilir. Denetim her koşuda tekrarlanıyor ama o da
  aynı kalıplarla bakıyor; periyodik elle örnekleme gerekli.
- KDV dahil tutarlar (31) düzeltilmedi.
- Bayraksız tekrarlar bağlanmıyor; 13'ünün hepsi okunmadı.
- Metodolojideki ampirik bulgular (Bulgu 1–12) bu düzeltmelerden önceki
  veriyle hesaplandı. 23 skor değişikliği ve 18 "aynı iş" olay
  çalışmasındaki örneklemi küçük ölçüde etkiler; analizler yeniden
  koşulunca metodoloji güncellenmeli.
- Yerel liste arşivi 20.09'da bittiği için taban oranı ve açık pencere
  düzeltmesi ilk kez CI'da yazılacak; o koşunun çıktısı kontrol edilmeli
  (beklenen: sıklık farkı 0, ARDYZ 44).
