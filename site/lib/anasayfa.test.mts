// Ana sayfanın seçimleri. `npm test`.

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  cetvelPenceresi,
  enBuyukler,
  karsiTarafMetni,
  ozetMetni,
} from "./anasayfa.ts";

const GUN = 86_400_000;
const SIMDI = Date.parse("2026-09-27T12:00:00Z");
const is = (gunOnce: number, oran: number | null, tur: string | null = null) => ({
  yayin_zamani: new Date(SIMDI - gunOnce * GUN).toISOString(),
  ciro_orani: oran,
  onceki_tur: tur,
});

test("14 günde en az 8 iş varsa pencere 14 gün", () => {
  const satirlar = [...Array.from({ length: 8 }, (_, i) => is(i + 1, 0.01)), is(20, 0.5)];
  const p = cetvelPenceresi(satirlar, SIMDI);
  assert.equal(p.gun, 14);
  assert.equal(p.isler.length, 8);
});

test("14 günde 8'den az iş varsa pencere 30 güne uzar", () => {
  const satirlar = [
    ...Array.from({ length: 7 }, (_, i) => is(i + 1, 0.01)),
    is(20, 0.5),
    is(40, 0.3),
  ];
  const p = cetvelPenceresi(satirlar, SIMDI);
  assert.equal(p.gun, 30);
  assert.equal(p.isler.length, 8);
});

test("skorsuz ve önceden duyurulan iş sayılmaz; güncelleme sayılır", () => {
  const satirlar = [is(1, null), is(2, 0.2, "ayni_is"), is(3, 0.2, "guncelleme")];
  assert.deepEqual(cetvelPenceresi(satirlar, SIMDI).isler, [satirlar[2]]);
});

test("en büyükler ciro oranına göre, eşitlikte yeni olan önce", () => {
  const a = is(1, 0.1);
  const b = is(2, 0.3);
  const c = is(3, 0.1);
  const d = is(4, 0.05);
  assert.deepEqual(enBuyukler([d, c, b, a]), [b, a, c]);
});

test("özet: hap özetin ilk maddesi, yoksa iş tanımı", () => {
  assert.equal(ozetMetni({ hap_ozet: ["Birinci", "İkinci"], is_tanimi: "Tanım" }), "Birinci");
  assert.equal(ozetMetni({ hap_ozet: null, is_tanimi: "Tanım" }), "Tanım");
  assert.equal(ozetMetni({ hap_ozet: [], is_tanimi: null }), "Özet yok");
});

test("karşı taraf: sınıflandırıcı adı gizli dediyse gösterilmez", () => {
  assert.equal(karsiTarafMetni({ karsi_taraf: "SSB", karsi_taraf_acik: true }), "SSB");
  assert.equal(
    karsiTarafMetni({ karsi_taraf: "Uluslararası Müşteri", karsi_taraf_acik: false }),
    null,
  );
  // Sınıflandırılmamış eski satır: alan doluysa açık sayılır.
  assert.equal(karsiTarafMetni({ karsi_taraf: "ASFAT", karsi_taraf_acik: null }), "ASFAT");
  assert.equal(karsiTarafMetni({ karsi_taraf: null }), null);
});
