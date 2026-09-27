// Grafik geometrisi: arı kovanı ve çakışmasız etiket. `npm test`.

import assert from "node:assert/strict";
import { test } from "node:test";

import { etiketYerlestir, kovanYerlesimi } from "./cetvel.ts";

test("aynı konumdaki noktalar 0, −adım, +adım diye dizilir", () => {
  // yarıçap 5, boşluk 2 → adım 12
  assert.deepEqual(kovanYerlesimi([100, 100, 100], 5, 2), [0, -12, 12]);
});

test("uzak noktalar eksende kalır", () => {
  assert.deepEqual(kovanYerlesimi([0, 50, 100], 5, 2), [0, 0, 0]);
});

test("dönen dizi girdi sırasında; küçük konum önce yerleşir", () => {
  const k = kovanYerlesimi([101, 100], 5, 2);
  assert.equal(k[1], 0);
  assert.equal(k[0], -12);
});

test("sınır aşılırsa nokta düşmez, sınır içinde kalır", () => {
  const k = kovanYerlesimi([0, 0, 0, 0, 0], 5, 2, 12);
  assert.equal(k.length, 5);
  assert.ok(k.every((d) => Math.abs(d) <= 12));
});

const ALAN = { w: 400, h: 200 };

test("yalnız nokta: etiket üstte, noktaya değmeden", () => {
  const m = etiketYerlestir([{ x: 200, y: 100, r: 8 }], [{ i: 0, genislik: 40 }], ALAN);
  assert.deepEqual(m.get(0), { x: 200, y: 88 });
});

test("yan yana iki nokta: ikinci etiket alta iner", () => {
  const n = [
    { x: 200, y: 100, r: 8 },
    { x: 220, y: 100, r: 8 },
  ];
  const m = etiketYerlestir(n, [{ i: 0, genislik: 40 }, { i: 1, genislik: 40 }], ALAN);
  assert.equal(m.get(0)?.y, 88);
  assert.equal(m.get(1)?.y, 118);
});

test("kenardaki etiket alanın içine kayar", () => {
  const m = etiketYerlestir([{ x: 395, y: 100, r: 8 }], [{ i: 0, genislik: 40 }], ALAN);
  assert.equal(m.get(0)?.x, 380);
});

test("dört yanı dolu nokta etiketsiz kalır", () => {
  const n = [
    { x: 200, y: 100, r: 8 },
    ...[-1, 1, -2, 2].map((k) => ({ x: 200, y: 100 + k * 16, r: 8 })),
  ];
  const m = etiketYerlestir(n, [{ i: 0, genislik: 40 }], ALAN);
  assert.equal(m.has(0), false);
});

test("alanın dışına taşan aday seçilmez", () => {
  const m = etiketYerlestir([{ x: 200, y: 10, r: 8 }], [{ i: 0, genislik: 40 }], ALAN);
  assert.equal(m.get(0)?.y, 28);
});
