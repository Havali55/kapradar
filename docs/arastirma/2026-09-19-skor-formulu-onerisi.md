# Skor formülü — öneri (ONAY BEKLİYOR)

Tarih: 2026-09-19 · Durum: **Hüseyin onaylamadı**, dört açık soru aşağıda
Dayanak: `2026-09-19-skor-kanit-taramasi.md`

Spec §8'in formülü (`skor = 2,5 + w1·f(ciro) + w2·g(karşı taraf) + w3·h(süre)`)
kanıt taramasından sonra bu hâle geldi.

---

## 1. Büyüklük skoru

```
S = clamp(5 · f(r) · K, 0, 5)

r    = net_tutar_tl / TTM_hasılat
f(r) = clamp((log10(r) + 2) / 2, 0, 1)      # %1 taban, %100 tavan
```

**Neden logaritmik.** Materyallik çarpımsaldır: %1 → %2 ile %10 → %20 aynı şeyi
söyler. Doğrusal ölçek aralığın tamamını dev sözleşmelere harcar ve asıl ayrımın
olduğu %1–%20 bandını ezer.

| ciro oranı | %1 | %2,3 | %5 | %20 | %50 | ≥%100 |
|---|---|---|---|---|---|---|
| f(r) | 0,00 | 0,18 | 0,35 | 0,65 | 0,85 | 1,00 |
| skor (K=1) | 0,00 | 0,91 | 1,75 | 3,25 | 4,25 | 5,00 |

**Net tutar** yalnızca `ilave_siparis + fiyat_farki + tek_seferlik`.
`toplam_sozlesme` **girmez** (spec §8; ORGE'de karıştırılsa oran ~12 kat şişer).

## 2. K — güvenilirlik çarpanı

Kanıt taramasındaki 2×2 tablodan türetildi:

| karşı taraf | tip | K | 3 günlük CAR | n |
|---|---|---|---|---|
| açık | ilk açıklama | 1,00 | +%1,23 | 327 |
| açık | güncelleme | 0,85 | +%0,68 | 55 |
| gizli | ilk açıklama | 0,70 | +%0,02 | 213 |
| gizli | güncelleme | 0,50 | −%5,18 | 6 |

**Çarpımsal, toplamsal değil.** Karşı tarafı gizli dev bir sözleşme hâlâ
büyüktür, sadece daha az güvenilirdir. Toplamsal olsa güvenilirlik büyüklüğü
ezerdi (ya da tersi).

## 3. Spec'ten üç sapma

1. **`2,5` taban kalktı.** Eski formülde tutarı açıklanmamış bildirim otomatik
   2,5/5 — "orta etki" — alıyordu. Veri bunların olay olmadığını söylüyor
   (612'nin 92'sinde tutar yok, tepkileri istatistiksel olarak sıfır).
   Yeni kural: **tutar yoksa ya da hasılat yoksa skor hiç gösterilmez**, yerine
   etiket. Bildirimlerin ~%15'i skorsuz kalır.
2. **`w3` (süre) düştü.** KAP yalnızca başlangıç tarihini veriyor; süre serbest
   metinde (LLM işi) ve önemli olduğuna dair kanıt yok. B sürümünde veriyle
   geri konabilir.
3. **Devre kesici skora girmiyor.** En güçlü istatistiksel sinyal o (−2,48
   puan) ama **bildirimin değil hissenin** özelliği. Skora katılsa "neden 3,2?"
   sorusunun cevabı "çünkü hisse spekülatif" olurdu — bu bildirimi anlatan bir
   skor değildir. Ayrı bayrak olarak yanında durur:
   ```
   V90 ≤ 2 ve V5 = 0    → temiz
   V90 ≤ 6 veya V5 = 1  → hareketli
   V90 > 6 veya V5 ≥ 2  → tedbirli
   ```

## 4. Tepki paneli (skor değil)

Benzer bildirim kümesi = aynı (karşı taraf × tip) hücresi; n ≥ 30 ise tahta
dilimi de eşleşir. Yayınlanan: **medyan, %25–%75 aralığı, n, pozitif oranı.**
Ortalama tek başına yayınlanmaz — 20 günlük ortalamalarımız (+%2,82)
medyanlarla (+%2,13 / −%2,51) çelişiyor, yani birkaç uç gözleme ait.

---

## Uçtan uca doğrulanmış örnek — ORGE 1665567 (18.09.2026 18:58)

Finansal raporlar `data/ham/finansal/` altında (1557898 = FY2025,
1649471 = 6A2026).

```
FY2025 hasılat          3.495.512.127 TL   (yayın 17.02.2026)
+ 6A2026                2.597.519.683 TL   (yayın 13.08.2026)
− 6A2025                2.069.654.707 TL   (aynı raporun karşılaştırma sütunu)
= TTM                   4.023.377.103 TL   ← iki rapor da bildirimden önce: lookahead yok

863.000 EUR × 55,7981     48.153.760 TL    (TCMB alış, bildirim tarihli)
+ fiyat farkı             44.645.758 TL
= net tutar               92.799.518 TL    (revize toplam sözleşme hariç)

r = %2,31 → f(r) = 0,181 → K = 0,85 (karşı taraf açık, güncelleme)
SKOR = 5 × 0,181 × 0,85 = 0,77 / 5
```

Sağlaması: cironun %2,3'ü kadar ilave sipariş, üstelik güncelleme → büyük haber
değil. Skor da öyle diyor.

---

## Onay bekleyen dört soru

1. **K değerleri** (1,00 / 0,85 / 0,70 / 0,50) — 2×2 tablodan türetildi ama
   ölçeklemesi yargı. Gizli karşı taraf 0,5'e kadar düşsün mü?
2. **Çapalar**: %1 taban / %100 tavan.
3. **"Tutar yoksa skor yok"** kabul mü? (~%15 bildirim skorsuz görünür.)
4. **w3'ün düşmesi.**
