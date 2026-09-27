// Başlıktaki hisse aramasının eşleştirmesi. `npm test`.

import assert from "node:assert/strict";
import { test } from "node:test";

import { ARAMA_SINIRI, hisseEsle, type HisseSecenek } from "./arama.ts";

const LISTE: HisseSecenek[] = [
  { t: "SASA", s: "SASA POLYESTER SANAYİ A.Ş.", n: 3 },
  { t: "ASELS", s: "ASELSAN ELEKTRONİK SANAYİ VE TİCARET A.Ş.", n: 44 },
  { t: "SDTTR", s: "SDT UZAY VE SAVUNMA TEKNOLOJİLERİ A.Ş.", n: 5 },
];

test("ticker öneki, unvanda geçenlerden önce gelir; bildirim sayısı ikinci", () => {
  // SASA önekle eşleşiyor (3 bildirim); ASELS ve SDTTR yalnız unvanla.
  assert.deepEqual(
    hisseEsle(LISTE, "sa").map((h) => h.t),
    ["SASA", "ASELS", "SDTTR"],
  );
});

test("sorgu Türkçe kurallarla büyütülür: i → İ", () => {
  // "ELEKTRONIK" (noktasız I) KAP'ın "ELEKTRONİK" unvanını bulamazdı.
  assert.deepEqual(hisseEsle(LISTE, "elektronik").map((h) => h.t), ["ASELS"]);
});

test("boş ya da yalnız boşluk sorgu sonuç vermez", () => {
  assert.deepEqual(hisseEsle(LISTE, ""), []);
  assert.deepEqual(hisseEsle(LISTE, "   "), []);
});

test("en çok ARAMA_SINIRI sonuç", () => {
  const cok = Array.from({ length: 10 }, (_, i) => ({ t: `AB${i}`, s: "X", n: i }));
  const sonuc = hisseEsle(cok, "ab");
  assert.equal(sonuc.length, ARAMA_SINIRI);
  assert.equal(sonuc[0].t, "AB9");
});
