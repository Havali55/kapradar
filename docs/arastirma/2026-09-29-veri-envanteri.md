# Veri ve maliyet envanteri: S1–S12, Y1–Y8 (D1-E, 2026-09-29)

**Durum: DALGA 1, D1-E.** Analiz yok, sonuç yok. Bu not yalnız verinin
durumunu çıkarıyor: her açık soru için ne lazım, elde ne var, eksik ne
kadara ve ne kadar sürede gelir. Dalga 2'de hangi soruların ön kayda
alınacağı buna göre seçilecek.

**Yeniden üretim.** Sayımlar yerel arşiv (`data/ham/`, `data/ham_rejim/`)
ve veritabanı üzerinde salt okunur sorgularla yapıldı. KAP'a istek
atılmadı, LLM çağrılmadı, veritabanına yazılmadı. Repodaki komutlar:

- `python scripts/veri_denetimi.py --liste 40`: S12 listeleri (yalnız
  veritabanı okur).
- `python scripts/rejim_arsivi.py rapor`: S1 ve S2 sayıları (KAP'a
  çıkmaz; USD kuru için yfinance'e çıkar). Son çıktısı
  `data/rejim_kap5.log`.

Diğer sayımların sorgusu ya da dosyası her sayının yanında. Yardımcı
betikler repoya eklenmedi (§7: yalnız §6'daki dosya).

## Özet

- **Hazır ve bedava olan çok.** KAP liste arşivi 2020-01-01 → 2026-09-19
  arası tam (478.250 kayıt; bildirimsiz tek iş günü 20.03.2026, bayram).
  Borsa İstanbul bülteni 2020-01-02 → 2026-09-25 (1.690 gün, 698 pay).
  Bu ikisiyle S4, S9, S10, Y5 (ve S5'in yarısı), Y6 çekimsiz ve LLM'siz
  sınanabilir. S12 ile Y3 ve Y4'ün 2024–26 kısmı veritabanında.
- **En büyük boşluk 2020–24 bildirim metinleri.** Yerelde tek bir
  2020-01 → 2024-08 detayı yok. S1, S2, Y3 ve Y4'ün 2020–24 kısmı, S6'nın
  gecikme kolu ve S11'in skor kademesi buna bağlı.
- **~1,43 USD doğru.** İki bağımsız yoldan 1,43–1,44 USD. Ama asıl
  maliyet KAP süresi: S1 ~4.400 istek. 2 sn aralıkla ~2,5 saat; gözlenen
  WAF kotasıyla ~17 saat; temkinli hızla ~55 saat.
- **S2 özetle çözülmez.** Özette sözleşme/ihale/sipariş geçen 4.195
  "Özel Durum Açıklaması (Genel)" var (2020-01 → 2024-08: 2.630). Özet
  medyanı 49 karakter, tutar yok. Detay, yeni bir sınıflama şeması ve
  altın küme gerekiyor. LLM ~2,2 USD (2020–24) ya da ~3,4 USD (2020–26).
- **S3 ve S8'in verisi yok.** Yerelde pay adedi yok. Fon portföyü yalnız
  Ağustos 2026; 12 aylık geçmiş ~21.400 KAP isteği.
- **S7 zamana duyarlı.** Taban veri hazır, sonuç her gün birikiyor. Ön
  kaydı sonuç birikmeden yapılmalı.
- **Beklenmedik:** Y5 "hiç ölçülmedi" değil. 20 günlük CAR 19.09
  taramasında tedbir gruplarına göre raporlanmış (§5).

## 0. Ortak varsayımlar

### KAP isteği ve süre

Detay 1 istek (`istemci.detay`). Liste penceresi (3 gün) 1 istek. Koşu
başına 1 oturum ısıtması. Fon raporu detay + PDF eki, 2 istek (muaf fon
1).

| Senaryo | Saatte istek | Dayanak |
|---|---|---|
| Nominal, 2 sn aralık | 1.800 | `rejim_arsivi.KAP_ASGARI_ARALIK_MS` |
| Gözlenen WAF kotası | ~260 | `scripts/rejim_arsivi.py:86–88` ("yarım saatte ~130 isteklik kota"); 28.09 koşusu ~174 istek 41 dk (`data/rejim_kap5.log`) |
| Temkinli | ~80 | aynı yorum, `--aralik-ms 45000` |

Geçmiş: 24.09'da 1,2 sn aralıkla 129 pencere + 691 detay 13 dk 51 sn'de
indi, blok yok (`data/backfill_2024.log`). 27.09'da 2 sn'de 100
pencereden sonra blok (`data/rejim_kap.log`). Tablolarda süre üç
senaryoyla veriliyor (Sapmalar §6).

### LLM birim maliyeti

- **Fiyat** (USD / 1 M token, Eylül 2026): flash-lite 0,25 / 1,50;
  3.8-flash 0,75 / 3,75 (`scripts/cikarim_kosu.py:47–52`). 3.8-flash'ın
  tanıtım fiyatı 31.12.2026'da bitiyor, ikiye katlanıyor.
- **Ölçülen token** (`cikarim.girdi_token`, `cikti_token`, 28.09):
  flash-lite 1.384 çağrı, ortalama 1.418 girdi / 190 çıktı. 3.8-flash 50
  çağrı, 1.494 / 257. Yükselme %3,6.
- **Fatura:** 2024-09 backfill, 690 bildirim, 0,487 USD
  (`data/cikarim_2024.log`) → **0,000706 USD/bildirim**.
- **Sağlama:** 1.418 × 0,25 + 190 × 1,50 = 0,000640 USD/çağrı; üst model
  0,002084; %3,6 yükselmeyle **0,000715 USD/bildirim**. Fark %1.
- **Girdinin ~%80'i sabit prompt.** Boş prompt 3.360 karakter (~1.120
  token, 3 karakter/token). Bildirim metni ortalama 545, medyan 436, %90
  1.010 karakter (`bildirim.ham_metin_tr`). Metin uzunluğu maliyeti az
  oynatır.
- 31.12.2026'dan sonra üst model çift fiyat: ~0,00079 USD/bildirim.

## 1. Tek tabloda envanter

| # | Elde | Eksik | KAP isteği | LLM | İş |
|---|---|---|---|---|---|
| S1 | Liste, olaylar, bülten, TÜFE (2019-12 →) | 2020–24 detay, 2019–24 finansal rapor, 2020–24 TCMB kuru | ~4.400 | ~1,43 USD | L |
| S2 | Liste ve özetler | Detay, sınıflama şeması, altın küme | 2.630 / 4.195 | ~2,2 / ~3,4 USD | L |
| S3 | Bülten işlem adedi | Pay adedi, dolaşım oranı | ~1.600 (C) + S1'le birlikte | yok | M–L |
| S4 | Bülten paneli (getiri, 2020–26) | — | 0 | yok | S |
| S5 | Y5'in verisi + bülten en iyi alış/satış | Ayrıştırma; 122 olayda t+60 | 0 | yok | M |
| S6 | 2025 söz, 6A2026; 9A2026 CI ile gelir | 2024 sözü (S1'in alt kümesi), sektör | 505 + ~215 | ~0,36 USD | M |
| S7 | Ağustos 2026 fon haritası, tasfiye listesi | Sonuç (ileriye dönük) | 0 (+ ayda ~340 isteğe bağlı) | yok | M |
| S8 | Fon listesi 2025-08 → | 11.114 fon raporu | ~21.400 | yok | L |
| S9 | Bülten kapanış ve en iyi alış | Ayrıştırma, kod denetimi | 0 | yok | S–M |
| S10 | Devre kesici 2020–26, VBTS listesi, bülten evreni | VBTS detayı 2020-01 → 2023-08 | 0 (1.057 isteğe bağlı) | yok | S |
| S11 | Bülten: TL hacim, BIST 100/30, pazar | Sektör, pay adedi, 2020–24 skoru | ~215 + S1 | S1'e bağlı | M |
| S12 | Veritabanı | — | 0 | yok | S |
| Y3 | 2024–26: para birimi dolu | Kamu/özel, yurt dışı, süre alanı yok; 2020–24 metin | S1'le | ~0,15–2,35 USD | M |
| Y4 | 2024–26: 92 bağ, bayraklar | 2020–24 bayraklar (detayda), ihale detayları | S1'le + 784 | yok | M |
| Y5 | Bülten paneli, 3.091 olay | 122 olayda ufuk (~15.12.2026) | 0 | yok | S–M |
| Y6 | Saniye hassasiyetli yayın zamanı, 2020–26 | Seans saati tarihçesi | 0 | yok | S |

## 2. Kimlik kimlik

### S1 · Skor sınavları 2020–24'te (Bulgu 3, 4, 5, 11)

**Gereken:** 2020-01 → 2024-08 "Yeni İş İlişkisi" metinleri (tutar
çıkarımı için), point-in-time payda (TTM köprüsü: son yıllık rapor + son
ara dönem raporu), duyuru günü TCMB kuru, 2023 öncesi köprüler için TÜFE,
olay ölçüleri.

| Veri | Yer | Kapsam | Durum |
|---|---|---|---|
| Bildirim listesi | `data/ham_rejim/yeni_is_2020_2024.csv` | 2.019 bildirim, 174 kod, 02.01.2020 → 29.08.2024 | Var |
| Olay ölçüleri (AV, CAR3, V90) | `data/ham_rejim/k1_olaylar.csv` | 3.091 olay (A+B 1.850) | Var |
| Fiyat, hacim | `data/ham_rejim/panel.pkl` | 174 kodun 174'ü panelde | Var |
| Bildirim metni | `data/ham/detay/` | 1.304 dosya, hepsi oda-12000, 02.09.2024 → 18.09.2026 | **2020–24 için yok.** `data/ham_rejim/` altında detay klasörü yok |
| Finansal rapor | `finansal_donem`, `data/ham/finansal/` | Dönem sonu 2023 → 2026, yayın 07.09.2023 →; 1.624 dosya | **2019–2023/08 yok.** 174 kodun 103'ü `finansal_donem`de |
| TÜFE | `src/kap_radar/tufe_aylik.csv` | 2019-12 → 2026-08 (81 ay) | 2019-01 … 2019-11 eksik |
| TCMB kuru | `kur_gunluk`, `data/ham/kur/` | 23.08.2024 → | **2020-01 → 2024-08 yok** |

**Finansal rapor sayımı** (liste arşivi, konu "Finansal Rapor", 174
koddan biri `stockCodes`'ta): 2020 338, 2021 411, 2022 533, 2023 625,
2024 (Ocak–Ağustos) 390. Toplam 2.297, bunun 325'i arşivde. Çekilecek
1.972. Ocak–Mart 2020 bildirimlerinin köprüsü 2019 raporlarını istiyor
(FY2018, 9A2019). Liste arşivi 2019'u kapsamıyor.

**KAP çekimi:**

| Kalem | İstek | Nasıl sayıldı |
|---|---|---|
| Yeni İş detayı | 2.019 | csv satırı |
| Finansal rapor 2020-01 → 2024-08 | 1.972 | yukarıda |
| 2019 liste penceresi (3 gün) | 122 | 365 / 3 |
| 2019 finansal rapor | ~300 | tahmin: 2020'deki 338'den, o yıl borsada olmayan kodlar düşer |
| **Toplam** | **~4.400** | |

Süre: 2 sn'de ~2,5 saat · ~260/saat ile ~17 saat · 80/saat ile ~55 saat.
Ek olarak TCMB kuru 01.01.2020 → 22.08.2024 için ~1.696 istek
(tcmb.gov.tr, KAP değil; önceki koşularda blok görülmedi) ve TÜFE'ye 11
aylık satır (elle, TCMB tablosundan).

**LLM:** 2.019 × 0,000706 = **1,43 USD**. Girdi ~2,96 M, çıktı ~0,40 M
token (%3,5 yükselme dahil). Kaynak: `rejim_arsivi.py:72–77` ve
`data/rejim_kap5.log`. Token ortalaması veritabanında yeniden sayıldı,
aynı. **~1,43 USD doğrulandı.** Üst model fiyatı iki katına çıkarsa ~1,60
USD.

**Riskler:**

- 2020–22 raporları TMS 29'suz. `finansal.ttm_coz` bugün TÜFE'yi yalnız
  TMS 29 uygulayan şirkette kullanıyor. 2023 öncesi köprünün TÜFE ile
  taşınması bir yöntem kararı (enflasyon 2022'de %80'i aştı).
- Altın küme (50 bildirim) 22.09.2025 → 04.08.2026 arası. 2020–22
  metinlerinde çıkarım doğruluğu ölçülmedi; küçük bir elle etiketli
  örneklem gerekir (LLM ~0,04 USD).
- Liste kayıtlarında `isOldKap` hep false (3.323/3.323), yani detay uç
  noktası büyük olasılıkla aynı. 2020 şablonunun alan kodları
  doğrulanmadı: önce 5 detay çekilip ayrıştırıcıdan geçirilmeli.
- 174 kodun 70'i `sirket`te yok (borsadan çıkan ya da evren dışı).
  Finansal rapor süzgeci listeden yapılabiliyor, sorun değil.

**İş: L.**

### S2 · "Özel Durum Açıklaması (Genel)" içindeki sözleşme duyuruları

**Sayım** (liste arşivi, konu tam eşleşme; desen
`rejim_arsivi.SOZLESME_DESENI` özet üzerinde):

| Yıl | ÖDA Genel | Özette desen | Desen ∩ kaba gürültü | Desen, olumlu kalıp, gürültüsüz |
|---|---|---|---|---|
| 2020 | 5.685 | 423 | 196 | 109 |
| 2021 | 6.352 | 509 | 173 | 179 |
| 2022 | 6.810 | 646 | 231 | 240 |
| 2023 | 8.141 | 548 | 188 | 165 |
| 2024 | 9.081 | 725 | 216 | 206 |
| 2025 | 9.089 | 760 | 255 | 278 |
| 2026 (→ 19.09) | 7.038 | 584 | 216 | 205 |
| **Toplam** | **52.196** | **4.195** | 1.475 | 1.382 |
| 2020-01 → 2024-08 | | **2.630** | | 821 |

Kaba gürültü kalıbı: toplu iş sözleşmesi, kredi, kira, pay devri, devir
ve temlik, fesih, dava, lisans, bayilik, franchise… Olumlu kalıp:
sipariş, ihale, iş ilişkisi, yeni iş, tedarik, proje. İkisi de yalnız
kapsamı görmek için. Sınıflama değil.

**Özet yeter mi? Hayır.** Özet medyanı 49 karakter, %90'ı 109. En sık
özetler: "İhale sonrası Devir ve Temlik İşlemlerinin tamamlanması hk."
(67), "Toplu İş Sözleşmesi Görüşmeleri Hakkında" (65), "Sözleşme
İmzalanması" türü genel başlıklar. Özet işin türünü çoğu zaman söylemiyor,
tutarı hiç vermiyor. Özet yalnız kural tabanlı ön eleme için (bedava).

Ek gözlemler:

- Desenli 4.195'in 2.812'si şablonu hiç kullanmamış şirketlerden
  (bankalar, holdingler, varlık yönetim şirketleri), 1.383'ü "Yeni İş
  İlişkisi" de gönderen şirketlerden.
- 328'inin PDF eki var. Metin ekteyse ek indirme ve PDF ayrıştırma
  gerekir.
- 2024–26 için de ÖDA detayı yok: `data/ham/detay/` yalnız oda-12000.

**KAP:** 2.630 (2020–24) ya da 4.195 (2020–26) detay, artı en çok 328 ek.
Süre (4.195 için): ~2,3 saat · ~16 saat · ~52 saat. 2.630 için ~1,5 ·
~10 · ~33 saat.

**LLM:** Yeni bir prompt (sınıflama + tutar). ÖDA metin uzunluğu
bilinmiyor; yerelde tek ÖDA detayı yok, 20 örnekle ölçülür. Metin Yeni
İş'in üç katı (~1.800 girdi token) varsayımıyla ~0,00082 USD/bildirim →
**~2,2 USD (2.630) / ~3,4 USD (4.195)**. Asıl maliyet elle: şema ve altın
küme.

**Riskler:** Sınıflama şeması sonuçtan önce yazılmalı. "İhale kazanıldı"
ile "sözleşme imzalandı" ÖDA'da da iki adım (Y4). Şablonu kullanmayan
şirket kümesi farklı (bankalar), karşılaştırma bileşimi değişir.

**İş: L.**

### S3 · Dolaşımdaki paya oranlı hacim (turnover)

**Gereken:** Pay adedi (ya da ödenmiş sermaye) ve fiili dolaşım oranı,
point-in-time.

**Elde yok.**

- Bülten: işlem adedi ve TL hacim var; pay adedi, sermaye, dolaşım oranı
  sütunu yok (`thb*.zip` başlığı, 2020 ve 2026).
- `data/ham/evren/kapanis.csv`: yalnız kapanış fiyatı (2024-01-02 →).
- Finansal arşiv yalnız künye ve gelir tablosu saklıyor
  (`arsiv.py:153–156`). Bilançodaki ödenmiş sermaye yok.
- Liste arşivinde "Şirket Genel Bilgi Formu" 24.300 kayıt (174 kod için
  3.910), "Sermaye Artırımı - Azaltımı" 5.740. Detayları yok.

**Seçenekler:**

| Kaynak | Ne verir | İstek |
|---|---|---|
| Finansal rapor bilançosu, "Ödenmiş Sermaye" | Toplam pay (nominal 1 TL), çeyreklik | 2024–26: 1.624 rapor yeniden (~0,9 · ~6 · ~20 saat). 2020–24: S1'in finansal çekimi bilançoyu da saklarsa **ek istek yok** |
| MKK fiili dolaşım oranları | Serbest dolaşım | Bilinmiyor: geçmiş arşivi olup olmadığı MKK sitesinden öğrenilir (borsa sitesi değil ama bu görevde bakılmadı) |
| Şirket Genel Bilgi Formu detayı | Sermaye, ortaklık yapısı | 174 kod için 3.910 istek; alan yapısı doğrulanmadı |

**Risk:** Ödenmiş sermaye toplam payı verir, serbest dolaşımı değil.
Bedelsiz ve bölünmeler çeyrek içinde değişir.

**İş: M–L.** S1'le aynı çekimde yapılırsa M.

### S4 · Seyrek işlem betası (Dimson, Scholes-Williams)

**Hazır.** `data/ham_rejim/panel.pkl`: 855.631 pay-günü, 698 pay,
2020-01-02 → 2026-09-25, günlük getiri (`r`) ve marj. Piyasa getirisi
panelden eşit ağırlıklı (K1 ile aynı). XU100 veritabanında yalnız
2024-01-02 → (`endeks_gunluk`, 682 gün); 2020–23 için gerekirse yfinance
(bedava). KAP ve LLM yok.

**İş: S.**

### S5 · Bulgu 12'nin mekanizması: geri dönüş mü, alıcı azlığı mı

- **Geri dönüş kolu** Y5 ile aynı veri (aşağıda).
- **Alıcı azlığı kolu:** Bülten kapanıştaki en iyi alış ve satışı
  taşıyor (`BEKLEYEN EN IYI ALIS/SATIS`, 2020 ve 2026 başlıklarında var).
  `panel.pkl`'de yok; 1.690 zip yeniden ayrıştırılmalı (yerel, bedava).
  Veri varlığı örneği: 18.09.2026'da kapanışı ≤ −%9,5 olan 113 payın
  107'sinde en iyi alış boş ya da 0.
- 2023-02-08 gibi piyasa kapalı günlerde bütün satırlar `GECICI DURDURMA`.
  Ayrıştırıcı bunu ayırmalı.

**İş: M.**

### S6 · Söz ve gerçek: gecikme, ikinci dönem, sektör

| Kol | Veri | Durum |
|---|---|---|
| İkinci dönem (9A2026) | `finansal_donem`, CI günlük çekimi | Kendiliğinden gelir. 9A2025 yayınları (`finansal_donem`, dönem sonu 2025-09-30, 137 rapor): %10 30.10, medyan 07.11, %90 10.11, son 17.11.2025. **Beklenti ~30.10–10.11.2026**; `soz_gercek.KAPSAM_ORANI` (%90) ~10–11 Kasım'da dolar (tahmin) |
| Gecikme (söz 2024 → büyüme 2025/26) | 2024 sözü | 2024-09 → 12 veritabanında. Ocak–Ağustos 2024'ün 505 bildirimi S1'in alt kümesi: 505 detay, ~0,36 USD |
| Gecikme (söz 2025 → FY2026) | — | Mart 2027'de kendiliğinden |
| Sektör | `sirket.sektor` | **145 şirketin 145'inde boş.** Yerelde sektör yok |

**Sektör için bedava kaynaklar** (hiçbiri yerelde değil):

- Bülten sektör vermiyor. Yalnız `BIST 100 ENDEKS`, `BIST 30 ENDEKS`
  (günlük 0/1; 2026'da `BIST KATILIM TUM ENDEKS`) ve `PAZAR` (Z, N, T, W,
  S; kod eşlemesi doğrulanmadı).
- KAP şirket sayfası (sektör ve dahil olduğu endeksler; uç nokta ve alan
  adları doğrulanmadı): ~215 istek (174 kod ∪ 145 şirket).
- yfinance `info["sector"]`: pay başına 1 istek. Borsadan çıkanlarda
  büyük olasılıkla yok. Sınıflama Yahoo'nun.
- Borsa İstanbul sektör endeksi bileşenleri: borsa sitesi, bu görevde
  bakılmadı.

**İş: M** (sektör dış kaynak; ikinci dönem S).

### S7 · Tasfiye baskısı altındaki payların sonraki seyri

**Taban hazır:**

| Tablo | Kapsam |
|---|---|
| `hisse_fon_guncel` | 560 pay; 266'sında `tasfiye_tl` > 0; hesap 23.09.2026, son rapor dönemi 2026-09 |
| `tasfiye_kurulus` | 7 portföy şirketi, karar 17.09.2026 |
| `fon_raporu` | Ağustos-2026 417, Eylül-2026 104, Temmuz-2026 1, dönemsiz 462 (343 hisse yok, 73 muaf, 41 tutarlı, 5 tutarsız) |
| `fon_pozisyon` | 7.331 satır, 384 rapor, 568 pay |
| `data/fon_baski.csv` | 268 pay, 22.09 (izlenmeyen dosya) |

**Sonuç değişkeni:** Günlük bülten (Borsa İstanbul, günde 1 istek; KAP
değil). SPK tasfiye süresini 6 aya uzattı (geçerlilik notu §9) → gözlem
~Mart 2027'ye kadar. İsteğe bağlı: 7 şirketin ~170 fonunun aylık raporu
(`data/fon_cek.log`), ayda ~340 KAP isteği (tahmin).

**Risk:** İleriye dönük doğal deney. 17–25 Eylül'ün sonucu zaten bültende.
Ön kayıt ne kadar geç yazılırsa o kadar çok sonuç görülmüş olur.

**İş: M.** Zamana duyarlı.

### S8 · "Sakin yükseliş" parmak izi

**Gereken:** Pay × ay fon pozisyonu (en az 3 dönem), oynaklık, fiyat,
etiket.

- **Fon geçmişi yok.** Fon liste arşivi `data/ham/fon/liste/` 153 dosya,
  2025-08-01 → 2026-09-23, 98.173 kayıt. `fon_arsiv.secilecekler`
  kuralıyla (hisse tutabilen fon, ayda tek rapor) 12.025 fon × ay. PDF ya
  da muaf işareti olan yalnız 911 (Ağustos 2026 dönemi).
- Çekilecek 11.114 rapor. Ağustos 2026'da muaf oranı 73/984 → **~21.400
  istek.** Süre ~12 saat · ~82 saat · ~268 saat. Bağlam notundaki "F1,
  ~2 saat" tahmini bu hesabın çok altında.
- 2025-08 öncesi fon listesi de yok. Fon listesi günde 2.000 sınırına
  dayanabiliyor (`data/fon_cek.log`: 08.07.2026).
- Oynaklık (devre kesici) ve fiyat (bülten) hazır.
- **Etiket kaynağı** (liste arşivi, bedava): "Sermaye Piyasası Kurulu
  Tedbir Kararı" 184, "SPK İşlem Yasağı Nedeniyle Pay Duyurusu" 171,
  "Pay İşlem Sırası Kapatma / Açma" 279 (2020–26).

**İş: L.** Kapsam 7 portföy şirketine daraltılırsa M.

### S9 · Tabanda kilitli tahtalar Bulgu 10–12'de nasıl sınıflandı

- Metodoloji sınırı açıkça yazıyor: "kilitli tahtadan gelen bildirimlerin
  o sınavlarda nasıl sınıflandığı ayrıca denetlenmedi"
  (`site/content/metodoloji.html:951`).
- **Veri hazır:** Bülten kapanış, önceki kapanış ve en iyi alış
  (2020–26, S5'teki ayrıştırma). 2024–26 için `fiyat_gunluk`
  (2024-01-02 →, 145 pay). `tahta_durumu` 1.317 bildirim (temiz 491,
  hareketli 461, tedbirli 365; hepsi `kap_v1`).
- `hisse_limit_gunleri` görünümü yalnız son 60 gün. Geçmiş için
  kullanılamaz.
- İş çoğunlukla kod denetimi: bildirimin tahta sınıfı ile önceki 90 günde
  tabanda alıcısız kapanış sayısının çapraz tablosu.

**İş: S–M.**

### S10 · Devre kesici ve VBTS başlangıcı; evrene göre normalizasyon

**Devre kesici** (konu "Pay Bazında Devre Kesici Bildirimi"):

| Yıl | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Kayıt | 15.854 | 10.366 | 9.350 | 22.370 | 12.038 | 10.538 | 10.106 |
| Bülten ort. pay sayısı | 405 | 421 | 471 | 512 | 562 | 590 | 613 |

- İlk kayıt 02.01.2020 10:00:30, arşivin ilk günü. Kayıt 2020 boyunca var.
  **K1 §8'deki "2020 başlangıç tarihleri doğrulanmadı" sınırı kapanabilir.**
  Sistemin kuruluş tarihi arşivden önce, bilinmiyor; 2020–26 penceresi
  için gerekmiyor.
- Hisse kodu `relatedStocks`'ta: 90.622 kaydın 90.534'ü (%99,9). Kaydın
  `stockCodes`'u hiç dolu değil.
- **Normalizasyon paydası hazır:** bültende günlük pay sayısı 409
  (02.01.2020) → 631 (25.09.2026) (`panel.pkl`).

**VBTS** (özette "Volatilite Bazlı Tedbir"):

- Liste 2.143 kayıt, 02.01.2020 → 15.09.2026, hepsinde `relatedStocks`.
- Detay (kademe, başlangıç–bitiş) yalnız 01.09.2023 → (`data/ham/vbts/detay/`,
  1.086 dosya). 2020-01 → 2023-08 için 1.057 istek (~0,6 · ~4 · ~13
  saat).
- **Bedava vekil:** Bülten günlük `BRUT TAKAS` bayrağı taşıyor (örnek
  günlerde 44 / 80 / 90 pay: 16.03.2020, 08.02.2023, 18.09.2026). VBTS 2.
  kademe ile SPK brüt takas kararını ayırmıyor; doğrulanmadı.

**Kural değişiklikleri:** Fiyat marjı 13.03.2020'de ±%20 → ±%10 (K1 §2).
Duyuru ifadesi Ocak 2026'da değişti (veri denetimi §3). Devre kesici
eşiklerinin 2020–26 tarihçesi yerelde yok.

**İş: S.**

### S11 · Akran grubunda sektör ya da büyüklük bandı

- Bugünkü akran grubu: aynı S kademesi × aynı tahta; hücre 20'nin altına
  düşerse yalnız kademe (`metodoloji.html:959`).
- **Büyüklük bandı bedava:** Bülten TL hacim, BIST 100/30 üyeliği ve
  pazar, 2020–26 günlük. Piyasa değeri pay adedi ister (S3).
- **Sektör:** S6 ile aynı dış kaynak.
- 2020–24'e uzatmak skor kademesi ister, yani S1.

**İş: M.**

### S12 · KDV dahil tutarlar (31), bayraksız aynı tutarlı tekrarlar (13)

**Liste repoda kalıcı değil.** İkisi de `scripts/veri_denetimi.py`'nin
çıktısı; bugün yeniden koşuldu (1.317 bildirim, 947 skorlu), sayılar
26.09 ile aynı.

- **Bayraksız 13:** `veri_denetimi.py --liste 40`, bölüm 3. ASELS
  03.03→13.08.2025; BVSAN 28.05.2025→13.04.2026; HRKET 4 çift (2025);
  BOBET 22.07→09.12.2025; EUPWR 20.02→15.06.2026; MACKO 3 çift
  (Aralık 2024, Kasım 2025); KAYSE 12→13.02.2025; BURVA 21.07→12.09.2025.
- **KDV dahil 31:** Betik yalnız sayıyor (bölüm 5; 3'ünde kademe
  değişir). Liste, yayındaki skorlu çıkarımlarda
  `denetim.kdv_dahil_mi(alinti)` sorgusuyla çıkıyor. 31'in hiçbirinin
  metninde KDV oranı geçmiyor (kaba kalıp: "%n KDV", "KDV oranı %n").
  Düzeltme ya dış bir oran varsayımı ya da 31 elle okuma ister.

**İş: S** (44 bildirim elle okuma; KAP ve LLM yok).

### Y3 · Bildirimin içeriği: para birimi, kamu/özel, yurt dışı, süre

**2024–26, veritabanı** (1.317 bildirim; son çıkarım satırı):

| Alan | Yer | Dolu |
|---|---|---|
| Para birimi | `cikarim.veri->'tutarlar'[].para_birimi` | Tutarlı 1.066. USD 516, TRY 333, EUR 164, karışık 49, diğer 4; tutarsız 251. Yayındaki 947 skorluda döviz 636, TRY 290, karışık 21 |
| Tutar gizli | `cikarim.veri->'tutar_gizli'` | 1 |
| Karşı taraf niteliği | `bildirim.kap_alanlari->>'karsi_taraf_niteligi'` | 1.317: Müşteri 1.200, Tedarikçi 69, Diğer 48. **Kamu/özel değil** |
| Karşı taraf adı | `kap_alanlari->>'karsi_taraf'`, `karsi_taraf_acik` | Dolu 880, gerçek isim 625. Kurum kalıbı (`karsi_taraf._KURUM`) 178 |
| Kamu/özel | — | **Kolon yok.** Metinde "kamu" kalıbı işe yaramaz: "kamuya açıklanmıştır" kalıp cümlesi |
| Yurt dışı | — | **Kolon yok.** Kaba kalıp: `hap_ozet` 357, metin 425 |
| Süre | — | **Kolon yok.** Şablonun 19 alanında süre ya da bitiş yok (`data/ham/detay/` 1.304 dosya, `ayristirici.xbrl_alanlari`). `baslangic` 1.165 dolu. Metinde süre kalıbı 118 |
| Müşterinin satışlardaki payı | `ham_govde_html` (oda_IfExistsShareOfCustomer…) | Detayların 196/1.304'ünde dolu, kolona alınmamış |

**2020–24 için:** S1'in detay çekimi (ek istek yok). Para birimi S1'in
tutar çıkarımıyla bedava gelir. Kamu/özel karşı taraf adından kural
tabanlı çıkarılabilir (bedava). Yurt dışı ve süre bir LLM alanı ister:

- S1 prompt'una alan eklemek: çıktı ~+50 token → ~+0,15 USD; ama prompt
  değişikliği altın kümede yeniden ölçülmeli (~0,04 USD, 26.09 kuralı).
- Ayrı bir geçiş (2020–26, 3.323 bildirim): ~2,35 USD.

**İş: M.**

### Y4 · İki adımlı duyurular; güncelleme ve düzeltmelerin kendi tepkisi

**2024–26, veritabanı:**

| Kaynak | Sayı |
|---|---|
| `bildirim.guncelleme_mi` | 141 |
| `bildirim.duzeltme_mi` | 16 |
| `onceki_aciklama_tarihleri` dolu | 176 |
| `ilgili_kap_id` dolu | 0 |
| `bildirim_bag` | 92: güncelleme 67 (tarihle 63, tutarla 4), aynı iş 18 (16 + 2), düzeltme 7 |

Bağlar yalnız "Yeni İş İlişkisi" içinde. İhale → sözleşme ayrı bir tür
değil; ikisi de şablonla geldiyse "aynı iş" olarak bağlanıyor.

**2020–24, liste:** Güncelleme ve düzeltme bayrağı listede yok.
`modifyStatus` bütün "Yeni İş İlişkisi" kayıtlarında boş (arşivde
başka konularda 11.164 kez dolu), `isLate` hep false. Özette
"güncel" / "düzelt" geçen 30 / 8 (2020-01 → 2024-08, 2.019 kayıt). **Bayraklar S1'in
detayıyla gelir** (ek istek yok).

**İhale adımı:** "İhale Süreci / Sonucu" 1.348 kayıt (2020-01 → 2024-08:
784). Aynı şirketin önceki 180 günde ihale bildirimi (konu ya da ÖDA
özetinde "ihale") olan "Yeni İş": 2020–24'te 619/2.019, 2024–26'da
308/1.304. Bu eşleşme değil, yalnız üst sınır. Çift kurmak metin ister:
ihale detayı 784 istek (~0,4 · ~3 · ~10 saat), 2024–26 için 564 daha.

**İş: M.**

### Y5 · Uzun ufuk, t+3 … t+60

- **Hazır:** `panel.pkl` son gün 25.09.2026. `k1_olaylar.csv` 3.091 olay,
  t0 02.01.2020 → 21.09.2026.
- **Ufku dolmamış olay** (t0'dan sonraki bülten günü sayısı):

  | Ufuk | t+10 | t+20 | t+40 | t+60 | t+120 |
  |---|---|---|---|---|---|
  | Dolmamış | 13 | 27 | 71 | **122** (t0 ≥ 03.07.2026) | 252 |

  t+60'ın hepsi için günlük bülten ~15.12.2026'ya kadar (60 işlem günü,
  29 Ekim tatili; tahmin). Bülten Borsa İstanbul'dan, günde 1 istek.
- **Önceki bakış var** (§5): 20 günlük CAR 19.09'da gösterildi.

**İş: S–M.**

### Y6 · Zamanlama: seans içi / sonrası, Cuma, aynı güne yığılma

- **Yayın zamanı saniye hassasiyetli, 2020–26 boyunca.** Liste
  `publishDate` "GG.AA.YYYY SS:DD:ss". Saniyesi sıfır olmayan kayıt payı
  her yıl %98,3–98,5 (tekdüze dağılımda beklenen 59/60 = %98,3). "Yeni
  İş" kayıtlarında 2020'de 143/146, 2026'da 382/388. Veritabanında
  `bildirim.yayin_zamani` 1.301/1.317.
- Aynı güne yığılma: listeden günlük bildirim sayısı (medyan 199, en çok
  1.282), bedava.
- **Eksik:** Seans kapanışı kodda sabit 18:10 (`tepki.SEANS_KAPANIS`).
  2020–26 seans saati değişiklikleri ve yarım günler yerelde yok;
  Borsa İstanbul duyurularından doğrulanmalı (bilinmiyor).
- Ertelenmiş açıklama bayrağı (`oda_DelayedAnnouncementFlag`) yalnız
  detayda: 1.304'te 13 "Evet". Kolona alınmamış.

**İş: S.**

### Y1, Y2, Y7, Y8 · Dalga 1'de

- **Y1, Y2:** D1-P. Veri (`panel.pkl`, `k1_olaylar.csv`) hazır; ücret yok.
- **Y7:** D1-L. Veri gerekmiyor.
- **Y8:** Veri maliyeti yok. Gereken şey sınav ailesinin kaydı: her
  notun sınavları ve t/p değerleri tek tabloda. Bugün notlara dağınık.

## 3. Dalga 2 için sıralama önerisi

İlke: bedava ve hazır olan önce; zamana duyarlı olan en önce.

1. **Hemen, zamana duyarlı:** S7. Taban hazır, sonuç birikiyor.
2. **Hazır, çekimsiz, LLM'siz:**
   - Y5 ve S5'in geri dönüş kolu. Ufku dolmuş 2.969 olayla; t+60 eksiği
     sapma olarak yazılır ya da Aralık'ta tamamlanır.
   - S4 (seyrek işlem betası).
   - S10 (normalizasyon; 2020–23 VBTS için bülten brüt takas vekili).
   - S9 ve S5'in alıcı azlığı kolu (tek bülten ayrıştırması ikisine de
     yeter).
   - Y6.
   - S12 (44 bildirim elle).
   - Y3 ve Y4'ün 2024–26 kısmı (tek rejim; para birimi ve 92 bağ).
3. **Kasım'da kendiliğinden:** S6'nın ikinci dönemi. Ön kaydı 9A2026
   raporları gelmeden (~30 Ekim) yazılmalı.
4. **Bedava ama KAP çekimi, LLM yok:** S10 VBTS detayı (1.057), Y4 ihale
   detayları (784), sektör (~215), S3 bilanço (2024–26: 1.624).
5. **KAP + ücret, tek paket:** S1 paketi. Aynı çekimde S1, Y3 ve Y4'ün
   2020–24 kısmı, S6'nın gecikme kolu, S11'in kademesi, S3'ün 2020–24
   bilançosu. ~4.400 istek, ~1,43 USD (+ Y3 alanları ~0,15 USD).
6. **Sonra:** S2 (yeni şema + altın küme). En son S8.

## 4. Hüseyin'in kararını gerektirenler

| # | Karar | Maliyet |
|---|---|---|
| 1 | S1 paketi: 2020–24 detay + finansal rapor çekimi ve tutar çıkarımı | ~1,43 USD (Gemini, mevcut hesap) + ~4.400 KAP isteği + ~1.700 TCMB isteği |
| 2 | 2023 öncesi TTM köprüsünde TÜFE (yöntem) | ücretsiz; 2019 TÜFE satırları elle |
| 3 | KAP çekim hızı: 45 sn (güvenli, S1 ~55 saat) mi, kotaya göre mi (~17 saat) | süre ve blok riski |
| 4 | MKK API Portalı hesabı (KAP veri yayın servisleri; geçerlilik §10) | hesap açma; kotası bilinmiyor |
| 5 | S2: kapsam (2020–24 mü, 2020–26 mı), sınıflama şeması, altın küme etiketi | ~2,2 / ~3,4 USD + 2.630 / 4.195 istek + elle etiket |
| 6 | Y3 alanları: S1 prompt'una mı (altın küme yeniden ölçümü ~0,04 USD) ayrı geçiş mi (~2,35 USD) | küçük |
| 7 | S3 kaynağı: finansal rapor bilançosu mu, MKK dolaşım oranı mı | 1.624 istek ya da bilinmiyor |
| 8 | S8 kapsamı: tüm piyasa 12 ay mı (~21.400 istek), 7 portföy şirketi mi | süre |
| 9 | Sektör kaynağı (S6, S11): KAP şirket sayfası, yfinance ya da BIST sektör endeksleri | ücretsiz, dış kaynak seçimi |
| 10 | S7 ön kaydının zamanı | bekledikçe görülen sonuç artar |

## 5. Beklenmedik ya da şüpheli

- **Y5 önceden bakılmış.** Harita "3 günden sonrası hiç ölçülmedi"
  diyor. `data/ozellikler.csv` (612 olay, 2025-09 →) `car_10g` ve
  `car_20g` taşıyor (`scripts/ozellik_kur.py:187–188`). 19.09 taraması
  tedbir gruplarına göre 20 günlük CAR'ı raporlamış
  (`2026-09-19-skor-kanit-taramasi.md` §3; β = 1 dönemi). Y5'in ön kaydı
  bu önceki bakışı yazmalı.
- **S10'un sınırı kapanabilir.** Devre kesici ve VBTS kayıtları arşivin
  ilk gününden (02.01.2020) var.
- **Bülten bedava vekiller taşıyor, panele alınmamış:** brüt takas, BIST
  100/30 üyeliği, pazar, kapanıştaki en iyi alış/satış, geçici durdurma.
- **`sirket.sektor` kolonu tasarımda var, 145 şirketin hiçbirinde dolu
  değil.**
- **Maliyet yorumları eskimiş.** `scripts/gunluk.py` başlığı "~0,0001
  USD/bildirim" diyor; ölçülen ~0,0007 (7 kat). Bağlam notundaki F1
  "~2 saat çekim" 12 aylık fon arşivi için ~21.400 istek demek.
- **Listede güncelleme bilgisi yok.** `modifyStatus` ve `isLate` "Yeni İş
  İlişkisi"nde hiç dolu değil. 2020–24 bayrakları ancak detayla gelir.
- **Desenli ÖDA'nın üçte ikisi şablonu hiç kullanmamış şirketlerden**
  (2.812/4.195). S2 başka bir şirket kümesini ölçebilir.
- **Altın küme tek dönemden** (22.09.2025 → 04.08.2026). Çıkarım
  doğruluğunun eski metinlerde geçerli olduğu varsayım.
- Yerel liste arşivi 19.09.2026'da bitiyor; veritabanı 28.09'a kadar
  (CI önbelleği). Yerel sayımlarla veritabanı sayımları arasında 13
  bildirimlik fark bundan.

## 6. Sapmalar

1. **KAP süresi üç senaryoyla.** §6 "2 sn aralıkla süre" istiyor. 2 sn'in
   WAF altında sürdürülemediği repoda kayıtlı (`rejim_arsivi.py:86–88`).
   Yalnız 2 sn yazmak süreyi ~7 kat iyimser gösterirdi. 2 sn değeri her
   satırda duruyor.
2. **Kaba kalıplar.** S2'nin gürültü/olumlu kalıbı ve Y3'ün metin
   kalıpları yalnız kapsamı göstermek için. Sınıflama ya da sonuç değil;
   Dalga 2'de kullanılmamalı.
3. **Yardımcı betikler repoda değil.** §7 yalnız bu notu oluşturmaya izin
   veriyor. Sorgular ve dosyalar metinde.
