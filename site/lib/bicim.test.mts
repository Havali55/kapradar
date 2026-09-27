// Node'un yerleşik test koşucusu: `npm test`. Tip ayıklama Node 22.18'de
// bayraksız, ek bağımlılık yok.
// Vercel UTC'de çalışıyor; yerel makine İstanbul saatinde. Tarih testleri
// ikisinde de aynı sonucu vermeli.
process.env.TZ = "UTC";

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  cirosununKati,
  gunAy,
  kat,
  isaretliYuzde,
  istanbulGunu,
  tahtaGorunumu,
  uzunTl,
  yilda,
  yuzdeIyelik,
} from "./bicim.ts";

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

test("gunAy İstanbul takvimiyle: 21:00 UTC'den sonrası ertesi gün", () => {
  assert.equal(gunAy("2026-09-25T22:30:00Z"), "26 Eyl");
  assert.equal(gunAy("2026-09-25T20:30:00Z"), "25 Eyl");
  assert.equal(gunAy("2026-09-25T22:30:00Z", true), "26 Eylül");
});

test("kat: iki ondalıkta sıfıra yuvarlanan oran 0,00× diye yazılmaz", () => {
  assert.equal(kat(1.3812), "1,38×");
  assert.equal(kat(0.0071), "0,01×");
  assert.equal(kat(0.0032), "<0,01×");
});

test("yilda: bulunma eki yılın okunuşundaki son sözcüğe uyar", () => {
  assert.equal(yilda(2025), "2025'te"); // beş
  assert.equal(yilda(2026), "2026'da"); // altı
  assert.equal(yilda(2027), "2027'de"); // yedi
  assert.equal(yilda(2024), "2024'te"); // dört
  assert.equal(yilda(2029), "2029'da"); // dokuz
  assert.equal(yilda(2020), "2020'de"); // yirmi
  assert.equal(yilda(2030), "2030'da"); // otuz
  assert.equal(yilda(2040), "2040'ta"); // kırk
  assert.equal(yilda(2000), "2000'de"); // bin
});

test("uzunTl: tez cümlesinin tutarı", () => {
  assert.equal(uzunTl(375_512_345_678), "375,5 milyar TL");
  assert.equal(uzunTl(92_400_000), "92,4 milyon TL");
  assert.equal(uzunTl(45_000), "45.000 TL");
});

test("cirosununKati: bir ve üstü kat, altı yüzde", () => {
  assert.equal(cirosununKati(1.67), "1,7 katı");
  assert.equal(cirosununKati(0.123), "%12,3'ü");
});
