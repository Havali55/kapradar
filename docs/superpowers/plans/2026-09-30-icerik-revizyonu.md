# İçerik revizyonu: araştırmayı kapatıp ürün diline dönüş (2026-09-30)

> **Ajanlar için:** Bu plan inline yürütülür (superpowers:executing-plans).
> Metinler tek sesle yazılmalı, o yüzden görevler alt ajanlara dağıtılmaz.
> Adımlar `- [ ]` ile işaretli.

**Amaç:** Dalga 1'in çıktılarını sitedeki ve depodaki metinlere yansıtmak.
Aşırı iddiaları yumuşatmak, K çarpanını bir şeffaflık ayarı olarak yeniden
konumlandırmak, araştırmayı yazılı bir kapanışla bitirmek.

**Yaklaşım:** Yeni analiz yok. Her sayı `docs/arastirma/` altındaki
commit'lenmiş notlardan geliyor. Makalenin üst katmanı (ilk ekran)
yeniden yazılıyor, gövdesi yerinde ve tarihli notlarla düzeltiliyor. Vaka
sayfasına mevcut içerikten iki bölüm ekleniyor. Ürünün davranışı, skorlar
ve veritabanı değişmiyor.

**Teknoloji:** Statik HTML (`site/content/metodoloji.html`), Next.js TSX
sayfaları, Markdown.

**Kaynak:** Hüseyin'in 30.09.2026 yönlendirmesi: proje bir veri ürünü ve bir
mühendislik vaka çalışması, akademik makale değil. Uzun çekimler ve yeni
ekonometrik sınavlar yapılmayacak.

---

## 0. Kararlar

### Bu yönlendirmeyle kapananlar (harita §8)

| # | Karar | Sonuç |
|---|---|---|
| Ka | K çarpanı | **A.** Değerler aynı kalıyor, anlatımı düzeltiliyor. K bir tepki tahmini değil, şeffaflık ayarı |
| Kb | Makale düzeltmeleri | **Uygulanıyor** (Görev 2–8) |
| Kc | S1 paketi (~4.400 istek, ~17 saat) | **Red.** Makalede "bilerek yapılmadı" olarak yazılıyor |
| Kd | Dalga 2 soruları | **Yapılmıyor.** Makalede "açık sorular" listesine giriyor |
| Ke | `arastirma/dalga-1` → master | Bu planın sonunda (Görev 13, onayla) |

### Onay bekleyen iki küçük karar

| # | Karar | Seçenekler | Öneri |
|---|---|---|---|
| Kf | Fon ve soruşturma bağlamında şirket adları | A: makalede kalsın · B: makaleden çıksın, notlarda kalsın | **B.** Bulguya bir şey eklemiyorlar. Vitrin metninde soruşturmayla aynı paragrafta anılmaları bir ima taşıyor |
| Kg | Eski üst özet (10 madde) ve K'nın 19.09 tablosu | A: sayfa sonunda `<details>` içinde "Sürüm geçmişi" · B: silinsin, git'te kalır | **A.** "Eski metin silinmiyor" geleneği sürüyor, ama okurun önüne çıkmıyor |

### Editör kuralları (bütün görevlerde)

1. Her iddia üç durumdan birinde yazılır: **ölçtük**, **bu veriyle
   cevaplanamıyor** ya da **bilerek ölçmedik**.
2. "Yok" yerine "bulunamadı" ya da "ayırt edilemiyor". Bir sonuç
   anlamsızsa yanına güç sınırı (MDE) yazılır.
3. Tarihli düzeltme geleneği sürüyor. Ama ilk ekran güncel ve temiz
   olmalı. Düzeltme notları gövdede kalır.
4. Yeni sayı üretilmez. Kullanılan her sayının kaynağı bu planda yazılı.

## Dosya haritası

| Dosya | Değişiklik |
|---|---|
| `docs/arastirma/2026-09-29-arastirma-haritasi.md` | Durum satırı, §2'de iki satır, yeni §9 Kapanış |
| `site/content/metodoloji.html` | Sürüm 3.0: üst katman, K bölümü, Bulgu 1/2/3/4/11 notları, fon dili, Sınırlar, açık sorular, VIII, künye |
| `site/app/metodoloji/page.tsx` | `metadata.description` |
| `site/app/proje-hakkinda/page.tsx` | 05 yeniden yazım, iki yeni bölüm (Payda, Nerede durduk), numaralar, `metadata.description` |
| `site/components/BildirimDetayi.tsx` | K açıklamasına bir cümle |
| `README.md` | İngilizce özete bir paragraf, K satırı, eskimiş "Ölçülen durum" tablosu |
| Hafıza | Kullanıcı ve proje notları |

Dokunulmayanlar: skor ve kademe kodu, veritabanı, `docs/arastirma/`
altındaki diğer notlar (tarihî kayıt), film (videodaki metni göremiyorum).

## Kaynak sayılar (yalnız bunlar kullanılır)

| Sayı | Kaynak |
|---|---|
| Plasebo AV 7Y +%2,2 (t 1,03); A1 +%11,3 (t 2,55); CAR3 olaysız \|t\| < 0,9; 20.354 olaysız gün | `2026-09-29-plasebo-ve-sira-sinavlari.md` Özet |
| Net hacim A +%27,4 (t 6,15), B +%20,8 (t 3,83), C +%33,9 (t 7,78) | aynı |
| Net CAR3 A +1,64 (t 4,30), B +0,76 (t 1,51), C +0,68 (t 2,98); A−C z −2,17 | aynı |
| Ön hacim, rastgele günlere göre: 7Y +%4,9 (t 2,06), C +%10,5 (t 2,79); olaysız günlerde tabanın %3–5 altında | aynı |
| KP-BMP plaseboda C +2,09 | aynı |
| K sınama yılı 663 olay; K-H1 −0,16 (t −0,29), ilk yıl +1,21; 612'nin 123'ü yeniden sınıflandı; −5,18 (n 6) → +0,31 (n 17) | `2026-09-29-k-carpani-sinamasi.md` Özet |
| Kore: Woo ve Park 2017, 6.072 olay, AR[0] +0,69, devir hızı +%40,4 | `2026-09-29-literatur-taramasi.md` §1 |
| Kore Kasım 2024: karşı taraf ve tutar birlikte gizlenemez, gizleyen uyarı yazar | aynı §4, kaynak 54–55 (tam metin) |
| Ellis, Fee, Thomas 2012: gizlilik rakibe bilgi verme maliyetiyle açıklanıyor | aynı §4, kaynak 33 (özet) |
| MDE ~0,6 puan/S (CAR3 ~ S) | metodoloji VII |
| S1: ~4.400 istek, kota hızıyla ~17 saat | `2026-09-29-veri-envanteri.md`, harita §8 |
| TMS 29: DCTTR 2,51 → 3,28; 1.074 çiftin ~%91'i; oran %7–25 büyük; 51 ve 13 bildirimin kademesi | metodoloji II "Paydayı sessizce bozan dört şey" |

---

### Görev 1: Araştırma haritası ve hafıza: kapanış kaydı

**Dosyalar:**
- Değiştir: `docs/arastirma/2026-09-29-arastirma-haritasi.md:3-6` (Durum)
- Değiştir: aynı dosya §2, "Ön hacim (Bulgu 2)" ve "K çarpanı" satırları
- Ekle: aynı dosyanın sonuna §9
- Hafıza: `arastirma-dalgalari.md`, `hüseyin-calisma-bicimi.md`

- [ ] **Adım 1: Durum satırını değiştir**

```markdown
**Durum: ARAŞTIRMA KAPANDI (2026-09-30).** Dalga 1 tamamlandı. Dalga 2 ve
3 yapılmayacak; proje ürün ve vitrin odağına döndü (§9). Aşağıdaki
metin 29.09'daki hâliyle duruyor.

*(Önceki durum satırı: DALGA 1 TAMAMLANDI, 2026-09-29 akşamı.)*
```

- [ ] **Adım 2: §2'deki iki satırı güncelle**

```markdown
| Ön hacim (Bulgu 2) | Tabana göre artış yok (temiz, 7 yıl −%0,8, t −0,3). Rastgele günlere göre +%4,9 (t 2,06). Sızıntı ne doğrulanıyor ne dışlanıyor | 7 yıl | K1 §4 H2, D1-P |
| K çarpanı | Örneklem dışında dört iddianın hiçbiri tekrarlanmadı. Şeffaflık ayarı olarak yeniden konumlandı (§9) | 2 yıl | D1-K |
```

- [ ] **Adım 3: Sona §9'u ekle**

```markdown
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

Uygulama planı: `docs/superpowers/plans/2026-09-30-icerik-revizyonu.md`.
```

- [ ] **Adım 4: Hafızayı güncelle.** `hüseyin-calisma-bicimi.md`'ye:
  Hüseyin yazılımcı ve ürün geliştirici, ekonometrist değil. Proje bir
  veri ürünü ve fintech veri/ürün liderlerine gösterilecek bir vaka
  çalışması. Araştırma karadeliği açacak iş (uzun çekim, yeni sınav)
  önerilmez. `arastirma-dalgalari.md`: araştırma 30.09'da kapandı, sıradaki
  iş bu plan.

- [ ] **Adım 5: Commit**

```bash
git add docs/arastirma/2026-09-29-arastirma-haritasi.md docs/superpowers/plans/2026-09-30-icerik-revizyonu.md
git commit -m "Arastirma kapanisi: harita §9, icerik revizyonu plani"
```

---

### Görev 2: Makale, ilk ekran (sürüm 3.0)

**Dosya:** `site/content/metodoloji.html:258-291`

İlk ekran bugün 2.4'ün 10 maddelik özetini gösteriyor. Dördüncü madde
örneklem dışında çökmüş Bulgu 10'u hâlâ bulgu diye sunuyor. Birinci madde
ilk yılın rakamlarıyla açılıyor. Karo sayıları (613 / 480 / 423) ilk
sürümden kalma.

- [ ] **Adım 1: Sürüm satırı (`:258`)**

```html
<div class="ust-et">ARAŞTIRMA NOTU · SÜRÜM 3.0 · 30 EYLÜL 2026</div>
```

- [ ] **Adım 2: İkinci giriş paragrafı (`:268`)**

```html
<p class="giris">Sınavın sonucu karışık ve öyle raporlanıyor: ürünün ana iddiaları yedi yılda ve üç para rejiminde tekrarlandı, ilk yılın iki bulgusu örneklem dışında çöktü, bazı sorulara da bu veriyle cevap verilemiyor. Hangisinin hangisi olduğu aşağıdaki tabloda.</p>
<div class="not" style="margin-bottom:28px;">
  <div class="et">SÜRÜM 3.0 · 30.09.2026</div>
  <p style="margin-bottom:0;">Araştırma bu sürümle kapandı. Yeni analiz yok, üç düzeltme var: K çarpanı bir tepki tahmini değil, şeffaflık ayarı olarak anlatılıyor (II). “Sızıntı yok” okuması yumuşatıldı (Bulgu 2). Ölçü aleti olay olmayan rastgele günlerle sınandı; net değerler eklendi (IV, rejim bölümü). Sayılar <code>docs/arastirma/</code> altındaki 29.09 notlarından.</p>
</div>
```

- [ ] **Adım 3: `<div class="ozet">…</div>` bloğunu (`:270-284`) iddia tablosuyla değiştir.** Eski blok Kg kararına göre sayfa sonuna taşınır (Görev 8, Adım 5).

```html
<div class="ozet">
  <h4>Ne iddia ediyoruz, ne iddia etmiyoruz</h4>
  <div class="tablo-sar">
    <table>
      <thead><tr><th>SORU</th><th>DURUM</th><th>NE ÖLÇTÜK</th></tr></thead>
      <tbody>
        <tr><td>Yeni iş bildirimi gerçek bir olay mı?</td><td><span class="cip cip-y">EVET, 7 YILDA</span></td><td>Bildirim günü işlem hacmi her para rejiminde normalin üstünde. Aynı ölçü olay olmayan rastgele günlerde sıfıra yakın; rastgele günlere göre net +%21 … +%34 (3.091 bildirim, 2020–2026).</td></tr>
        <tr><td>Büyüklük bir getiri tahmini mi?</td><td><span class="cip cip-y">HAYIR, TASARIM GEREĞİ</span></td><td>Skor ile 3 günlük tepki arasında iki yılda da ilişki bulunamadı. Bu “ilişki yok” demek değil: örneklemin yakalayabileceği en küçük eğim ~0,6 puan/S.</td></tr>
        <tr><td>Piyasa bildirime ortalamada nasıl tepki veriyor?</td><td><span class="cip cip-y">POZİTİF</span></td><td>3 günde +0,7 … +1,6 puan (rastgele günlere göre net). Büyüklüğü döneme bağlı; 2020–23'ün gevşek parasında 2024–26'nın iki katından fazla.</td></tr>
        <tr><td>Oynak tahtada durum farklı mı?</td><td><span class="cip cip-y">EVET, 7 YILDA</span></td><td>Tepki her dönemde daha zayıf. Ortalamanın eksiye dönmesi yalnız 2024–26'da ve tasfiye edilen fonların yoğun tuttuğu paylarda. Mekanizma bilinmiyor.</td></tr>
        <tr><td>Bilgi duyurudan önce sızıyor mu?</td><td><span class="cip cip-m">CEVAPLANAMIYOR</span></td><td>Hacim ölçüsü bu soruya yetecek hassasiyette değil; getiri tabanlı bir ön sınav yapılmadı. Ürün bir sızıntı iddiası taşımıyor.</td></tr>
        <tr><td>Karşı tarafın gizli olması tepkiyi değiştiriyor mu?</td><td><span class="cip cip-r">DAYANAK YOK</span></td><td>İlk yıldaki fark örneklem dışında tekrarlanmadı. K bu yüzden bir tepki ayarı değil, doğrulanabilirlik ayarı olarak duruyor (II).</td></tr>
        <tr><td>Çok iş duyuranlar sonra gerçekten büyüdü mü?</td><td><span class="cip cip-m">ZAYIF, TEK DÖNEM</span></td><td>Üst üçte birin reel ciro büyümesi medyanı +%20,8; sıra korelasyonu 0,24 (t = 1,91). Betimleyici, nedensel değil (V).</td></tr>
        <tr><td>İlk yılın bulgularının hepsi tuttu mu?</td><td><span class="cip cip-r">İKİSİ ÇÖKTÜ</span></td><td>Bildirim yorgunluğu (Bulgu 7) ve tahtaya göre ayrışma (Bulgu 10) görülmemiş yılda tekrarlanmadı. Metinde duruyorlar, üründen çıkarıldılar.</td></tr>
      </tbody>
    </table>
  </div>
</div>
```

  Tablodaki özet rakamların kaynağı: "net +%21 … +%34" = plasebo netleri
  B +%20,8 … C +%33,9. "+0,7 … +1,6" = net CAR3 C +0,68 … A +1,64.

- [ ] **Adım 4: Karolar (`:286-291`)**

```html
<div class="izgara" style="margin-bottom:56px;">
  <div><div class="et">SINAMA</div><div class="say">3.091</div><div class="say-et">bildirim · 7 yıl · üç para rejimi</div></div>
  <div><div class="et">ÇIKARIM DOĞRULUĞU</div><div class="say">47/50</div><div class="say-et">elle etiketlenmiş altın kümede tam doğru</div></div>
  <div><div class="et">ÇÖKEN BULGU</div><div class="say">2</div><div class="say-et">örneklem dışında; metinde işaretli duruyor</div></div>
  <div><div class="et">ÜRETİLEN TAHMİN</div><div class="say">0</div><div class="say-et">fiyat, hedef ya da yön tahmini</div></div>
</div>
```

- [ ] **Adım 5: Commit** (Görev 3–8 ile birlikte tek commit de olabilir)

---

### Görev 3: Makale, K bölümü

**Dosya:** `site/content/metodoloji.html:374-387`

- [ ] **Adım 1: Başlık ve ilk paragraf (`:374-375`)**

```html
<h4>K: bilginin netliği</h4>
<p>İkinci bileşen, bildirimin dışarıdan ne kadar doğrulanabildiğini yansıtır. Karşı tarafın adı verilmemişse iş bağımsız olarak doğrulanamaz. Duyuru daha önce açıklanmış bir işin güncellemesiyse haberin bir kısmı zaten biliniyordur. K bu iki durumda skoru aşağı çeker. <strong>Çarpımsaldır, toplamsal değil:</strong> karşı tarafı gizli dev bir sözleşme hâlâ devdir, yalnız doğrulanması daha zordur.</p>
<p><strong>K bir tasarım tercihi, ampirik bir katsayı değil.</strong> Değerler getiriden ya da hacimden türetilmedi ve bir tepki tahmini iddia etmiyor. Gerekçe kurumsal. Düzenleyiciler de gizli karşı tarafı bir şeffaflık riski sayıyor: Kore, Kasım 2024'ten beri aynı tür bildirimde karşı taraf ile tutarın ikisinin birden gizlenmesine izin vermiyor ve gizleyen şirketten bildirime yatırımcı uyarısı yazmasını istiyor. Gizlilik kendi başına kötü niyet de değil; şirket müşterisini rakiplerinden saklamak için gizleyebilir (Ellis, Fee ve Thomas 2012). K bu ikisini ayırt etmez. Yalnız okurun doğrulayabildiği bilgiyle doğrulayamadığını ayırır.</p>
<p><strong>Ürüne etkisi sınırlı.</strong> Kartta görünen büyüklük kademesi (rutin / önemli / mega) K'dan etkilenmez, doğrudan ciro oranından okunur. K yalnız hesap dökümündeki S'yi ve Modül C'nin akran grubunu etkiler.</p>
```

- [ ] **Adım 2: Tabloyu (`:376-386`) sadeleştir.** Tepki sütunları çıkıyor; eski tablo Kg'ye göre Adım 3'teki `<details>` içine taşınıyor.

```html
<div class="tablo-sar">
  <table>
    <thead><tr><th>DURUM</th><th class="sag">K</th><th>NEDEN</th></tr></thead>
    <tbody>
      <tr><td>Karşı taraf açık + ilk bildirim</td><td class="s v">1,00</td><td>Doğrulanabilir, yeni</td></tr>
      <tr><td>Karşı taraf açık + güncelleme</td><td class="s v">0,85</td><td>Doğrulanabilir, kısmen biliniyor</td></tr>
      <tr><td>Karşı taraf gizli + ilk bildirim</td><td class="s v">0,70</td><td>Doğrulanamıyor, yeni</td></tr>
      <tr><td>Karşı taraf gizli + güncelleme</td><td class="s v">0,50</td><td>Doğrulanamıyor, kısmen biliniyor</td></tr>
    </tbody>
  </table>
</div>
```

- [ ] **Adım 3: `:387` paragrafını tarihli düzeltme notuyla değiştir**

```html
<div class="uyar" style="margin-top:18px;">
  <div class="et">30.09.2026 DÜZELTMESİ</div>
  <p>Bu bölümün 2.4 sürümü, ilk yılın karşı taraf × güncelleme tablosunu (3 günlük tepki ve anormal hacim) K için bir “sağlama” sayıyor ve “n ≥ 55 olan üç hücrede anormal hacim sıralaması K sıralamasıyla birebir uyumlu” diyordu. Bu cümle tutmuyor.</p>
  <ul style="margin-bottom:0;">
    <li>Bulgular kurulurken görülmemiş yılda (663 bildirim) tablonun dört iddiasının hiçbiri tekrarlanmadı, üçünde yön ters. Örnek: açık + ilk ile gizli + ilk arasındaki tepki farkı −0,16 puan (t = −0,29); ilk yılda +1,21.</li>
    <li>25.09'daki karşı taraf sınıflaması düzeltmesi ilk yılın 612 bildiriminden 123'ünü “açık”tan “gizli”ye taşıdı. Bugünkü veriyle ilk yılın kendi hacim sıralaması da tutmuyor. K = 0,50'nin dayandığı −%5,18 (n = 6), 17 bildirimle +%0,31.</li>
    <li>K'nın değerleri değişmedi. Değişen, onun ne olduğunun anlatımı. Ayrıntı: <code>docs/arastirma/2026-09-29-k-carpani-sinamasi.md</code>.</li>
  </ul>
  <details style="margin-top:12px;"><summary>2.4 sürümündeki tablo ve paragraf (19.09 verisi)</summary>
    <!-- :376-387'nin eski hâli buraya birebir taşınır -->
  </details>
</div>
```

  Yorum satırı yer tutucu değil, taşıma talimatı: eski `<div class="tablo-sar">…</div>` ve `<p style="margin-top:14px;">…</p>` birebir kopyalanır.

- [ ] **Adım 4:** `:372`'deki "Sebep K: … K bir güvenilirlik ayarı, büyüklük değil." cümlesinde "güvenilirlik ayarı" → "doğrulanabilirlik ayarı".

---

### Görev 4: Makale, Bulgu 2 ve "sızıntı" cümleleri

**Dosya:** `site/content/metodoloji.html`

- [ ] **Adım 1: Bulgu 2 başlığının çipi (`:557`)** `YORUM 27.09'DA ZAYIFLADI` → iki çip: `YORUM 27.09'DA ZAYIFLADI` (cip-r) + `AÇIK SORU` (cip-m).

- [ ] **Adım 2: `:558`'den önce yeni paragraf**

```html
<p><strong>Güncelleme (30.09.2026): “sızıntı yok” demek de fazla.</strong> 28.09'daki yedi yıllık sınama, temiz olaylarda ön hacmi tabana göre sıfır buldu (−%0,8). Ama aynı ölçü olay olmayan rastgele günlerde de sıfır değil, tabanın %3–5 altında. Gerçek olaylar rastgele günlerle kıyaslanınca ön hacim yedi yılda +%4,9 (t = 2,06), 2024–26'da +%10,5 (t = 2,79) fazla. Bunun mekanik bir açıklaması olabilir: bir önceki duyurunun hacmi ön pencereye taşıyor olabilir. Bu ölçülmedi. Başka piyasalarda (Kore, ABD, BIST-30 haberleri) duyuru öncesi pozitif getiri raporlanıyor; bizde getiri tabanlı bir ön sınav yok. Doğru cümle: <strong>bu veriyle sızıntıyı ne doğrulayabiliyoruz ne dışlayabiliyoruz.</strong> Soru açık bırakıldı (VII); ürün bir sızıntı iddiası taşımıyor.</p>
```

- [ ] **Adım 3: Rejim bölümü "Okuma" maddesi (`:837`)**

```html
<li><strong>Ön hacimde tabana göre artış yok.</strong> 2024–26'daki artış şirketin kendi önceki açıklamalarından geliyordu; 2020–24'te o artış da yok. Bu, sızıntının yokluğunu göstermiyor: rastgele günlere göre ön hacim yüksek (30.09.2026, Bulgu 2). <em>İlk hâli: “‘Bilgi sızıyor’ yorumu hiçbir dönemde desteklenmiyor.”</em></li>
```

- [ ] **Adım 4: VII "Nedensellik iddiası yok" maddesi (`:956`)**

```html
<li><strong>Nedensellik iddiası yok.</strong> Bildirim öncesi hacim artışının yarısından fazlası şirketin önceki günlerdeki kendi KAP açıklamalarıyla örtüşüyor. Kalanı ne sızıntı olarak doğrulanabiliyor ne dışlanabiliyor (Bulgu 2, 30.09.2026).</li>
```

---

### Görev 5: Makale, plasebo ve literatür kıyası

**Dosya:** `site/content/metodoloji.html`

- [ ] **Adım 1: Rejim bölümünde, H tablosundan sonra ve "Okuma"dan önce (`:832`'den sonra)**

```html
<p><strong>Olay yokken ölçü ne diyor (29.09.2026).</strong> Aynı ölçüm kodu, aynı paylarda rastgele seçilen 20.354 olaysız günde çalıştırıldı. Olay yokken hacim ölçüsü yedi yılda +%2,2 (t = 1,03), 3 günlük tepki her dönemde sıfır (|t| &lt; 0,9). Yani ölçü aleti kendi kendine sinyal üretmiyor; tek istisna 2020–21'de hacimde +%11,3. Rastgele günlere göre net etkiler: hacim A +%27,4, B +%20,8, C +%33,9; tepki A +1,64, C +0,68 puan (B'de güç yetmiyor). Gevşek paradaki iki kat fark nete göre de duruyor (z = −2,17). Hükümlerin hiçbiri değişmedi. Ayrıntı: <code>docs/arastirma/2026-09-29-plasebo-ve-sira-sinavlari.md</code>.</p>
```

- [ ] **Adım 2: Bulgu 1'in son paragrafından sonra (`:555`'ten sonra)**

```html
<p>Bu büyüklük literatürde olağan. KAP şablonuna en yakın örnek Kore'nin zorunlu sözleşme bildirimi: 6.072 olayda duyuru sonrası işlem devir hızı +%40, duyuru günü getirisi +0,69 puan (Woo ve Park 2017). Tanımlar farklı, birebir karşılaştırma değil.</p>
```

---

### Görev 6: Makale, Bulgu 3, 4 ve 11'in dili

**Dosya:** `site/content/metodoloji.html`

- [ ] **Adım 1: Bulgu 3 (`:563-564`).** Çip `DOĞRULANDI` → `TEKRARLANDI`. Cümle: "S ile işaretli anormal getiri arasında hiçbir ilişki yok." → "S ile işaretli anormal getiri arasında ilişki bulunamadı; örneklem dışı yılda da bulunamadı."

- [ ] **Adım 2: Bulgu 3'ün son paragrafından sonra (`:576`)**

```html
<p>Bu “ilişki yok” demek değil. Bu örneklemle yakalanabilecek en küçük eğim ~0,6 puan/S. Literatür, sözleşme şirkete oranla büyüdükçe tepkinin büyüdüğünü buluyor (ABD'de sözleşme/varlık oranı, savunma ilanlarında piyasa değerine oran). Skorun iddiası zaten dar: büyüklüğü ölçer, tepkiyi tahmin etmez.</p>
```

- [ ] **Adım 3: Bulgu 4 (`:609`)** "Bulgu 10 bunu ele alıyor ve sonucu değiştiriyor." cümlesinin arkasına: `<em>(24.09.2026: Bulgu 10 örneklem dışında tekrarlanmadı; Bulgu 4'ün hükmü “sonuçsuz” olarak kalıyor.)</em>`

- [ ] **Adım 4: Bulgu 11 (`:718`)** "Skorun bir getiri tahmini olarak kurulmamasının gerekçesi buradan daha net görülemezdi." → "Skorun bir getiri tahmini olarak kurulmamasının gerekçelerinden biri bu. Güç sınırı ve literatürle gerilim için bkz. Bulgu 3."

---

### Görev 7: Makale, fon dili (Kf = B varsayımıyla)

**Dosya:** `site/content/metodoloji.html`

- [ ] **Adım 1: `:669` (bayrağın sınırı).** "[ad] … [ad] …" → "Soruşturmada adı geçen iki şirkette dönemden önceki 90 günde 11 ve 10 devre kesici günü var, dönem içinde 2 ve 2."

- [ ] **Adım 2: `:768`.** "Örneklemde iki sık bildirimci bu türden: OZATD (…) ve ODINE (…)." → "Örneklemde bu gruba giren iki sık bildirimci var: 29 ve 24 yeni iş bildirimi; tasfiye fonlarındaki pozisyonları 27 ve 10 günlük işlem hacmi."

- [ ] **Adım 3: `:840-842`.** Başlık "Fonlarla yükseltilen niş kağıtlar." → "Tasfiye edilen fonların yoğun tuttuğu paylar." Parantezdeki şirket listesi çıkar. "Bu kağıtlarda hacim ilginin temiz bir ölçüsü değil." → "Bu paylarda hacim ilginin temiz bir ölçüsü olmayabilir." "Bulgular bu kağıtlardan gelmiyor." → "Bulgular bu paylardan gelmiyor."

- [ ] **Adım 4: `:282` ve `:948`.** "(OZATD, ODINE)" parantezi çıkar. `:282` zaten Görev 2'de özetle birlikte `<details>`'e taşınıyor; orada eski hâli kalır (tarihî metin).

- [ ] **Adım 5: Kontrol**

```bash
grep -n "OZATD\|ODINE\|GESAN\|ALTNY\|EUPWR\|BOBET\|GUNDG\|Destek Faktoring" site/content/metodoloji.html
```

Beklenen: yalnız `<details>` içindeki eski metin satırları.

  Kf = A seçilirse bu görev yalnız Adım 3'ün ilk cümlesiyle sınırlı kalır.

---

### Görev 8: Makale, Sınırlar, açık sorular, yeniden üretim, künye

**Dosya:** `site/content/metodoloji.html`

- [ ] **Adım 1: VII ilk madde (`:946`).** "2020–24 bildirimlerinden henüz tutar çıkarılmadı." → "2020–24 bildirimlerinden tutar çıkarılmadı. Bu bilinçli bir kapsam kararı: ~4.400 KAP isteği, kota hızıyla ~17 saatlik bir çekim gerektiriyor ve kartta görünen hiçbir şeyi değiştirmiyor."

- [ ] **Adım 2: VII'ye iki madde ("Hacim ölçüsü tek bir tanıma dayanıyor" maddesinden sonra)**

```html
<li><strong>Hacim ölçüsü literatürün standart tanımından farklı.</strong> Standart, günlük hacim logaritmalarının ortalaması. Bizimki ortalamanın logaritmasından medyanın logaritmasını çıkarıyor. Rastgele günlerde bu farkın sapması küçük (+%2,2, anlamsız); yalnız 2020–21'de +%11,3. Net etkiler bu sapma çıkarılarak raporlandı (IV, rejim bölümü).</li>
<li><strong>Çarpıklığa dayanıklı sınavlar zayıf destek veriyor.</strong> Sıra ve standardize sınavlar (Kolari-Pynnönen düzeltmeli BMP ve diğerleri) hiçbir hükmü zayıflatmadı. Ama bu veride olay yokken de 2024–26'da “anlamlı” çıkıyorlar (plaseboda +2,09). Bu yüzden ek kanıt sayılmıyorlar.</li>
```

- [ ] **Adım 3: `</ul>`'den sonra (`:962`) yeni alt bölüm**

```html
<h4 id="acik-sorular">Bilerek açık bıraktığımız sorular <span class="cip cip-m" style="margin-left:6px;">30.09.2026</span></h4>
<p>Araştırma bu sürümle kapandı. Aşağıdaki sorular sınanmadı. Cevapları ürünün iddialarını değiştirmez, yalnız bilgi ekler. Hepsinin veri ve maliyet envanteri repoda: <code>docs/arastirma/2026-09-29-veri-envanteri.md</code>.</p>
<ul>
  <li><strong>Sızıntının getiri ayağı.</strong> Duyuru öncesi anormal getiri ve seans içi / seans sonrası ayrımı.</li>
  <li><strong>Üç günden uzun ufuk.</strong> Oynak tahtadaki eksi tepki sonradan geri dönüyor mu?</li>
  <li><strong>Büyüklüğe dayanan sınavların 2020–24'e taşınması.</strong> O yılların bildirimlerinden tutar çıkarımı gerektiriyor.</li>
  <li><strong>Tasfiye edilen fonların tuttuğu payların sonraki seyri.</strong></li>
  <li><strong>Söz ve gerçeğin ikinci dönemi.</strong> Bunun için iş gerekmiyor: 9A2026 raporları gelince site kendiliğinden yeni döneme geçiyor, metin veriden türüyor.</li>
</ul>
```

- [ ] **Adım 4: VIII (`:969-971`).** "Bu nottaki istatistikler beş betikten çıkıyor" → "Bu nottaki istatistikler şu betiklerden çıkıyor". Komut listesine ekle: ` · python scripts/analiz_plasebo.py · python scripts/analiz_k_carpani.py --mutabakat`.

- [ ] **Adım 5: Künye (`:984`) ve sürüm geçmişi.** Künyedeki son cümleye ekle: "Plasebo ve K sınaması 29 Eylül 2026. Araştırma 30 Eylül 2026'da kapandı." Künyeden sonra, `</main>`'den önce:

```html
<details style="margin-top:24px;"><summary>Sürüm geçmişi: 2.4 sürümünün özeti (28.09.2026)</summary>
  <!-- Görev 2 Adım 3'te kaldırılan <div class="ozet">…</div> bloğu birebir buraya -->
</details>
```

  Not: `site/app/metodoloji/page.tsx` gövdeyi `<main class="govde">…</main>` regex'iyle alıyor. Eklenen hiçbir metin `</main>` içermemeli.

- [ ] **Adım 6: Aşırı iddia taraması**

```bash
grep -n "birebir uyumlu\|hiçbir dönemde desteklenmiyor\|hiçbir ilişki yok\|Fonlarla yükseltilen\|daha net görülemezdi\|sızıntı penceresi" site/content/metodoloji.html
```

Beklenen: her eşleşme ya `<details>` içinde ya da "İlk hâli:" / tarihli not bağlamında. "sızıntı penceresi" (`:559`) Bulgu 2'nin ilk ölçümünü anlatıyor ve üstünde 27.09 ve 30.09 notları var; kalır.

- [ ] **Adım 7: Commit**

```bash
git add site/content/metodoloji.html
git commit -m "Metodoloji 3.0: arastirma kapanisi, K yeniden konumlandi, sizinti yumusatildi"
```

---

### Görev 9: Metodoloji sayfasının açıklaması

**Dosya:** `site/app/metodoloji/page.tsx:7-8`

- [ ] **Adım 1**

```ts
  description:
    "Skorun nasıl kurulduğu, neyi ölçtüğü ve neyi ölçmediği: yedi yıllık hacim sınaması, olay olmayan günlerle kıyas, örneklem dışında çöken bulgular ve sınırlar.",
```

---

### Görev 10: Vaka sayfası (proje hakkında)

**Dosya:** `site/app/proje-hakkinda/page.tsx`

Vitrinin asıl sayfası bu. 05'teki "Sınır" maddesi eskimiş (rejim sınaması 28.09'da yapıldı). Fintech veri ekiplerine en yakın hikâye olan TMS 29 düzeltmesi yalnız makalenin içinde duruyor.

- [ ] **Adım 1: `metadata.description` (`:12-13`)**

```ts
  description:
    "Vaka çalışması: KAP yeni iş bildirimlerini şirketin kendi cirosuna göre ölçen veri hattı; ölçülen doğruluğu, enflasyon muhasebesi tuzağı, bir denetimin hikâyesi, sınamalar ve bilerek yapılmayanlar.",
```

- [ ] **Adım 2: 02'den sonra yeni bölüm "03 · PAYDA"** (sonraki numaralar birer kayar: 04 Ölçülen doğruluk, 05 Denetim, 06 Ampirik sınama, 07 Söz ve gerçek, 08 Maliyet)

```tsx
      <section>
        <h2 className="mono">03 · PAYDA</h2>
        <h3>Enflasyon muhasebesi oranı sessizce %7–25 büyütüyordu</h3>
        <p>
          Oranın paydası şirketin son 12 aylık cirosu ve tek bir ara dönem
          raporundan kuruluyor: geçen yılın cirosu, artı bu yılın ilk aylarının
          cirosu, eksi geçen yılın aynı aylarının cirosu. Yüksek enflasyon
          muhasebesinden (TMS 29) beri her rapor geçen yılın rakamlarını
          bugünün satın alma gücüyle yeniden yazıyor. DCTTR&apos;nin 2024
          hasılatı ilk raporunda 2,51, bir yıl sonraki raporda 3,28 milyar TL.
          Formülün iki terimi bugünün TL&apos;siyle, biri geçen yılın
          TL&apos;siyle geliyordu. Payda küçük, oran %7–25 büyük çıkıyordu;
          arşivdeki rapor çiftlerinin yaklaşık %91&apos;i yeniden ifade
          edilmişti.
        </p>
        <p>
          Düzeltme dış veri kullanmıyor. Eski terim, şirketin kendi
          raporlarından okunan katsayıyla bugünün birimine taşınıyor: aynı
          dönemin ilk yayını ile yeniden ifadesinin oranı. Bildirim anında
          yayınlanmamış hiçbir rapor kullanılmıyor. TMS 29&apos;a geçiş yılında
          bu katsayı enflasyonu değil muhasebe geçişini ölçtüğü için o dönemde
          resmî TÜFE kullanılıyor. İki düzeltme önce 51, sonra 13 bildirimin
          kademesini değiştirdi, hiçbir bildirimin yayın kararını değiştirmedi.
          Aynı yeniden ifade, sitedeki ciro büyümesini dış veri olmadan reel
          ölçmeyi de sağlıyor.
        </p>
      </section>
```

- [ ] **Adım 3: 05 → 06 · AMPİRİK SINAMA, gövde (`:177-216`)**

```tsx
      <section>
        <h2 className="mono">06 · AMPİRİK SINAMA</h2>
        <h3>Yedi yılda sınandı; ikisi çöktü, biri açık soru</h3>
        <p>
          Büyüklük &ldquo;bu iş şirketin ölçeğine göre büyük&rdquo; der,
          &ldquo;hisse yükselecek&rdquo; demez. Bu yüzden asıl sınavı getiri
          değil işlem hacmi. Bulgular ilk yılda kuruldu, sonra hiç görülmemiş
          bir yılda ve 2020&apos;den bu yana üç para rejiminde (3.091
          bildirim) aynı kodla yeniden koşuldu. Ölçü aletinin kendisi de
          sınandı: aynı hesap olay olmayan rastgele günlerde çalıştırıldı ve
          orada sinyal üretmedi.
        </p>
        <ul>
          <li>
            <strong>Tuttu.</strong> Bildirim günü işlem hacmi her rejimde
            normalin üstüne çıkıyor; rastgele günlere göre net +%21 ile +%34
            arası. Büyüklük bir getiri tahmini değil: iki yılda da ilişki
            bulunamadı. %1&apos;in altındaki işlerde de ilgi var, bu yüzden
            ölçeğin tabanı %0,25&apos;e indirildi.
          </li>
          <li>
            <strong>Çöktü.</strong> &ldquo;Sık bildirimcide tepki sönük&rdquo; ve
            &ldquo;tahtaya göre ayrışma&rdquo; örneklem dışında tekrarlanmadı;
            sitede artık iddia edilmiyor.
          </li>
          <li>
            <strong>Açık kaldı.</strong> Hacmin bildirimden önce yükselmesi önce
            bir &ldquo;sızıntı&rdquo; gibi okundu, sonra &ldquo;sızıntı
            yok&rdquo;a döndü. İkisi de fazlaydı: bu ölçü o soruya cevap
            verecek hassasiyette değil. Ürün bir sızıntı iddiası taşımıyor.
          </li>
          <li>
            <strong>Yeniden konumlandı.</strong> Karşı tarafı gizli ya da
            güncelleme olan duyuruyu aşağı çeken K çarpanının ilk yıldaki
            &ldquo;sağlaması&rdquo; örneklem dışında tutmadı. K kalıyor, ama ne
            olduğu düzeltildi: bir tepki tahmini değil, dışarıdan
            doğrulanamayan bilgi için bir şeffaflık ayarı. Kartta görünen
            büyüklüğü etkilemiyor.
          </li>
        </ul>
        <p>
          Sayıların ve sağlamlık sınavlarının tamamı{" "}
          <Link href="/metodoloji">araştırma notunda</Link>.
        </p>
      </section>
```

- [ ] **Adım 4: 08 · MALİYET'ten sonra yeni bölüm "09 · NEREDE DURDUK"** (Nasıl çalışıldı → 10)

```tsx
      <section>
        <h2 className="mono">09 · NEREDE DURDUK</h2>
        <h3>Araştırmanın da bir kapsamı var</h3>
        <p>
          Ürünün iddiası dar: bir işin, şirketin kendi ölçeğine göre
          büyüklüğü. Bu iddiayı sınamak için yedi yıllık veri, örneklem dışı
          sınama ve rastgele gün kıyası yetti. Ötesindeki her soru ürünü
          değiştirmeden bilgi eklerdi; araştırma bu yüzden 30 Eylül 2026&apos;da
          kapandı. Bilerek yapılmayanlar:
        </p>
        <ul>
          <li>
            <strong>2020–24 bildirimlerinden tutar çıkarmak.</strong> Yaklaşık
            4.400 KAP isteği, KAP&apos;ın izin verdiği hızla ~17 saatlik bir
            çekim. Skora dayanan sınavları yedi yıla taşırdı; kartta görünen
            hiçbir şeyi değiştirmezdi.
          </li>
          <li>
            <strong>Yeni sınavlar.</strong> Sızıntının getiri tabanlı sınavı,
            üç günden uzun ufuk, fonların tuttuğu payların sonraki seyri.
            Araştırma notunda{" "}
            <Link href="/metodoloji#acik-sorular">açık sorular</Link> olarak,
            veri ve maliyet envanteriyle duruyor.
          </li>
          <li>
            <strong>Tahmin.</strong> Site alım-satım sinyali üretmiyor. Bu bir
            ihtiyat cümlesi değil, ölçümün sonucu: büyüklük 3 günlük tepkiyi
            bu örneklemde öngörmüyor.
          </li>
        </ul>
      </section>
```

- [ ] **Adım 5: Numara kontrolü**

```bash
grep -n 'className="mono">[0-9][0-9] ·' site/app/proje-hakkinda/page.tsx
```

Beklenen: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 sırayla.

---

### Görev 11: Bildirim sayfasındaki K açıklaması

**Dosya:** `site/components/BildirimDetayi.tsx:177-184`

- [ ] **Adım 1.** "…K 1&apos;in altına iner." cümlesinden sonra ekle: "K bir tasarım tercihi: getiriden ya da hacimden türetilmedi, bir tepki tahmini değil."

---

### Görev 12: README

**Dosya:** `README.md`

- [ ] **Adım 1: İngilizce özetin sonuna (`:12`'den sonra)**

```markdown
> Validation: the volume response was tested across seven years and three
> monetary regimes (3,091 disclosures, 2020–2026) and against randomly drawn
> non-event days. Two first-year findings failed out of sample; they stay in
> the write-up, marked. The score is a size measure, not a return forecast,
> and the research was deliberately closed once the product's claims were
> tested.
```

- [ ] **Adım 2: Skor bölümü (`:102-103`)**

```markdown
`K` bilginin netliği: karşı taraf gizliyse ya da duyuru bir güncellemeyse
skoru aşağı çeker (1,00 → 0,50). Bir tasarım tercihi; getiriden türetilmedi
ve örneklem dışında bir tepki farkı göstermedi (metodoloji II).
```

  `:107`'deki "K bir güvenilirlik ayarı" → "K bir doğrulanabilirlik ayarı".

- [ ] **Adım 3: "Ölçülen durum" (`:130-141`).** Başlık "Ölçülen durum (ilk sürüm, 19.09.2026)" olur. Tablonun altına: "Güncel sayılar canlı sitede, /proje-hakkinda sayfasında veritabanından hesaplanıyor." Test satırı güncellenir:

```bash
.venv/Scripts/python -m pytest --collect-only -q | tail -1
```

- [ ] **Adım 4: Commit**

```bash
git add site/app README.md site/components/BildirimDetayi.tsx
git commit -m "Vaka sayfasi: payda ve nerede durduk bolumleri; K dili"
```

---

### Görev 13: Doğrulama, birleştirme, yayın

- [ ] **Adım 1: Site kontrolleri**

```bash
cd site && npm run typecheck && npm test && npm run build
```

Beklenen: üçü de hatasız.

- [ ] **Adım 2: Tarayıcı.** `npm run dev`. `/metodoloji`, `/proje-hakkinda` ve bir bildirim sayfası (`/kap/<id>`), 1280 px ve 390 px genişlikte. İddia tablosu yatay kaydırma yaratmıyor (`tablo-sar` sarmalı), `<details>` açılıyor, `#acik-sorular` bağlantısı doğru yere iniyor, konsolda hata yok.

- [ ] **Adım 3: Birleştirme (Ke).** `arastirma/dalga-1` → `master`, `--no-ff`, repo geleneğindeki "Merge: …" mesajıyla. Commit'lenmemiş üç veri dosyası (`data/baglam_kap_v1.csv`, `data/fon_baski.csv`, `data/tepki_yedek_beta1_2026-09-22.csv`) birleştirmeye girmez.

- [ ] **Adım 4: Yayın. Hüseyin'in açık onayıyla.** `git push` → Vercel. Canlıda `/metodoloji` ve `/proje-hakkinda` bir kez daha açılır.

---

## Öz-denetim

- **Kapsam:** Yönlendirmedeki üç istek: (1) iddiaları yumuşatmak → Görev 2, 4, 6, 7. (2) K'yı şeffaflık riski olarak konumlandırmak → Görev 3, 10, 11, 12. (3) Hazır veriyle küçük eklemeler → Görev 5 (plasebo net, literatür kıyası), Görev 8 (Sınırlar). Paketleme → Görev 2 (ilk ekran), Görev 10 (vaka sayfası), Görev 12 (README). Kapanış kaydı → Görev 1.
- **Yeni analiz:** Yok. Her sayı "Kaynak sayılar" tablosunda.
- **Riskli nokta:** `metodoloji.html` satır numaraları ilk düzenlemeden sonra kayar. Her adım eşsiz bir metin parçasıyla bulunur; satır numarası yalnız yön gösterir.
