# KAP·RADAR

> **In English:** A data product that measures Borsa Istanbul "New Business
> Relation" disclosures (KAP) against each company's own size: contract value
> divided by the company's point-in-time trailing-twelve-month revenue. An LLM
> only extracts amounts from free text; every number must quote its source
> sentence verbatim, and a 13-rule deterministic gate rejects anything else
> (including amounts that are not revenue, such as a tender's estimated cost).
> Measured on a hand-labelled gold set: 47 of 50 disclosures exactly right.
> Extracting a full year of history cost $0.49. Runs every weekday on GitHub
> Actions. Live site: [kap.calibresolve.com](https://kap.calibresolve.com) ·
> case study (Turkish): [/proje-hakkinda](https://kap.calibresolve.com/proje-hakkinda).
> Built with AI coding tools (Claude Code); scope, architecture and validation
> decisions are the author's. Identifiers are Turkish; see the glossary.

**KAP'taki her yeni iş duyurusunu şirketin kendi cirosuna göre ölçer.**

Eylül 2026'da ASTOR 1,65 milyar TL'lik bir iş duyurdu: yıllık cirosunun %3,9'u.
Ağustos'ta SKYLP 84 milyon TL'lik bir iş duyurdu: cirosunun %33,5'i. Manşette 20
kat büyük olan rakam, şirket için 8 kat daha hafif. KAP metni bu bağlamı vermez;
bu depo onu her iş günü bütün bildirimler için çıkaran veri hattı ve site.

> **Yatırım tavsiyesi değildir.** Fiyat tahmini ya da alım-satım sinyali
> üretmez. Her sayı kaynak KAP bildirimine ve metindeki cümlesine bağlıdır.

---

## Ne gösteriyor

- **Her bildirim için oran ve kademe:** işin TL tutarı ÷ şirketin bildirim
  anındaki son 12 aylık cirosu. %5 ve üstü önemli, %15 ve üstü mega iş.
- **Her şirket için son 12 ay:** kaç iş duyurdu, toplamı cirosunun kaç katı,
  kimlerle; duyurduğu işlerin yanında gerçekleşen, enflasyondan arındırılmış
  ciro büyümesi.
- **Her sayının kanıtı:** bildirim sayfasında tutarın çıkarıldığı ham cümle.

## Hat

```
KAP listesi ──► ham arşiv (disk) ──► Postgres
                                      │
   TCMB kurları ─────────────────────►│
   Finansal raporlar (XBRL, TTM) ────►│
                                      ▼
                         çıkarım (LLM, katmanlı)
                                      ▼
                        doğrulama kapısı (13 kural)
                                      ▼
                     oran ve kademe ──► site (Next.js)
```

**Dil modelinin tek işi serbest metinden tutarları çıkarmak.** Karşı taraf,
başlangıç tarihi, güncelleme ve düzeltme bayrakları KAP'ın yapılandırılmış
alanlarından deterministik geliyor. Kur çevrimi, ciro ve oran düz kod; modele
hiç aritmetik verilmiyor.

## Doğrulama kapısı

Model her tutarı, para birimini ve kalem tipini metindeki birebir alıntısıyla
vermek zorunda. Kapıdan geçmeyen bildirim yayınlanmaz; kısmi yayın yok.

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
şüphesidir, doğrudan elle inceleme kuyruğuna düşer. İnsan kararı gerekçesiyle
kayda geçer ve sitede görünür.

A7 ve B4–B6 bir denetimden doğdu. Eylül 2026'da bir okur, bir belediye
ihalesinin muhammen bedelinin şirketin geliri gibi ölçüldüğünü fark etti: A1–A3
sayının metinde **geçtiğini** denetliyor, **neyin sayısı olduğunu**
denetlemiyordu. Yayındaki 1.272 bildirim kural tabanlı bir tarayıcıdan geçti,
işaretlenen 453'ün yaklaşık 150'si elle okundu, 10 kesin yanlış büyüklük
bulundu ve bu hata sınıfı kapıya eklendi. Denetim artık her akşamki koşunun
sonunda çalışıyor (`docs/arastirma/2026-09-26-veri-denetimi.md`).

## Payda: bildirim anındaki son 12 aylık ciro

Payda iki şartı birden karşılamak zorunda: son 4 çeyrek **ve** bildirim anında
açıklanmış olmak. Sonradan yayınlanan rapor geçmişe yazılmaz. Tek bir ara
dönem raporu iki bileşeni birden veriyor:

```
TTM = FY(önceki yıl) + YTD(cari) − YTD(geçen yıl aynı dönem)
```

**Enflasyon muhasebesi (TMS 29) oranı sessizce %7–25 büyütüyordu.** Her rapor
geçen yılın rakamlarını bugünün satın alma gücüyle yeniden yazıyor; formülün
iki terimi bugünün TL'siyle, biri geçen yılın TL'siyle geliyordu. Arşivdeki
rapor çiftlerinin yaklaşık %91'i yeniden ifade edilmişti. Düzeltme dış veri
kullanmıyor: eski terim, şirketin kendi raporlarından okunan katsayıyla
bugünün birimine taşınıyor. TMS 29'a geçiş yılında resmî TÜFE kullanılıyor.

Gerçek veriden öğrenilen başka tuzaklar: gelir tablosunun XBRL rolü sabit
değil, "Sunum Para Birimi" `1.000 TL` olabiliyor ve şirket bu beyanı yanlış da
yazabiliyor (yükleyici her şirketin kendi serisindeki medyana bakıp aykırı
raporu almıyor).

## Ölçülen doğruluk ve maliyet

| | |
|---|---|
| Çıkarım doğruluğu | Elle etiketlenmiş 50 bildirimde 47 tam doğru; büyüklük 49'unda elle hesaplananla aynı |
| Ölçüm | `scripts/dogruluk_olc.py`; saklı çıkarımlar üzerinden koşar, dil modeli gerekmez |
| Maliyet | 2024-09'a uzanan 690 bildirimlik geçmişin çıkarımı 0,487 USD; günlük koşu ayda birkaç sent |
| Test | Python 434, site 75 |

Güncel arşiv sayıları canlı sitede: `/proje-hakkinda` her tazelemede
veritabanından hesaplıyor.

## Canlı koşu

`.github/workflows/gunluk.yml` hafta içi her akşam 19:30'da (İstanbul)
`scripts/gunluk.py`'yi koşar. Orkestratör betikleri sırayla çağırır; ücretli
dil modeli çağrıları katmanlı ve sınırlı.

Üç tasarım kararı:

- **Açık pencere arşivlenmez.** Dünü ya da bugünü içeren liste penceresi
  yarımdır; arşive girerse o günün sonraki bildirimleri bir daha sorulmaz.
- **Fiyat düne kadar çekilir.** Kapanışlar üzerine yazılmıyor; seans içinde
  gelen yarım bir kapanış kalıcı olurdu.
- **Soğuk başlangıç korumalı.** Ham arşiv CI önbelleğinde taşınıyor. Önbellek
  yoksa arşiv önce tam aralıkla yeniden kuruluyor (tamamlandığında
  `data/ham/liste/.tam` yazılır).

Sırlar GitHub Secrets'ta; iş akışı koşu başında geçici bir `.env` yazar.

## Nasıl çalışıldı

Kod Claude Code ile birlikte yazıldı; commit'lerde `Co-Authored-By` ile
işaretli. Kapsam, mimari, doğrulama ve yayın kararları Hüseyin Dinçer'in. Her
büyük değişiklik önce yazılı bir tasarım ve plan (`docs/superpowers/`), sonra
testli küçük adımlar, en sonda tarayıcıda doğrulama olarak ilerliyor.

Depoda Eylül 2026'da yapılıp kapatılan bir araştırmanın notları ve analiz
betikleri de duruyor (`docs/arastirma/`, `scripts/analiz_*`). Ürün bunları
kullanmıyor.

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Linux/macOS: .venv/bin/pip
cp .env.example .env                    # sonra .env'i doldur
```

Şema `supabase/migrations/` altında. Python 3.13 gerekiyor. Site için `site/`
içinde `npm install` ve `.env.local.example`'dan `.env.local`.

## Çalıştırma

```bash
python scripts/gunluk.py                 # günlük koşunun tamamı (ücretli adım yok)
python scripts/gunluk.py --llm           # ücretli çıkarım dahil

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
python -m pytest                    # Python
cd site && npm test && npm run typecheck   # site
```

Ağa çıkan testler ayrı: `scripts/kap_duman_testi.py` zinciri gerçek KAP'a karşı
doğruluyor.

## Veri kaynakları

KAP (Kamuyu Aydınlatma Platformu), TCMB günlük döviz kurları, TÜİK TÜFE
(TCMB'nin yayımladığı tablodan), fonların KAP'taki Portföy Dağılım Raporları,
Yahoo Finance (BIST kapanışları). Ham arşivler depoya girmiyor.

## Terim sözlüğü

| Türkçe | English |
|---|---|
| bildirim | disclosure |
| çıkarım | extraction (LLM) |
| kapı | gate (validation) |
| ciro / hasılat | revenue |
| kademe | size tier (routine / significant / mega) |
| sıklık | disclosure frequency |
| depo / arşiv | repository layer / raw archive |
| yayına hazır | publishable |

## Lisans

Kod MIT lisanslı (`LICENSE`). KAP metinleri ve ham veriler depoda yok ve bu
lisansın kapsamında değil. `site/public/film/` altındaki tanıtım filmi ve
içindeki müzik de bu lisansın kapsamında değildir.
