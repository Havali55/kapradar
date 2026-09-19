# KAP Radar — Tasarım Spesifikasyonu (A sürümü)

Tarih: 2026-09-17 · Durum: tasarım onaylandı, inşa edilmedi
Güncelleme 2026-09-18: açık üç karar kapatıldı (kapı katı, skor ağırlıkları,
rota önceliği) — §6, §8, §11.
Önceki proje: `C:\Yazilim\mezun-atlas` (rafta, dokunulmuyor)

---

## 1. Tek cümle

**KAP bildirimi düşer, 10 saniye içinde ne anlama geldiği yayında olur.**

KAP bildirimleri ham metindir: "45.200.000 USD tutarında sözleşme imzalanmıştır."
Bu sayının büyük mü küçük mü olduğunu, şirketin cirosuna göre ne ifade ettiğini,
geçmişte benzer açıklamalardan sonra ne olduğunu söyleyen bir yer yok.
Biz o dönüşümü yapıyoruz.

## 2. Ne ChatGPT'nin yapamadığı

Tek bildirimi ChatGPT'ye yapıştırıp özet istemek mümkün. Yapamadığı üç şey:

1. **Ciroya oran** — şirketin son 4 çeyrek hasılatını bilmek ve bildirim tarihli
   TCMB kuruyla çevirip bölmek gerekir. Veritabanı işi.
2. **Geçmiş karne** — "bu şirket son 12 ayda 4 benzer iş açıkladı, toplam 142M USD".
   Geçmiş bildirim arşivi olmadan üretilemez.
3. **Anormal getiri** — "benzer açıklamalar sonrası ilk 3 işlem günü BIST100'den
   arındırılmış ortalama tepki +%2.40". Fiyat serisi + endeks serisi + doğru t0 gerekir.

Üçü de veri varlığı gerektiriyor. Ürünün savunma hattı prompt değil, veritabanı.

## 3. Kapsam — A sürümü (MVP)

**İçinde:**
- Tek şablon: **Yeni İş İlişkisi**
- 12 aylık geçmiş backfill (**gerçekleşen: 613 bildirim**, Adım 4)
- Çıkarım hattı + doğrulama kapısı + katmanlı model yönlendirme
- Günlük kapanış fiyat batch'i + CAR (anormal getiri) hesabı
- Bildirim sayfası + hisse sayfası (Next.js, ISR)
- X botu: Pillow ile üretilen görsel kart + hap metin

**Dışında:** Pay Geri Alım şablonu, Telegram botu, sektör sayfaları, e-posta
bülteni, kullanıcı hesabı, gerçek zamanlı fiyat, karşılaştırma sayfaları.

**Kabul kriteri:** Hiçbir sayfada doğrulama kapısından geçmemiş sayı yayınlanmaz.
Her sayı kaynak KAP linki + çekim zamanı + model/prompt versiyonu taşır.
Her sayfa ve her tweet "yatırım tavsiyesi değildir" künyesi taşır.

## 4. Mimari

```
VPS (Hetzner ~5 EUR/ay, systemd, Python 3.13)
├─ poller       : KAP'ı dinler → yeni bildirim id'leri
├─ cekici       : ham metin/HTML → DB (idempotent, ON CONFLICT DO NOTHING)
├─ router       : şablon eşleşmesi; "Yeni İş İlişkisi" dışı arşivlenir, işlenmez
├─ on_eleme     : regex — sayı yok / "ticari sır" → LLM'e hiç gitmez
├─ cikarim      : katmanlı model yönlendirme (§7)
├─ dogrulama    : programatik kapı (§6) → yayina_hazir bayrağı
├─ hesap        : TL çevrimi, ciro oranı, skor (§8) — deterministik
├─ fiyat_batch  : seans sonrası cron, günlük kapanış + XU100 + CAR
└─ yayinci      : Pillow görsel kart → X API → Vercel on-demand revalidate
        ↓
   Supabase (Postgres)
        ↓
   Vercel / Next.js (Server Components, ISR)
```

Ayrım net: **VPS veri üretir, Vercel veri gösterir.** Site canlı kaynağa hiç
bağlanmaz, yalnızca Postgres okur. Çekiciler kırılsa site ayakta kalır.

## 5. Veri modeli

```sql
sirket (
  ticker                  text PRIMARY KEY,   -- ASELS
  ad                      text NOT NULL,
  sektor                  text,
  son_yillik_hasilat_tl   numeric,            -- son 4 çeyrek toplamı
  hasilat_donemi          text,               -- "2025/12" 
  hasilat_kaynak          text                -- KAP finansal rapor linki
);

bildirim (
  kap_id        text PRIMARY KEY,             -- KAP'ın kendi id'si
  ticker        text REFERENCES sirket,
  sablon        text NOT NULL,
  yayin_zamani  timestamptz NOT NULL,
  baslik        text,
  ham_metin     text NOT NULL,
  kaynak_url    text NOT NULL,
  cekildi_at    timestamptz DEFAULT now()
);

cikarim (                                     -- APPEND-ONLY, versiyonlu
  id              bigserial PRIMARY KEY,
  kap_id          text REFERENCES bildirim,
  model           text NOT NULL,              -- "gemini-3.1-flash-lite"
  katman          smallint NOT NULL,          -- 1 | 2 | 3
  prompt_versiyon text NOT NULL,
  sema_versiyon   text NOT NULL,
  veri            jsonb NOT NULL,
  guven           text NOT NULL,
  yayina_hazir    boolean NOT NULL,
  red_nedeni      text,
  olusturuldu_at  timestamptz DEFAULT now()
);

fiyat_gunluk  (ticker, tarih, kapanis_duzeltilmis, hacim,  PRIMARY KEY (ticker, tarih));
endeks_gunluk (tarih PRIMARY KEY, xu100_kapanis);
kur_gunluk    (tarih, para_birimi, tl_karsiligi,           PRIMARY KEY (tarih, para_birimi));
altin_kume    (kap_id PRIMARY KEY REFERENCES bildirim, elle_dogrulanmis jsonb NOT NULL);
```

Üç tasarım kararı:

- **`bildirim.kap_id` = KAP'ın kendi id'si.** Idempotency tek satırla çözülüyor:
  `ON CONFLICT DO NOTHING`. Poller çökse, tekrar çekse, backfill canlıyla
  çakışsa mükerrer kayıt oluşmaz.
- **`cikarim` append-only.** Prompt veya şema değişince yeni satır yazılır,
  eski silinmez. "Bu sayfadaki sayıyı hangi model, hangi prompt, hangi şema
  üretti" her zaman cevaplanabilir. Yayında olan = o `kap_id` için
  `yayina_hazir=true` olan en son satır.
- **`altin_kume` ayrı tablo.** Elle doğrulanmış gerçek; çıkarım hiçbir zaman
  buraya yazmaz. Doğruluk ölçümünün referansı.

## 6. Çıkarım şeması ve doğrulama kapısı

**Revizyon 2026-09-18.** Adım 0'da şablonun yapılandırılmış olduğu görüldü
(§9). Şema ikiye ayrıldı: KAP'ın kendi XBRL alanlarından **deterministik**
gelenler ve LLM'in serbest metinden çıkarması gerekenler.

```python
# --- A) KAP'ın yapılandırılmış alanları: LLM YOK, doğrudan ayrıştırma ---
class KapAlanlari(BaseModel):
    karsi_taraf: str | None          # oda_NameSurnameOrCompanyTitleOf...
    karsi_taraf_niteligi: str | None # oda_NatureOfTheOtherParty... ("Müşteri")
    baslangic: date | None           # oda_ExpectedStartingDateOf...
    sozlesme_kosullari: str | None   # oda_IfExistSignificantProvisions...
    sirket_etki_beyani: str | None   # oda_ImpactOfNewBusinessRelation...
    guncelleme_mi: bool              # oda_UpdateAnnouncementFlag
    duzeltme_mi: bool                # oda_CorrectionAnnouncementFlag
    onceki_aciklama_tarihleri: list[date]  # oda_DateOfThePrevious...

# --- B) LLM'in tek işi: serbest metindeki tutarlar ---
class Tutar(BaseModel):
    deger: float
    para_birimi: Literal["TRY", "USD", "EUR", "DIGER"]
    tip: Literal["ilave_siparis", "fiyat_farki",
                 "toplam_sozlesme", "tek_seferlik"]
    alinti: str                      # geldiği cümle, BİREBİR

class TutarCikarimi(BaseModel):
    tutarlar: list[Tutar]            # boş olabilir (tutar açıklanmamışsa)
    tutar_gizli: bool                # "ticari sır niteliğindedir"
    hap_ozet: list[str] = Field(min_length=3, max_length=3)
    guven: Literal["yuksek", "orta", "dusuk"]
```

**Neden etiketli liste.** Gerçek bildirimler tek sayı içermiyor. `1665567`
(ORGE) örneğinde ilave sipariş 863.000 EUR, fiyat farkı 44.645.758 TL,
revize toplam sözleşme 10.842.903 EUR + 178.397.470 TL. Artış ile kümülatif
bedel karıştırılırsa ciro oranı ~12 kat şişer. `tip` etiketi bu ayrımı
şemaya taşıyor; hangi tipin skora gireceği §8'de **deterministik** kural.

`karsi_taraf_tipi` (kamu/özel/yurtdışı/ilişkili) artık LLM'e sorulmuyor:
KAP'ın `karsi_taraf_niteligi` alanı + şirket unvanı üzerinden kural tabanlı
eşleme yapılır, belirsizse `bilinmiyor` kalır ve skorun o bileşeni düşer.

**LLM aritmetik yapmaz.** Ciro oranı, TL çevrimi, skor şemada yok — hepsi §8'de
deterministik kod. LLM'in tek işi metinden tutar çıkarmak.

**Dil ayrımı zorunlu.** `oda_ExplanationTextBlock` Türkçe ve İngilizce metni
aynı blokta taşıyor. Ayrıştırıcı LLM'e **yalnızca Türkçe kısmı** vermeli;
yoksa her rakam iki kez görünür ve alıntı kapısı yanlış eşleşir.

`*_alinti` alanları doğruluk omurgası. Her sayı ve her isim için bildirimden
birebir alıntı isteniyor, sonra programatik kapı çalışıyor:

Kapı iki aşamalı, çünkü bir kontrol §8 hesaplarına ihtiyaç duyuyor.

**Aşama A — metin kapısı** (çıkarımdan hemen sonra, hesaplardan önce):

Kapı artık **her `Tutar` kalemi için ayrı ayrı** koşar; bir kalem düşerse
bildirimin tamamı düşer (§6 katı kapı kararı).

| # | Kontrol | Sonuç |
|---|---|---|
| A1 | Kalemin `alinti`'sı normalize edilmiş **Türkçe** metinde geçiyor mu? | Geçmiyorsa halüsinasyon → **RED** |
| A2 | Alıntıdaki sayı, kalemin `deger` alanıyla uyuşuyor mu? | Uyuşmuyorsa → **RED** |
| A3 | Alıntıdaki para birimi, kalemin `para_birimi` alanıyla uyuşuyor mu? | Uyuşmuyorsa → **RED** |
| A4 | `tutar_gizli=true` ama `tutarlar` dolu mu? | Çelişki → **RED** |
| A5 | Aynı `(para_birimi, tip)` çiftinde birden çok kalem var mı? | Belirsiz → **RED** |
| A6 | `guven == "dusuk"` mü? | **RED** |

A3 eski şemadaki "karşı taraf alıntısı" kontrolünün yerini aldı: karşı taraf
artık KAP'ın yapılandırılmış alanından geldiği için doğrulanacak bir
halüsinasyon yok. Serbestleşen kontrol para birimi eşlemesine verildi —
çok para birimli bildirimlerde asıl hata kaynağı orası.

Aşama A'da RED → Katman 2'ye yükselt (§7). Katman 2 de RED verirse elle kuyruğa.

**Aşama B — tutarlılık kapısı** (§8 hesapları koştuktan sonra):

| # | Kontrol | Sonuç |
|---|---|---|
| B1 | Hesaplanan ciro oranı > %200 mü? | Şüpheli → **elle kuyruğa**, yayınlanmaz |
| B2 | Bildirim tarihine ait TCMB kuru bulunabildi mi? | Bulunamadıysa → **elle kuyruğa** |

Aşama B'de RED → yükseltme yapılmaz (model hatası değil, veri şüphesi);
doğrudan elle inceleme kuyruğuna düşer.

Kapıdan geçmeyen hiçbir çıkarım yayınlanmaz: sayfa basılmaz, tweet atılmaz.
Yanlış bir sayının bir kez yayınlanması bu tür bir ürüne güveni tek başına
bitirir.

**Karar (2026-09-18): kapı bu katılıkta kalıyor.** Kısmi yayın (tutar gizlenip
bildirimin yine de yayınlanması) ve A3/A6 redlerinin uyarıya düşürülmesi
seçenekleri reddedildi. Yanlış-red kabul edilen maliyet; kapsama uğruna
gevşetme yapılmaz.

Normalizasyon notu: alıntı karşılaştırması öncesi hem alıntı hem ham metin için
boşluk daraltma, binlik ayırıcı normalizasyonu (`45.200.000` / `45,200,000` /
`45 200 000`) ve **Türkçe noktasız ı indirgemesi** (`İ/I/ı → i`) uygulanır.
`"ASELSAN".casefold()` → `aselsan` ama `"Yazılım".casefold()` → `yazılım`;
normalize edilmezse tam da manşet şirketlerde eşleşme sessizce başarısız olur.

## 7. Katmanlı model yönlendirme

Doğrulama kapısı (§6) aynı zamanda bedava bir güven sinyali. Yönlendirici olarak
kullanılıyor:

| Katman | Model | Girdi | Beklenen hacim |
|---|---|---|---|
| 0 | regex ön eleme | — | ~%20 (LLM'e hiç gitmez) |
| 1 | `gemini-3.1-flash-lite` | $0.25 / $1.50 per 1M | ~%85 |
| 2 | `gemini-3.8-flash` | $0.75 / $3.75 per 1M | ~%13 |
| 3 | elle inceleme kuyruğu | — | ~%2 |

Katman 3 yerine `claude-opus-5` ($5 / $25) opsiyonel olarak konabilir; A
sürümünde konmuyor.

Çıkarım adaptörü sağlayıcı-bağımsız arayüzün arkasında:

```python
class Cikarici(Protocol):
    def cikar(self, ham_metin: str) -> tuple[YeniIsIliskisi, CikarimMeta]: ...
```

Sağlayıcı değiştirmek tek dosya. Şema, doğrulama kapısı, skor formülü ve CAR
hesabı sağlayıcıdan bağımsız.

**Tahmini maliyet** (613 bildirim — Adım 4'te ölçüldü, prompt caching + Batch API %50 dahil):

```
Backfill (tek seferlik)  ≈ 0.30 USD
Canlı işletme            ≈ 0.10 USD / ay
```

Ücretsiz katman kullanılırsa 0 USD; limit Google hesabına özel ve AI Studio
panelinden okunur, backfill gün sayısı ona göre planlanır.

> **Harcama kuralı:** Hüseyin'in o an verilmiş açık izni olmadan hiçbir ücretli
> API çağrısı yapılmaz. İşin sırası buna göre dizildi (§9): ücret gerektiren
> adım en sona konuldu.

## 8. Deterministik hesaplar

LLM'in dokunmadığı kısım. Hepsi test edilebilir saf fonksiyon.

**TL çevrimi.** TCMB'nin **bildirim tarihli** resmî kuru kullanılır, bugünkü kur
değil: `tcmb.gov.tr/kurlar/YYYYMM/DDMMYYYY.xml` — ücretsiz, resmî, arşivli.
Bildirim tatil/hafta sonu günündeyse önceki iş günü kuru. Backfill'de bu şart:
2025'te imzalanmış bir sözleşmeyi 2026 kuruyla çevirmek rakamı şişirir.

**Net tutar — hangi kalemler sayılır (revizyon 2026-09-18).** §6 artık
etiketli `tutarlar` listesi veriyor. Skora giren büyüklük **yalnızca yeni
olan iş**:

```
net_tutar_tl = Σ  tl_cevir(kalem)   for kalem in tutarlar
               if kalem.tip in {"ilave_siparis", "fiyat_farki", "tek_seferlik"}
```

`toplam_sozlesme` kalemleri **skora girmez**; sayfada ayrı bir bağlam kartı
olarak gösterilir ("projenin revize toplam bedeli"). Karıştırılırsa ORGE
örneğinde ciro oranı ~12 kat şişerdi.

Çok para birimli bildirimde her kalem **kendi** para biriminden, bildirim
tarihli TCMB kuruyla TL'ye çevrilip toplanır. Tek bir "para_birimi" alanı
yok; toplam her zaman TL cinsinden tek sayıdır.

**Ciro oranı.** `net_tutar_tl / sirket.son_yillik_hasilat_tl`.
`son_yillik_hasilat_tl` boşsa oran gösterilmez — tahmin edilmez.
`tutarlar` boşsa (tutar açıklanmamış) oran hesaplanmaz, bildirim yine
yayınlanabilir — skorun ciro bileşeni düşer, diğer bileşenler çalışır.

**Güncelleme bildirimleri.** `guncelleme_mi = true` olan bildirimde ürün
"yeni sözleşme" demez; başlık ve kart "mevcut işin güncellemesi" olarak
kurulur. Ciro oranı yine ilave tutardan hesaplanır — doğru payda budur.

**Etki skoru — kural tabanlı, LLM kanaati değil.** 0–5 arası:

```
skor = 2.5
     + w1 * f(ciro_orani)          # oran büyüdükçe artar, üstten satüre
     + w2 * g(karsi_taraf_tipi)    # kamu / yurtdisi > ozel_yurtici > iliskili_taraf
     + w3 * h(sure)               # tek seferlik vs yıllara yayılı
```

**Başlangıç ağırlıkları (karar 2026-09-18): `w1 = 1.5`, `w2 = 0.7`,
`w3 = 0.3`.** Ciro oranı baskın sürücü; karşı taraf tipi ikincil; süre ince
ayar. Altın küme (Adım 6) etiketlendikten sonra bu değerler gerçek dağılıma
göre yeniden kalibre edilir — o yüzden config'te, kodda değil.

Ağırlıklar konfigürasyonda, kodda gömülü değil. Aynı girdi → aynı skor.
Sayfada skorun bileşen kırılımı gösterilir ("neden 4.1"). LLM'e sorulsa
tekrarlanamaz ve açıklanamaz olurdu; ayrıca "şu formülle hesaplanmış büyüklük
göstergesi" demek "AI'ya göre çok olumlu" demekten savunulabilir.

**CAR — anormal getiri.** Yayınlanan tepki metriği ham getiri değil:

```
anormal_getiri(t) = hisse_getirisi(t) − xu100_getirisi(t)
CAR(3G)           = Σ anormal_getiri(t0+1 .. t0+3)
```

Hisse %2.8 yükselmiş ama XU100 da %2.8 yükselmişse tepki **yok**. Ham getiri
yayınlamak yanıltıcıdır.

İki incelik, ikisi de sessizce yanlış sonuç üretir:

- **t0 tanımı.** Bildirim seans kapandıktan sonra düştüyse `t0` bir sonraki
  işlem günüdür. Kaçırılırsa tüm tepki serisi bir gün kayar. Seans saatleri ve
  BIST tatil takvimi tabloda tutulur, koda gömülmez.
- **Düzeltilmiş kapanış.** Bedelsiz sermaye artırımı ve pay bölünmesi fiyat
  serisini kırar → `yfinance(auto_adjust=True)`.

**Fiyat kaynağı.** `yfinance`, `TICKER.IS` formatı. Yalnızca günlük kapanış
gerekiyor (tick/anlık veri değil), günde bir kez seans sonrası batch. Veri kendi
DB'mizde saklanır → bağımlılık tek seferlik çekime iner, kaynak sonra
değiştirilebilir. Resmî olmadığı ve ara ara kırıldığı için çekici ayrık tutulur
ve tutarlılık kontrolü (negatif fiyat, %50+ tek gün sıçraması, eksik gün)
uygulanır.

## 9. İş sırası

Ücret gerektiren adım en sona. Bundan önceki her şey 0 USD.

| # | Adım | Maliyet | Not |
|---|---|---|---|
| 0 | ~~KAP erişim yüzeyini doğrula~~ | 0 | **BİTTİ** — aşağıdaki bulgular |
| 1 | Postgres şeması + migration'lar | 0 | `tutarlar` listesi jsonb |
| 2 | KAP istemcisi (ısıtma + başlıklar + hız sınırı + geri çekilme) | 0 | Liste + detay API |
| 3 | Şablon ayrıştırıcısı: `oda-12000` XBRL alanları + TR/EN ayrımı | 0 | **LLM'siz, saf fonksiyon** |
| 4 | ~~Backfill: 12 ay liste + detay, kontrol noktalı~~ | 0 | **BİTTİ** — 613 bildirim, arşivde ve DB'de |
| 5 | ~~TCMB kur çekici + arşiv doldurma~~ | 0 | **BİTTİ** — 253 bülten, 5.610 kur satırı |
| 6 | yfinance fiyat batch + XU100 + CAR + testler | 0 | |
| 7 | Şirket hasılat tablosu (KAP finansal raporlardan) | 0 | |
| 8 | **Altın küme: 50 bildirim elle etiketle** | 0 | ≥10'u ilave/toplam ayrımı içersin |
| 9 | Çıkarıcı arayüzü + doğrulama kapısı + testler | 0 | Sahte çıkarıcıyla |
| 10 | Skor formülü (w1=1.5/w2=0.7/w3=0.3) + testler | 0 | |
| 11 | Pillow görsel kart + `/hisse/[ticker]` + `/kap/[id]` + X botu | 0 | Elle etiketli veriyle |
| 12 | **Pilot: 20 bildirim, Katman 1** | ~0.01 USD | **İZİN İSTENİR** |
| 13 | Altın küme üzerinde doğruluk ölçümü | ~0.05 USD | **İZİN İSTENİR** |
| 14 | Tam backfill çıkarımı (613 bildirim) | ~0.30 USD | **İZİN İSTENİR** |
| 15 | Canlı poller'ı aç | ~0.10 USD/ay | **İZİN İSTENİR** |

Adım 4 artık ücretsiz kısımda ve erken: ham veriyi bir kez çekip diske
almak, sonraki her adımın ağa bağımlılığını bitiriyor. Adım 3 sayesinde
karşı taraf/tarih/bayraklar LLM'e hiç uğramadan doluyor; LLM ilk kez
Adım 12'de devreye giriyor.

Adım 9'a kadar ürünün tamamı elle etiketlenmiş 50 bildirimle uçtan uca
çalışıyor olacak. Yani sayfa, kart ve tweet görülebilir durumda olacak; LLM
sadece ölçeklendirme aracı.

**Adım 0 — KAP erişim yüzeyi. TAMAMLANDI (2026-09-18).**

Spec'in "KAP bir Angular SPA, JSON ucu yok" varsayımı **yanlış çıktı** iki
ayrı biçimde: site Next.js'e taşınmış **ve** kimliksiz bir JSON API'si var.

### Seçilen erişim yolu — JSON API

Ampirik olarak doğrulandı (2026-09-18, gerçek yanıtlarla):

**1. Liste:** `POST https://www.kap.org.tr/tr/api/disclosure/members/byCriteria`

```json
{"fromDate":"2026-09-17","toDate":"2026-09-18","mkkMemberOidList":[],"subjectList":[]}
```

Sarmalayıcısız JSON dizisi, **2.000 eleman üst sınırı**. Alanlar:
`disclosureIndex` (detay anahtarı) · `publishDate` (`DD.MM.YYYY HH:MM:SS`) ·
`subject` (şablon adı) · `stockCodes` · `disclosureClass` · `summary` ·
`attachmentCount` · `modifyStatus` (düzeltmelerde dolu).

**2. Detay:** `GET /tr/api/notification/attachment-detail/{disclosureIndex}`

Tek elemanlı dizi: `disclosure.disclosureBasic` (künye) + `disclosureBody[0]`
(şablonun HTML gövdesi) + `attachments[]`. `disclosureBasic.disclosureId`
kararlı hex UUID — **upsert anahtarı bu olmalı**, `disclosureIndex` değil.
`isChanged` ve `relatedDisclosureOid` düzeltme zincirini verir.

**Zorunlu istek kuralları** (üçü de eksikse WAF bağlantıyı düşürür):

1. **Oturum ısıtması:** API'den önce bir kez `GET /tr/bildirim-sorgu`
   (çerez alınır — 4 çerez döndü)
2. `Referer` başlığı: liste için `/tr/bildirim-sorgu`, detay için
   `/tr/Bildirim/{index}`
3. Dürüst `User-Agent` (proje adı + iletişim)

Hız: **~2 istek/sn**, 2 günlük pencere <2 sn'de dönüyor.

### Neden bu, sıralı id taramasından iyi

İlk denemede `/tr/Bildirim/{id}` HTML'i ve ardışık id taraması seçilmişti.
O yol **terk edildi**: 201 id'lik ardışık tarama ~79 istekten sonra WAF'a
takıldı, sonraki 41 istek timeout aldı, tek istek 755 ms'de reddedildi.
Blok kalıcı değildi — ısıtma + başlıklarla aynı IP'den API hemen çalıştı.
Yani **engelin sebebi hız değil, eksik başlıklardı**. Yine de liste API'si
her bakımdan üstün: tarih penceresiyle sorgulanıyor, 404 boşluklarını
yoklamak gerekmiyor, backfill 12 ay için ~52 haftalık istek + bildirim
başına 1 detay isteğine iniyor.

### Doğrulanan hacim

17–18 Eylül 2026 penceresi: **949 bildirim / 2 gün**. Şablon dağılımının
tepesi Pay Bazında Devre Kesici (428), ÖDA Genel (104), Pay Alım Satım (63),
**Payların Geri Alınması (50)**. Hedefimiz **"Yeni İş İlişkisi" 2 günde 6
adet ≈ 3/gün ≈ 90/ay** — spec'in ~100/ay tahmini tutuyor, backfill ~1.100.

Not: B sürümü için ayrılan Pay Geri Alım şablonu günde ~25 adet, yani
MVP'nin 8 katı hacim. Sıraya alınırken bu bilinmeli.

### En önemli bulgu — şablon yapılandırılmış, serbest metin değil

Gövde HTML'i `tbl_oda-12000_New-Business-Relation` sınıfını taşıyor;
**router Türkçe `subject` string'ine değil `oda-12000` koduna bağlanmalı.**

Şablonun 15 XBRL alanı var ve §6 şemasının çoğu **LLM'siz, deterministik
olarak** doluyor:

| `oda_*` alanı | Şema karşılığı |
|---|---|
| `NatureOfTheOtherPartyWithWhichNewBusinessRelationWillStart` | `karsi_taraf_tipi` — "Müşteri (Customer)" gibi sabit küme |
| `NameSurnameOrCompanyTitleOfCustomerOrSupplier` | `karsi_taraf` |
| `ExpectedStartingDateOfNewBusinessRelation` | `baslangic` |
| `IfExistSignificantProvisionsOfTheContractTextBlock` | sözleşme koşulları |
| `ImpactOfNewBusinessRelationOnCompanyActivities` | şirketin kendi etki beyanı |
| `UpdateAnnouncementFlag` / `CorrectionAnnouncementFlag` / `DateOfThePreviousNotificationAboutTheSameSubject` | düzeltme zinciri |
| `ExplanationTextBlock` | **serbest metin — tutarın bulunduğu tek yer** |

Sonuç: **LLM'in işi bire indi — tutarı serbest metinden çıkarmak.** Karşı
taraf, tipi ve tarih için halüsinasyon riski tamamen ortadan kalkıyor,
çünkü o alanlar KAP'ın kendi yapılandırılmış verisi. §7'nin katmanlı
yönlendirmesi ve §6'nın alıntı kapısı yalnızca `tutar` için gerekli.

### Çözülmemiş — `tutar` şeması yetersiz

`1665567` (ORGE) gerçek örneği, §6'daki tek `tutar` + tek `para_birimi`
alanının **bu şablonu temsil edemediğini** gösteriyor. Serbest metinde beş
ayrı rakam var:

- 863.000 EUR — ilave sipariş (asıl yeni tutar)
- 44.645.758 TL — fiyat farkı
- 9.979.903 EUR + 133.751.712 TL — **eski** sözleşme bedeli
- 10.842.903 EUR + 178.397.470 TL — **revize** toplam sözleşme bedeli

İki ayrı sorun: (a) tek bildirimde **iki para birimi birden**, (b) artış
tutarı ile kümülatif sözleşme bedeli farklı şeyler ve karıştırılırsa ciro
oranı 12 kat şişiyor. "En büyük sayıyı al" sezgisi burada yanlış cevap
veriyor. Şema kararı gerekiyor — §6 revizyonu, Adım 6'dan önce.

İkinci incelik: `ExplanationTextBlock` **Türkçe ve İngilizce metni aynı
blokta** taşıyor. Ayrıştırıcı önce dili bölmeli, yoksa her rakam LLM'e iki
kez görünür ve alıntı kapısı yanlış eşleşir.

Üçüncüsü: ORGE örneğinde `UpdateAnnouncementFlag = Evet`, önceki tarihler
`10.05.2023, 14.06.2023, 03.01.2024, 07.02.2025`. Yani "Yeni İş İlişkisi"
bildirimlerinin önemli bir kısmı **yeni sözleşme değil, mevcut sözleşmenin
güncellemesi**. Ürün vaadi ve skor formülü bunu ayırmak zorunda.

**Adım 4 — 12 aylık backfill. TAMAMLANDI (2026-09-19).**

2025-09-22 → 2026-09-18 arası **613 "Yeni İş İlişkisi"** bildirimi, 111
şirket. Arşiv `data/ham/` altında, tamamı `bildirim` tablosunda.

Üç varsayım gerçek veriyle düzeldi:

1. **Hacim tahmini ~%45 yüksekti.** ~1.100 bekleniyordu, 613 çıktı
   (~1,7/gün). Tahmin iki günlük yoğun bir örnekten çıkarılmıştı. §7'nin
   backfill maliyeti aynı oranda düşüyor.
2. **Haftalık pencere çalışmaz.** KAP listeyi 2.000 kayıtta kesiyor,
   günde ~475 bildirim düşüyor; haftalık pencere ~3.300 eder ve fazlası
   **sessizce** kaybolurdu. Koşucu 3 günlük pencere kullanıyor, sınıra
   dayanan pencereyi ikiye bölüp yeniden soruyor, bölünemiyorsa özette
   bildiriyor.
3. **`karsi_taraf` bildirimlerin %36,5'inde boş** (224/613) — KAP karşı
   tarafı gizlemeye izin veriyor. §8'deki skorun `w2` bileşeni bu
   kayıtlarda "bilinmiyor"a düşer; Adım 10 kalibrasyonu bunu hesaba
   katmalı, çünkü etkilenen küme azınlık değil.

Ön eleme doğrulandı: liste kaydındaki `subject == "Yeni İş İlişkisi"`
olan 613 bildirimin **613'ü de** `oda-12000` çıktı.

WAF riski (§13, risk 2) ampirik olarak gerçekleşti: ilk koşu 12 ayın
%85'inde düştü, beş yeniden deneme de aynı çerezle gitti. Çare Adım 0
bulgusundan: başarısız denemeden sonra oturum soğuk işaretleniyor,
sonraki deneme çerezleri temizleyip yeniden ısıtıyor. Kontrol noktası
diskte olduğu için ilk koşunun 502 bildirimi korunmuştu; ikinci koşu
kalan 111'ini 2 dk 49 sn'de tamamladı.

**Adım 5 — TCMB kur arşivi. TAMAMLANDI (2026-09-19).**

2025-09-12 → 2026-09-18 arası **253 bülten**, 23 para birimi, **5.610 kur
satırı**. 115 gün yayın yok (hafta sonu + resmî tatil) ve bu da arşivde
işaretli — aksi hâlde her koşu o günleri TCMB'ye yeniden sorardı.

Üç karar yazıya geçti:

1. **Döviz alış (`ForexBuying`)** kullanılıyor. Şirketler hasılatlarını bu
   kurla çeviriyor; ciro oranının payı ile paydası aynı mantıkla
   hesaplanmış oluyor. Alış-satış farkı ~%0.2, ama hangisi olduğunun
   sabit olması önemli.
2. **`Unit` indirgemesi zorunlu.** JPY kuru 100 birim üzerinden
   yayınlanıyor; indirgenmezse yen cinsli bir sözleşme 100 kat büyük
   görünür. Alış kuru boş gelen para birimi atlanıyor — boşu sıfır saymak
   çarpımı sessizce sıfırlar.
3. **404 hata değil, veri yokluğu.** Tatilde TCMB dosya yayınlamıyor;
   yeniden denemek anlamsız. 5xx ise geçici sayılıp yeniden deneniyor.

"Önceki iş günü" kuralı tek yerde yaşıyor: `depo.kur_coz`. Geri yürüme
**10 günle sınırlı** — üç ay önceki kurla çevirmek sessizce yanlış bir
rakam üretirdi; bulunamayan kur §6'nın B2 kapısında elle incelemeye düşer.

Kapsama doğrulandı: bildirimlerin düştüğü **223 günün 223'ünde** hem USD
hem EUR çözülüyor. 221'i aynı gün, 2'si bir gün geriden; en uzun geri
yürüme **1 gün**, yani sınır bol bol yetiyor.

## 10. Doğruluk ölçümü

50 bildirimlik altın küme, elle etiketli, `altin_kume` tablosunda. Ölçülen:

Revizyon 2026-09-18: `karsi_taraf` ve `baslangic` artık KAP'ın
yapılandırılmış alanlarından geldiği için **doğruluk ölçümünün konusu
değil** — onlar ayrıştırıcı testiyle (birim test) doğrulanır, model
ölçümüyle değil. Ölçüm yalnızca LLM'in yaptığı işi hedefler:

| Metrik | Hedef |
|---|---|
| `tutarlar` kalem sayısı tam eşleşme | ≥ %95 |
| Kalem `deger` tam eşleşme | ≥ %98 |
| Kalem `para_birimi` doğruluk | ≥ %99 |
| Kalem `tip` doğruluk (ilave vs toplam ayrımı) | ≥ %95 |
| `net_tutar_tl` tam eşleşme (uçtan uca) | ≥ %95 |
| `tutar_gizli` precision / recall | ≥ %95 / ≥ %95 |
| Doğrulama kapısı yanlış-kabul oranı | %0 |

`tip` doğruluğu yeni ve en riskli metrik: ilave sipariş ile revize toplam
sözleşme bedelini karıştırmak sessizce yanlış bir ciro oranı üretir ve
kapıdan geçer (her iki sayı da metinde gerçekten var, alıntı eşleşir).
Altın kümede bu ayrımı içeren en az 10 örnek bulunmalı.

Son satır en önemlisi: kapının yanlış bir çıkarımı yayına geçirmesi kabul
edilemez. Yanlış-red (doğru çıkarımı reddetme) tolere edilir — maliyeti bir
bildirimin yayınlanmaması, hatalı sayı yayınlamak değil.

Bu ölçüm CI'da koşar. Prompt veya şema değiştiğinde eşiklerin altına düşerse
build kırılır. Katman 1 → Katman 2 kararının verisi de bu ölçüm.

## 11. Yayın

**Web (Vercel / Next.js).**

| Rota | İçerik | SEO değeri |
|---|---|---|
| `/kap/[kap_id]` | Tek bildirim: göstergeler, hap özet, skor kırılımı, karne, CAR, kaynak | Günlük — tweet'in indiği yer |
| `/hisse/[ticker]` | O şirketin tüm iş ilişkileri + kümülatif karne + CAR dağılımı | **Kalıcı** — asıl SEO varlığı |

`/hisse/[ticker]` daha değerli: "ASELS yeni iş ilişkisi" araması kalıcı bir
niyet, tek bildirim sayfası bir günlük. Programmatic SEO'nun ağırlığı burada.

**Karar (2026-09-18): Adım 9'da önce `/hisse/[ticker]` yazılır**, `/kap/[kap_id]`
ondan sonra gelir.

Slug notu: `/kap/asels-2026-09` çakışır (aynı ay iki bildirim). Kanonik rota
`kap_id` üzerinden; okunur slug varsa `/kap/asels-2026-09-17-{kap_id}` ve
kanonik olana `rel=canonical`.

Her sayfanın künyesi: kaynak KAP linki, bildirim yayın zamanı, çekim zamanı,
model + prompt versiyonu, **"Yatırım tavsiyesi değildir."**

**X botu.** 1200×675 koyu tema görsel kart, Pillow ile önceden hazırlanmış
statik şablon üstüne 4-5 satır basılır (Puppeteer/headless tarayıcı yok —
gereksiz 2-3 saniye). Metin görseldeki bilgiyi kopyalanabilir biçimde tekrarlar,
sonuna arındırılmış geçmiş tepki dökümü linki. Künye tweet'te de var.

Fontlar repoda gömülü (sistem fontuna güvenilmez); Türkçe karakter seti
(ğüşıöçĞÜŞİÖÇ) render testiyle doğrulanır.

## 12. Gecikme bütçesi

| Adım | Süre | Not |
|---|---|---|
| Tespit | ~2.5 sn | Seans içi 5 sn polling → ortalama aralık/2 |
| Çıkarım (Katman 1) | 2-4 sn | Flash-Lite, streaming |
| Deterministik hesap | ~10 ms | |
| Görsel kart | ~80 ms | Pillow, statik şablon |
| X API | 1-2 sn | |
| **Toplam** | **~7-9 sn** | |

Polling politikası: seans içi (10:00–18:10 TR) 5 sn, seans dışı 60 sn, KAP
`ETag`/`If-Modified-Since` destekliyorsa koşullu istek. Saniyede bir sormak
(günde 86.400 istek) hem bloklanma riski hem nezaketsizlik — yapılmıyor.
Katman 2'ye düşen bildirimde toplam ~12-15 sn olur; kabul ediliyor.

## 13. Riskler

1. **KAP yapı değişikliği.** Erişim yüzeyi resmî API değil. Karşı hamle:
   çekici tek dosyada ayrık, ham HTML/metin diskte ve DB'de saklanır, site
   canlı kaynağa bağlı değil. Kırılınca site ayakta kalır, sadece yeni bildirim
   akmaz. Sağlık kontrolü: 4 saat boyunca yeni bildirim yoksa (seans içi) alarm.
2. **KAP hız sınırlaması / IP bloku.** Adım 0'da ampirik olarak tetiklendi:
   ardışık id taraması ~79 istekten sonra bağlantı seviyesinde reddedilmeye
   başladı. Backfill'in tek gerçek darboğazı bu — LLM maliyeti değil, çekim
   hızı. Karşı hamle: düşük sabit hız, kontrol noktalı ve kaldığı yerden
   devam eden backfill, üstel geri çekilme, dürüst `User-Agent`, ham HTML'in
   diskte saklanması (aynı sayfa iki kez istenmez). Blok kalıcı hale
   gelirse VPS/Railway üzerinden farklı bir çıkış IP'si gerekir; bu bir
   çözüm değil, sadece hızı düşürmenin alternatifi değil tamamlayıcısıdır.

3. **SPK / lisanssız yatırım tavsiyesi.** Skor ve tepki istatistiği yayınlamak
   risk taşıyor; Hüseyin bu riski bilerek kabul etti. Azaltıcılar: skor
   deterministik formül ve kırılımı gösteriliyor, tepki geçmiş istatistik olarak
   sunuluyor (tahmin değil), her çıktıda künye + KAP kaynak linki, al/sat
   ifadesi hiç kullanılmıyor.
4. **yfinance kırılganlığı / ToS.** Veri kendi DB'mizde saklandığı için
   bağımlılık tek seferlik; kaynak değiştirilebilir. B sürümünde ücretli bir
   sağlayıcıya (EODHD / Twelve Data) geçiş yolu açık bırakılıyor.
5. **Hasılat verisi eksikliği.** `son_yillik_hasilat_tl` olmayan şirkette ciro
   oranı ve skorun bir bileşeni hesaplanamaz. Bu durumda oran **gösterilmez**,
   tahmin edilmez; bildirim yine yayınlanır, sadece o kart eksik.
6. **Tespit gecikmesi rekabeti.** KAP'ın kendi uygulaması ve mevcut Telegram
   botları bildirimleri anlık aktarıyor. Bizim farkımız hız değil analiz;
   pazarlama mesajı buna göre kurulur, "en hızlı" iddiası edilmez.

## 14. Sonraki sürümler

- **Pay Geri Alım** — deterministik parser (şablon tablo, LLM'e gerek yok) +
  kümülatif takip: "bu şirket 90 günde halka açık payın %X'ini geri aldı,
  ortalama maliyeti Y TL, bugünkü fiyat Z". Kimse yayınlamıyor.
- **Telegram botu** — X'ten teknik olarak daha kolay, MVP dışı tutuldu.
- **Sektör kırılımı** sayfaları.
