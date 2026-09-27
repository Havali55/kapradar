# KAP Radar

> **In English:** A data pipeline that turns Borsa Istanbul "New Business
> Relation" disclosures (KAP) into a measurable size: contract value divided
> by the company's point-in-time trailing-twelve-month revenue, parsed from
> XBRL filings. An LLM only extracts amounts from free text; every number it
> returns must quote the source sentence verbatim or the disclosure is
> withheld (deterministic gate A1–A7, B1–B6). FX conversion, ratios and the
> score are plain code. Runs daily on GitHub Actions for a few cents a month.
> Live site: [kap.calibresolve.com](https://kap.calibresolve.com) · Methodology
> and validation (Turkish): [/metodoloji](https://kap.calibresolve.com/metodoloji).
> Identifiers are Turkish; see the glossary at the end.

**KAP bildirimi düşer, ne anlama geldiği ölçülebilir hâle gelir.**

KAP bildirimleri ham metindir: *"45.200.000 USD tutarında sözleşme imzalanmıştır."*
Bu sayının büyük mü küçük mü olduğunu, şirketin cirosuna göre ne ifade ettiğini,
geçmişte benzer açıklamalardan sonra fiyatın ne yaptığını söyleyen bir yer yok.
Bu depo o dönüşümü yapan veri hattı.

Kapsam (A sürümü): yalnız **"Yeni İş İlişkisi"** şablonu.

> **Yatırım tavsiyesi değildir.** Üretilen hiçbir sayı alım-satım önerisi değil;
> kamuya açık KAP bildirimlerinin deterministik bir özetidir. Her çıktı kaynak
> KAP bildirimine, çekim zamanına ve model/prompt sürümüne bağlıdır.

---

## Neden bu bir veritabanı işi

Tek bir bildirimi bir dil modeline yapıştırıp özet istemek mümkün. Üç şey
istenemez:

1. **Ciroya oran** — şirketin son 4 çeyrek hasılatını (TTM) bilmek ve tutarı
   bildirim tarihli TCMB kuruyla çevirip bölmek gerekir.
2. **Geçmiş karne** — "bu şirket son 12 ayda 4 benzer iş açıkladı" ancak
   bildirim arşiviyle üretilebilir.
3. **Anormal getiri** — endeksten arındırılmış tepki; fiyat serisi, endeks
   serisi ve doğru `t0` gerektirir.

Üçü de veri varlığı gerektiriyor. Hattın savunma hattı prompt değil, veritabanı.

## Hat

```
KAP listesi  ──► ham arşiv (disk)  ──► Postgres
                                        │
    TCMB kurları ──────────────────────►│
    Finansal raporlar (TTM) ───────────►│
    Fiyat + XU100 (CAR) ───────────────►│
                                        ▼
                           çıkarım (LLM, katmanlı)
                                        ▼
                     doğrulama kapısı  A1–A7 · B1–B6
                                        ▼
                          büyüklük skoru + tepki paneli
```

**LLM'in tek işi serbest metinden tutarları çıkarmak.** Karşı taraf, başlangıç
tarihi, güncelleme/düzeltme bayrakları KAP'ın yapılandırılmış XBRL alanlarından
deterministik geliyor. TL çevrimi, ciro oranı ve skor da koddan — modele hiç
aritmetik verilmiyor.

## Doğrulama kapısı

Kapıdan geçmeyen bildirim yayınlanmaz; kısmi yayın yok.

| Aşama | Kontrol |
|---|---|
| A1 | Alıntı ham metinde birebir geçiyor mu |
| A2 | Değer alıntının içinde geçiyor mu |
| A3 | Para birimi alıntıda geçiyor mu |
| A4 | `tutar_gizli` ile dolu tutar listesi çelişiyor mu |
| A5 | Aynı tip + aynı para biriminde mükerrer kalem |
| A6 | Modelin kendi güven beyanı |
| A7 | Özette metinde geçmeyen bir yıl var mı |
| B1 | Ciro oranı makul üst sınırın üstünde mi |
| B2 | Bildirim tarihli TCMB kuru bulunabildi mi |
| B3 | Aynı tutar iki para biriminde tekrarlanmış mı |
| B4 | KAP karşı taraf niteliği "tedarikçi" mi (şirket alıcı olabilir) |
| B5 | Tutarın cümlesinde muhammen bedel, yatırım tutarı, görüşme ya da ön ödeme var mı |
| B6 | Bir kalem, başka bir kalem ile metindeki bir sayının toplamı mı (artış ve yeni toplam birlikte) |

A reddi bir üst katman modele **yükseltilir**; B reddi model hatası değil veri
şüphesidir, doğrudan elle inceleme kuyruğuna düşer. A7 ve B4–B6, 26.09.2026
veri denetiminden doğdu: A1–A3 sayının metinde **geçtiğini** denetliyor,
**neyin sayısı olduğunu** denetlemiyordu (bkz.
`docs/arastirma/2026-09-26-veri-denetimi.md`).

B3 gerçek bir vakadan doğdu: `1.040.400 USD (50.613.963 TL)` — şirket kendi
çevirisini parantez içinde vermiş. İkisi de kalem sayılırsa net tutar tam iki
katına çıkar ve A5 bunu göremez, çünkü para birimleri farklı.

## Skor

```
S = clamp(5 · f(r) · K, 0, 5)      f(r) = clamp((log10(r) + 2,602) / 2,602, 0, 1)
```

`r` = net tutar / TTM hasılat. Logaritmik, çünkü materyallik çarpımsal:
%0,25 taban, %100 tavan (taban başta %1'di; hacim sınaması o eşiğin altındaki
bildirimlerin de ilgi gördüğünü gösterince indirildi). `K` güvenilirlik
çarpanı (karşı taraf açık/gizli × ilk/güncelleme), 1,00'dan 0,50'ye.

Sitede görünen **kademe S'den değil doğrudan r'den** okunuyor: %5 ve üstü
"önemli", %15 ve üstü "mega". K bir güvenilirlik ayarı; büyüklük etiketine
karışırsa gizli karşı taraflı dev bir iş "rutin" görünebiliyordu.

Skor bir **getiri tahmini değil, büyüklük ölçüsüdür.** Bunun sebebi ölçüldü:
601 bildirimlik örneklemde tüm sinyaller birlikte 3 günlük anormal getirinin
yalnızca %6,4'ünü açıklıyor. Tepki, tahmin olarak değil betimleyici bir panel
olarak (medyan, çeyreklikler, n) gösteriliyor.

Tutar yoksa skor **hiç gösterilmiyor** — sıfır ya da varsayılan bir taban değil.

## Point-in-time TTM

Payda iki şartı birden karşılamak zorunda: son 4 çeyrek **ve** bildirim anında
açıklanmış olmak. Tek bir ara dönem raporu TTM'in iki bileşenini birden veriyor:

```
TTM = FY(önceki yıl) + YTD(cari) − YTD(geçen yıl aynı dönem)
```

Gerçek veriden öğrenilen üç tuzak: gelir tablosunun XBRL rolü sabit değil,
"Sunum Para Birimi" `1.000 TL` olabiliyor, ve şirket bu beyanı yanlış da
yazabiliyor (yükleyici her şirketin kendi serisindeki medyana bakıp aykırı
raporu almıyor).

## Ölçülen durum

| | |
|---|---|
| Bildirim arşivi | 613 bildirim / 111 şirket (12 ay) |
| TCMB kur satırı | 5.610 |
| Fiyat serisi | 27.607 kapanış (111 hisse) + 259 günlük XU100 |
| Tepki | 612 bildirimde hesaplandı, 601'inde 3 günlük CAR dolu |
| Finansal | 933 dönem kaydı; bildirimlerin %97,4'ünde TTM çözülüyor |
| Altın küme | 50 bildirim elle etiketli |
| Çıkarım doğruluğu | 47/50 tam doğru (%94); skor 49/50'de elle etiketle aynı |
| Test | 221 |

## Canlı koşu

`.github/workflows/gunluk.yml` hafta içi her akşam 19:30'da (İstanbul)
`scripts/gunluk.py`'yi koşar. Orkestratör yeni bir hat değil; yukarıdaki
betikleri kısa aralıkla ve sırayla çağırır:

```
liste+detay → DB → kur → finansal → fiyat → faktör → VBTS → çıkarım (LLM) → tepki → bağlam
```

Üç tasarım kararı:

- **Açık pencere arşivlenmez.** Dünü ya da bugünü içeren liste penceresi
  yarımdır; arşive girerse o günün sonraki bildirimleri bir daha sorulmaz.
- **Fiyat düne kadar çekilir.** Kapanışlar üzerine yazılmıyor; seans içinde
  gelen yarım bir kapanış kalıcı olurdu.
- **Soğuk başlangıç korumalı.** Ham arşiv CI önbelleğinde taşınıyor. Önbellek
  yoksa arşiv önce tam aralıkla yeniden kuruluyor (tamamlandığında
  `data/ham/liste/.tam` yazılır); yarım arşivle bağlam hesabı koşarsa
  veritabanındaki tahta ve sıklık değerlerini eksik sayımla ezerdi.

Sırlar (`DATABASE_URL`, `GEMINI_API_KEY`) GitHub Secrets'ta; iş akışı koşu
başında geçici bir `.env` yazar.

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Linux/macOS: .venv/bin/pip
cp .env.example .env                    # sonra .env'i doldur
```

Şema `supabase/migrations/` altında. Python 3.13 gerekiyor.

## Çalıştırma

```bash
python scripts/backfill_calistir.py      # KAP bildirim arşivi
python scripts/kur_cek.py                # TCMB kurları
python scripts/fiyat_cek.py              # kapanış + XU100
python scripts/tepki_hesapla.py          # CAR
python scripts/finansal_cek.py           # finansal raporlar
python scripts/finansal_yukle.py         # TTM hasılat tablosu

python scripts/cikarim_kosu.py --adet 20             # KURU: maliyet tahmini
python scripts/cikarim_kosu.py --adet 20 --calistir  # ücretli çağrı
python scripts/dogruluk_olc.py --ayrinti             # ücretsiz yeniden ölçüm
```

`cikarim_kosu.py` **varsayılan olarak kuru koşar**; `--calistir` verilmeden tek
bir ücretli çağrı yapılmaz. Ölçüm koşudan ayrı: çıkarımlar veritabanında
durduğu için prompt ya da karşılaştırma kuralı değiştiğinde aynı satırlar para
harcanmadan yeniden puanlanır.

## Test

```bash
python -m pytest
python -m pyflakes scripts src tests   # testler scripts/ altını koşturmuyor
```

Ağa çıkan testler ayrı: `scripts/kap_duman_testi.py` zinciri gerçek KAP'a karşı
doğruluyor.

## Veri kaynakları

KAP (Kamuyu Aydınlatma Platformu), TCMB günlük döviz kurları, Yahoo Finance
(BIST kapanışları). Ham arşivler depoya girmiyor.

## Terim sözlüğü

| Türkçe | English |
|---|---|
| bildirim | disclosure |
| çıkarım | extraction (LLM) |
| kapı | gate (validation) |
| ciro / hasılat | revenue |
| tepki | market reaction (CAR) |
| tahta | trading board state (circuit breakers, VBTS) |
| sıklık | disclosure frequency |
| depo / arşiv | repository layer / raw archive |
| yayına hazır | publishable |

## Lisans

Kod MIT lisanslı (`LICENSE`). KAP metinleri ve ham veriler depoda yok ve bu
lisansın kapsamında değil.
