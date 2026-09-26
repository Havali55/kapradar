// Node'un yerleşik test koşucusu: `npm test`. Tip ayıklama Node 22.18'de
// bayraksız, ek bağımlılık yok.
import assert from "node:assert/strict";
import { test } from "node:test";

import { isaretliYuzde, yuzdeIyelik } from "./bicim.ts";

test("iyelik eki son okunan sözcüğe uyar: birler basamağı", () => {
  assert.equal(yuzdeIyelik(0.055), "%5,5'i");
  assert.equal(yuzdeIyelik(0.056), "%5,6'sı");
  assert.equal(yuzdeIyelik(0.023), "%2,3'ü");
});

test("tam sayıda onlar basamağı okunur: kırk altı → 'sı, kırk → 'ı", () => {
  assert.equal(yuzdeIyelik(0.46, 0), "%46'sı");
  assert.equal(yuzdeIyelik(0.4, 0), "%40'ı");
  assert.equal(yuzdeIyelik(0.3, 0), "%30'u");
  assert.equal(yuzdeIyelik(0.2, 0), "%20'si");
  assert.equal(yuzdeIyelik(1, 0), "%100'ü");
});

test("iki ondalıkta virgülden sonrası sayı olarak okunur", () => {
  // beş virgül kırk altı → 'sı; otuz virgül elli dört → 'ü
  assert.equal(yuzdeIyelik(0.0546, 2), "%5,46'sı");
  assert.equal(yuzdeIyelik(0.3054, 2), "%30,54'ü");
  assert.equal(yuzdeIyelik(0.0510, 2), "%5,10'u");
});

test("sıfır ondalık kısmı 'sıfır' okunur", () => {
  assert.equal(yuzdeIyelik(0.05, 1), "%5,0'ı");
});

test("negatif yüzde işareti yüzde işaretinin önünde, eksi karakteriyle", () => {
  assert.equal(isaretliYuzde(-0.0448), "−%4,48");
  assert.equal(isaretliYuzde(0.03), "+%3,00");
  assert.equal(isaretliYuzde(0), "%0,00");
});
