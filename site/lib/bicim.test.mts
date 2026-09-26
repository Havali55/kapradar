// Node'un yerleşik test koşucusu: `npm test`. Tip ayıklama Node 22.18'de
// bayraksız, ek bağımlılık yok.
// Vercel UTC'de çalışıyor; yerel makine İstanbul saatinde. Tarih testleri
// ikisinde de aynı sonucu vermeli.
process.env.TZ = "UTC";

import assert from "node:assert/strict";
import { test } from "node:test";

import { isaretliYuzde, istanbulGunu, tahtaGorunumu, yuzdeIyelik } from "./bicim.ts";

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

test("tahta notuna aynı günün piyasa taban oranı eklenir", () => {
  const cok = tahtaGorunumu("tedbirli", 20, 3, 0, 0.44);
  assert.ok(cok?.not.endsWith("Aynı gün piyasadaki hisselerin %44'ü de bu durumdaydı."));
  const sakin = tahtaGorunumu("temiz", 1, 0, 0, 0.3);
  assert.ok(sakin?.not.endsWith("Aynı gün piyasadaki hisselerin %30'u çok oynaktı."));
  const yok = tahtaGorunumu("temiz", 1, 0, 0);
  assert.ok(!yok?.not.includes("piyasadaki"));
});

test("İstanbul günü UTC gününden farklı olabilir", () => {
  // 21:30 UTC = ertesi gün 00:30 İstanbul
  assert.equal(istanbulGunu("2025-12-08T21:30:00+00:00"), "09.12.2025");
});
