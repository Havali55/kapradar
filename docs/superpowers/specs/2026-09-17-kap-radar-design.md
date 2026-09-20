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

**Etki skoru — kural tabanlı, LLM kanaati değil.** 0–5 arası.

> **REVİZYON 2026-09-20 — formül değişti.** Aşağıdaki toplamsal formül
> (`2.5 + w1·f(ciro) + w2·g(karşı taraf) + w3·h(süre)`) 2026-09-19 kanıt
> taramasından sonra bırakıldı. Yürürlükteki formül:
> `docs/arastirma/2026-09-19-skor-formulu-onerisi.md` (Hüseyin 2026-09-20'de
> onayladı), uygulaması `src/kap_radar/skor.py`. Özet:
>
> ```
> S = clamp(5 · f(r) · K, 0, 5)
> f(r) = clamp((log10(r) + 2) / 2, 0, 1)      # %1 taban, %100 tavan
> K    = 1,00 (açık+ilk) · 0,85 (açık+güncelleme)
>        0,70 (gizli+ilk) · 0,50 (gizli+güncelleme)
> ```
>
> Üç fark: **2,5 tabanı kalktı** (tutar ya da hasılat yoksa skor hiç
> gösterilmez, ~%15 bildirim skorsuz), **w3 (süre) düştü** (KAP süre
> vermiyor, kanıt yok), **devre kesici skora girmiyor** (bildirimin değil
> hissenin özelliği → ayrı tahta bayrağı). Skor bir **getiri tahmini
> değil**: tüm sinyaller 3 günlük CAR'ın yalnız %6,4'ünü açıklıyor.
> Geçmiş tepki ayrı ve betimleyici bir panelde (medyan + çeyreklik + n).

Eski formül (tarihsel kayıt):

```
skor = 2.5
     + w1 * f(ciro_orani)          # oran büyüdükçe artar, üstten satüre
     + w2 * g(karsi_taraf_tipi)    # kamu / yurtdisi > ozel_yurtici > iliskili_taraf
     + w3 * h(sure)               # tek seferlik vs yıllara yayılı
```

Değişmeyen karar: ağırlıklar konfigürasyonda (`skor.Agirliklar`), kodda
gömülü değil. Aynı girdi → aynı skor. Sayfada skorun bileşen kırılımı
gösterilir ("neden 4.1"). LLM'e sorulsa tekrarlanamaz ve açıklanamaz
olurdu; ayrıca "şu formülle hesaplanmış büyüklük göstergesi" demek
"AI'ya göre çok olumlu" demekten savunulabilir.

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
| 6 | ~~yfinance fiyat batch + XU100 + CAR + testler~~ | 0 | **BİTTİ** — 27.581 kapanış, 612 tepki |
| 7 | ~~Şirket hasılat tablosu (KAP finansal raporlardan)~~ | 0 | **BİTTİ** — `finansal_donem`, point-in-time TTM |
| 8 | ~~**Altın küme: 50 bildirim elle etiketle**~~ | 0 | **BİTTİ** — 12'si ilave/toplam ayrımı |
| 9 | ~~Çıkarıcı arayüzü + doğrulama kapısı + testler~~ | 0 | **BİTTİ** — sahte çıkarıcıyla, LLM yok |
| 10 | ~~Skor formülü + testler~~ | 0 | **BİTTİ** — onaylanan logaritmik formül |
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

**Adım 6 — fiyat serisi ve anormal getiri. TAMAMLANDI (2026-09-19).**

111 hisse + XU100, 259 işlem günü, **27.581 kapanış satırı**. 613
bildirimin **612'si** için tepki hesaplandı (biri serinin bittiği günden
sonra düştü); `car_3g` 601'inde dolu.

Ölçülen dağılım: ortalama **+%0,69**, medyan +%0,41, standart sapma
%6,86, aralık −%30,2 … +%30,2. Yani "Yeni İş İlişkisi" bildirimleri
ortalamada küçük ama pozitif bir anormal getiriyle karşılanıyor — ürünün
"bu açıklama ne ifade ediyor" vaadinin sayısal karşılığı bu.

**İşlem takvimi ayrı tabloda tutulmuyor, endeks serisinden geliyor.**
XU100'ün kapanışı olan gün seans var demektir. §8 "tatil takvimi tabloda
tutulur" diyordu; elle bakılan bir liste eskir, endeks serisi kendini
güncel tutar. Koda gömülü tek zaman bilgisi seans kapanışı (18:10).

**Pencere tanımı düzeltildi.** §8'in yazılı formülü `CAR(3G) =
Σ anormal_getiri(t0+1 .. t0+3)` idi, ama aynı bölüm t0'ı "bildirim seans
kapandıktan sonra düştüyse bir sonraki işlem günü" diye tanımlıyor. İkisi
birleşince **asıl tepki günü pencerenin dışında kalıyordu**. Varsayılan
pencere artık `t0` dahil üç işlem günü; `tepki.pencere_basi` sütunu hangi
tanımla hesaplandığını taşıyor ve `--pencere-basi 1` eski tanıma döner.

**`auto_adjust` BIST bedelsizlerini düzeltmiyor.** §8 bunun yeterli
olduğunu varsayıyordu; gerçek veride üç seri kırık çıktı: HRKET
87,9 → 6,15 (2026-09-09), MEGMT 47,3 → 4,90 (2026-09-09), CVKMD
37,82 → 14,42 (2026-08-03). Böyle bir gün fiyat olarak "var" olduğu için
eksik sayılmaz ama getirisi anlamsızdır; CAR bu tarihlere dokunan
pencereleri tümden reddediyor. Eksik kapanış da aynı şekilde: pencere
içinde tek gün eksikse sonuç NULL kalır — yanlış sayı yayınlamaktansa
hiç yayınlamamak.

İkincil bulgu: yfinance kapanışları float32 taşıyor (22,2 → 
22.200000762939453). Kapanışlar dört ondalığa yuvarlanarak saklanıyor;
fazlası olmayan bir hassasiyeti iddia etmek olurdu.

**Adım 7 — şirket hasılat tablosu. TAMAMLANDI (2026-09-20).**

Skorun paydası. İki şart baştan konmuştu: **TTM** (son dört çeyrek, tek
çeyrek değil) ve **point-in-time** (bildirim anında piyasada hangi
bilanço açıksa o).

**Sonuç: 613 bildirimin 597'sinde (%97,4) o bildirimin yayınlandığı
andaki TTM hasılat çözülüyor** (492'si YTD köprüsüyle, 105'i doğrudan
yıllık rapordan). Çözülemeyen 16 bildirim 8 şirkete ait ve hepsi yeni
halka açılmış: geçmiş rapor yok, uydurulacak bir payda da yok.
935 rapor arşivde (19 MB), 111 şirket, 2024-09 → 2026-09.

Gelir tablosu KAP'ın finansal rapor detayında `disclosureBody` içinde
`3100xx` rol ailesiyle işaretli parçada. Parça sırası şirkete göre
değiştiği için indekse değil role bakılıyor. Hasılat etiketi
`ifrs-full_Revenue`, bankalar ve finans kuruluşlarında
`kap-fr_RevenueFromFinanceSectorOperations`.

**Rol tek bir sabit değil — bu ilk koşuda pahalıya patladı.** IFRS gelir
tablosunu iki türlü sunmaya izin veriyor ve KAP taksonomiyi şirket
tipine göre de ayırıyor:

| rol | kim kullanıyor |
|---|---|
| `tbl_general_role_310000` | fonksiyon esaslı (ORGE) |
| `tbl_general_role_310003` | çeşit esaslı (NETAS, ARDYZ, FONET, SAFKR) |
| `tbl_holding_role_310030` | holding taksonomisi (TCELL) |

Yalnız `310000` arandığında 935 raporun **577'si** "gelir tablosu yok"
diye sessizce atlandı. Kalıp `tbl_[a-z]+_role_3100\d*` yapıldıktan
sonra 935'in 935'i indi. Bu hatanın görünür olmasının tek sebebi
çekicinin gelir tablosu bulunamayan raporu **özete yazması**; sessizce
atlasaydı o şirketlerin hepsi kalıcı olarak paydasız kalırdı.

**Sunum birimi para birimi değil.** `Sunum Para Birimi` alanı "TL"
olabildiği gibi "1.000 TL" ya da "1.000.000 TL" de olabiliyor: 935
raporun 78'i bin TL, 1'i milyon TL cinsinden. Çarpan uygulanmazsa TOASO,
DOAS ve AKENR'in hasılatı bin kat küçük okunur ve her ciro oranı bin kat
büyür — 500 milyonluk bir sipariş Tofaş'ın cirosunun %156'sı gibi
görünürdü (gerçekte %0,16). Çarpan **ayrıştırma anında** uygulanıyor:
tabloda saklanan hasılat her zaman mutlak tutar, `birim_carpani` sütunu
yalnız izlenebilirlik için. Okuma anına bırakılsa bir yerde unutulurdu.

**Beyan da yanlış olabiliyor.** İki şirket sunum birimini hatalı yazmış:
ONCSM 2025 yıllığında "1.000.000 TL" demiş ama rakam sade TL serisinin
doğal devamı; ALTNY 6A2026'da "1.000 TL" demiş, sonra **aynı rakamla
düzeltilmiş raporu yeniden yayınlamış** (1650534 → 1652196). Bu yüzden
beyana körü körüne uyulmuyor: yüklemeden önce her şirketin kendi serisi
içinde yıllıklandırılmış hasılat medyanına bakılıyor, yüz katı aşan
sapma ölçek hatasıdır ve o rapor yüklenmeyip bildiriliyor. ALTNY
örneğinde kontrol, şirketin kendi düzeltmesiyle aynı sonuca vardı.

**Sütun seçimi tek gerçek tuzak.** Ara dönem raporunda dört sütun var:
cari YTD, önceki yıl YTD, cari 3 aylık, önceki yıl 3 aylık. Türkçe
etiketlere ("Cari Dönem 3 Aylık") değil sütun başlığındaki tarih
aralığına bakılıyor — en geç biten ve en uzun olan cari YTD'dir. 3
aylık sütunu YTD sanmak paydayı yarıya indirir, yani her ciro oranını
iki katına çıkarır.

TTM köprüsü: `TTM = FY(önceki hesap dönemi) + YTD(cari) − YTD(geçen yıl
aynı dönem)`. Ara dönem raporu köprünün iki bileşenini birden taşıyor,
çünkü geçen yılın aynı dönemi karşılaştırma sütununda duruyor. Köprünün
yıllık bacağı **dönem başıyla** eşleştiriliyor (`FY.donem_sonu ==
R.donem_basi − 1 gün`), takvim yılıyla değil: özel hesap dönemi
kullanan şirkette takvim yılı yanlış rapora bağlar.

Point-in-time seçim: `an`dan sonra yayınlanmış rapor hiç görünmez; kalan
raporlar arasından **en güncel DÖNEM** kazanır, en son yayın değil (eski
bir dönemin revizyonu yeni yayınlanmış olabilir); aynı dönemde son yayın
kazanır. Köprünün yıllık bacağı da o anda açıklanmış olmalı — eksikse
TTM üretilmez ve ciro oranı gösterilmez. Yarım veriyle TTM uydurmak
sessizce yanlış bir skor üretir.

Yeni tablo `finansal_donem` (bir satır = bir rapor): `kap_index`,
`ticker`, `yayin_zamani`, `donem_basi`, `donem_sonu`, `ay_sayisi`,
`hasilat`, `onceki_yil_hasilat`, `para_birimi`, `konsolide`.
`sirket.son_yillik_hasilat_tl` duruyor ama artık yalnızca sitenin
göstereceği **önbellek**; skorun paydası oradan okumuyor.

**Para birimi saklanıyor, çevrilmiyor.** USD raporlayan şirkette hasılat
TL sanılırsa ~40 kat hata olur. TL çevrimi skor anında, bildirim tarihli
TCMB kuruyla yapılıyor — payla paydanın aynı mantıkta olması için.

Çekim: liste arşivi 2024-09-01'e kadar geriye uzatıldı (en eski bildirim
2025-09-22; onun paydası için FY2024'ün Şubat–Nisan 2025'teki yayınını
görmek gerekiyor). Ön eleme `subject == "Finansal Rapor"` + hedef
ticker: `disclosureClass == "FR"` yetmiyor, aynı sınıfta sorumluluk
beyanı ve faaliyet raporu da var ve onlarda gelir tablosu yok.

**Arşiv kırpılarak saklanıyor.** Tam rapor beş parça ve ~2 MB; 900 rapor
~2 GB eder. Dördü (bilanço, nakit akış, özkaynak, dipnotlar) bu projede
hiç açılmıyor. Saklanan yalnız künye + gelir tablosu, o da gzip'li:
rapor başına ~10 KB. Bilanço gerekirse KAP'tan yeniden çekilir.

**Koşu sırasında bulunan kusur:** liste penceresi hatası tüm çekimi
kesiyordu (detay hataları baştan beri tolere ediliyordu). 250 pencerelik
ilk koşu WAF'a takılıp düştü ve o ana kadar inen 151 rapor özetsiz
kaldı. Artık düşen pencere özete yazılıp geçiliyor, ikinci koşu onları
yeniden deniyor.

**Adım 8 — altın küme. TAMAMLANDI (2026-09-20).**

50 bildirim elle etiketlendi. Rastgele 50 yanlış olurdu: doğruluk
ölçümünün işe yaraması için örnek **zor olanı** temsil etmeli. Tabakalar
gerçek hatalardan çıkarıldı ve kotalar buna göre kondu: `ilave_toplam`
12, `mukerrer_cevrim` 5, `cok_para` 8, `tutarsiz` 6, `guncelleme` 6,
`gizli_karsi_taraf` 6, `sade` 7.

Etiketlerin tamamı §6'nın metin kapısından geçirilerek doğrulandı —
model çıktısı gibi. 48'i kapıdan geçiyor, 2'si **bilinçli** A5 reddi,
0 hatalı alıntı. Elle yazılmış bir alıntının ham metinde birebir
geçmediği fark edilmezse ölçüm modeli değil etiketi cezalandırırdı.

Etiketlerken çıkan ve prompt'a yazılan kurallar (her biri gerçek bir
bildirimden):
- Şirketin parantez içinde verdiği kendi TL çevrimi **ayrı kalem değil**
  (ARDYZ 1664397: "1.040.400 USD (50.613.963 TL)"). İkisi de sayılırsa
  net tutar tam iki katına çıkar ve A5 bunu görmez — para birimleri
  farklı. Bunun için B3 kontrolü eklendi.
- Opsiyon tutarları etiketlenmez (ONRYT 1521650, YEOTK 1575338):
  kesinleşmiş iş değil.
- Şirketin **ödediği** bedel gelir değil (DGATE 1491549: 8.000.000 USD
  sözleşme devir ücreti). Aynı bildirimdeki "yıllık 300 milyon USD ek iş
  hacmi hedeflenmektedir" de bir beklenti. Doğru çıkarım: boş liste.
- Alt siparişler ve toplamı birlikte veriliyorsa yalnız toplam (EMKEL
  1493982: 433.015 + 190.725 = 623.740 EUR).
- Güncellemede yalnız nihai tutar (OZATD 1492195: 2.750.000 → 3.575.000).
- **Şirketin kendi TL çevrimine güvenilmez:** CWENE 1502587'deki TL
  rakamı bir önceki bildirimden kopyalanmış, yanlıştı; şirket 1502725
  ile düzeltti. TL çevrimi kendi TCMB kurumuzla yapılmalı.

Bilinen yanlış-red: A5, aynı para biriminde iki **ayrı gerçek** sözleşme
olan bildirimleri de reddediyor (ASELS 1572732: 111.850.000 + 54.600.000
USD). Katı kapı kararı gereği elle kuyruğa düşüyor; küme bunu belgelemek
için içeriyor.

**Adım 9 — çıkarıcı arayüzü ve doğrulama kapısı. TAMAMLANDI (2026-09-20).**

LLM yok; sahte çıkarıcıyla uçtan uca test edildi. `Cikarici` protokolü,
pydantic şeması, A1–A6 metin kapısı, B1–B3 tutarlılık kapısı ve katmanlı
yönlendirme (`katmanli_cikar`) hazır. Prompt `prompt_kur` içinde,
sürümü `cikarim` tablosuna yazılıyor.

Gerçek metinlerle çalışırken kapının üç yerinde eksik bulundu:
- **Çarpan sözcükleri.** "25,02 milyon ABD Doları" (CVKMD 1494067)
  A2'den dönüyordu. `bin|milyon|milyar|trilyon` artık çözülüyor.
- **Çekim ekleri.** Şirketler "USD" yerine sık sık "Amerikan Doları"
  yazıyor; `\bdolar\b` "doları"yı tutmuyordu. Sözlük `\w*` kuyruğu aldı.
- **Sayıya bitişik kod.** "2.974.771,80USD" (CWENE 1502725) A3'ten
  dönüyordu. Para kodlarının sınırı artık kelime karakterine değil
  **harfe** göre: hem bunu geçiriyor hem "atlanmıştır" içindeki "tl"
  dizisini eliyor.

Üçü de yakalanmasaydı kapı gerçek çıkarımları halüsinasyon sanıp
reddedecek ve yanlış-red oranını sessizce şişirecekti.

**Adım 10 — skor. TAMAMLANDI (2026-09-20).**

Onaylanan formül `src/kap_radar/skor.py` içinde; ayrıntı §8'in revizyon
kutusunda ve `docs/arastirma/2026-09-19-skor-formulu-onerisi.md`'de.
Yanında iki parça daha var: betimleyici **tepki paneli** (medyan,
%25–%75, n, pozitif oranı — ortalama bilerek yok) ve **tahta bayrağı**
(temiz / hareketli / tedbirli).

**Uçtan uca doğrulama (`scripts/skor_dogrula.py`).** Altın kümenin 50
bildirimi gerçek veriyle baştan sona koşturuldu — LLM'e hiç uğramadan,
çünkü tutarlar elle etiketli. Zincirin tamamı bağlandı: TCMB kuru
(Adım 5) → point-in-time TTM (Adım 7) → kapı (Adım 9) → skor (Adım 10).

```
skorlu               40
tutar yok -> skorsuz 10        (altın kümedeki boş listelerin tamamı)
elle kuyruğa          0
skor: en düşük 0,00 · medyan 1,41 · en yüksek 4,07
```

Tek tek bakıldığında sayılar da tutuyor: ASELS'in 1,12 milyar avroluk
sözleşmesi cironun %42'si (skor 4,06), LINK'in 2 milyon TL'lik işi
%0,12 ile taban altında (skor 0,00), ORGE'nin 940 bin dolarlık ilave
siparişi %1,21 (skor 0,18). CWENE'nin iki bildirimi aynı 2.974.771,80
USD'yi farklı günlerin kuruyla 123,9 ve 124,1 milyon TL veriyor —
şirketin yanlış yazdığı 400 milyonluk rakam hiçbir yerde görünmüyor.

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
