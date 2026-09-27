// Söz ve gerçek — Python'daki tests/test_soz_gercek.py ile aynı fikstür.
// `npm test`.
process.env.TZ = "UTC";

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  anlamliMi,
  buyumeDonemiSec,
  donemAdi,
  okumaTuru,
  oncekiCeyrek,
  ozetle,
  sozSatirlariKur,
  spearman,
  type BuyumeGirdi,
  type DuyuruGirdi,
  type SozSatiri,
} from "./soz.ts";

const FIKSTUR = JSON.parse(
  readFileSync(new URL("../../tests/fixtures/soz_gercek.json", import.meta.url), "utf8"),
);
const B = FIKSTUR.beklenen;
const satirlar = (): SozSatiri[] => FIKSTUR.satirlar.map((s: SozSatiri) => ({ ...s }));
const yakin = (a: number[], b: number[]) => {
  assert.equal(a.length, b.length);
  a.forEach((x, i) => assert.ok(Math.abs(x - b[i]) < 1e-12, `${x} ≈ ${b[i]}`));
};

test("üç eşit grup, yoğunluğa göre; artan son gruba", () => {
  const o = ozetle(satirlar())!;
  assert.deepEqual(
    o.gruplar.map((g) => g.satirlar.map((s) => s.ticker)),
    B.grup_tickerlari,
  );
});

test("grup medyanları", () => {
  const o = ozetle(satirlar())!;
  yakin(o.gruplar.map((g) => g.medyanBuyume), B.medyan_buyume);
  yakin(o.gruplar.map((g) => g.medyanYogunluk), B.medyan_yogunluk);
});

test("Spearman, t ve üst grup", () => {
  const o = ozetle(satirlar())!;
  assert.equal(o.n, B.n);
  yakin([o.rho, o.t], [B.rho, B.t]);
  assert.equal(o.ustGrupOnde, B.ust_grup_onde);
});

test("eşit değerler ortalama sıra alır", () => {
  const e = FIKSTUR.spearman_esitlik;
  yakin([spearman(e.x, e.y)], [e.rho]);
});

test("girdi sırası sonucu değiştirmez", () => {
  assert.deepEqual(ozetle([...satirlar()].reverse()), ozetle(satirlar()));
});

test("üst grup farkı eşiği geçmezse önde denmez", () => {
  const ornek = satirlar().map((s) =>
    ["EEE", "FFF", "GGG"].includes(s.ticker) ? { ...s, buyume: 0.16 } : s,
  );
  assert.equal(ozetle(ornek)!.ustGrupOnde, false);
});

test("üç satırdan azla özet kurulmaz", () => {
  assert.equal(ozetle(satirlar().slice(0, 2)), null);
});

test("dönem seçimi raporlama sezonunu bekler", () => {
  const kapsam = new Map<string, number>(Object.entries(FIKSTUR.kapsam));
  assert.equal(buyumeDonemiSec(kapsam), FIKSTUR.beklenen_donem);
});

test("dönem seçimi çeyrek sonu olmayanı saymaz", () => {
  const kapsam = new Map([["2026-07-31", 50], ["2026-06-30", 40]]);
  assert.equal(buyumeDonemiSec(kapsam), "2026-06-30");
});

test("önceki çeyrek yıl sınırını geçer", () => {
  assert.equal(oncekiCeyrek("2026-03-31"), "2025-12-31");
  assert.equal(oncekiCeyrek("2026-09-30"), "2026-06-30");
});

test("anlamlılık: iki yönlü %5, ara serbestlik derecesinde tutucu", () => {
  assert.equal(anlamliMi(1.91, 64), false); // sd 62 → 60 satırı, 2,000
  assert.equal(anlamliMi(2.01, 64), true);
  assert.equal(anlamliMi(-2.01, 64), true);
  assert.equal(anlamliMi(2.1, 12), false); // sd 10 → 2,228
  assert.equal(anlamliMi(99, 2), false); // sd 0
});

test("okuma türü: önde ve anlamlılığa göre", () => {
  const o = ozetle(satirlar())!; // ρ 0,786, n 7, t 2,84 > 2,571 (sd 5)
  assert.equal(okumaTuru(o), "onde-anlamli");
  assert.equal(okumaTuru({ ...o, t: 1.5 }), "onde");
  assert.equal(okumaTuru({ ...o, ustGrupOnde: false }), "ayrismiyor");
});

test("dönem adı", () => {
  assert.equal(donemAdi("2026-06-30"), "2026 ilk yarı");
  assert.equal(donemAdi("2026-03-31"), "2026 ilk çeyrek");
  assert.equal(donemAdi("2026-09-30"), "2026 ilk dokuz ay");
  assert.equal(donemAdi("2025-12-31"), "2025 yılı");
});

// --------------------------------------------- satır kurma (analiz_soz_gercek D)

const duyuru = (
  ticker: string,
  zaman: string,
  tl: number,
  oran: number | null = 0.1,
  tur: string | null = null,
): DuyuruGirdi => ({
  ticker,
  yayin_zamani: zaman,
  net_tutar_tl: tl,
  ciro_orani: oran,
  onceki_tur: tur,
});

const buyume = (
  ticker: string,
  donem_sonu: string,
  ay_sayisi: number,
  hasilat: number,
  g: number | null,
  reel = true,
  para_birimi = "TL",
): BuyumeGirdi => ({ ticker, donem_sonu, ay_sayisi, hasilat, para_birimi, buyume: g, reel });

const DUYURULAR: DuyuruGirdi[] = [
  duyuru("AAA", "2025-03-01T08:00:00Z", 50),
  duyuru("AAA", "2025-06-01T08:00:00Z", 30),
  duyuru("AAA", "2025-07-01T08:00:00Z", 100, 0.2, "ayni_is"), // önceden sayıldı
  duyuru("AAA", "2025-08-01T08:00:00Z", 70, null), // skorsuz
  duyuru("AAA", "2024-06-01T08:00:00Z", 999), // söz yılı dışı
  duyuru("BBB", "2025-05-01T08:00:00Z", 10), // nominal
  duyuru("CCC", "2025-05-01T08:00:00Z", 10), // FY cirosu USD
  // İstanbul'da 1 Ocak 2025 00:30 → 2025 sayılır.
  duyuru("DDD", "2024-12-31T21:30:00Z", 20),
  // İstanbul'da 1 Ocak 2026 00:30 → 2026, sayılmaz.
  duyuru("DDD", "2025-12-31T21:30:00Z", 500),
];

const BUYUMELER: BuyumeGirdi[] = [
  buyume("AAA", "2025-12-31", 12, 400, 0.05),
  buyume("AAA", "2026-06-30", 3, 110, 0.5), // çeyreklik; en uzun kümülatif değil
  buyume("AAA", "2026-06-30", 6, 220, 0.1),
  buyume("BBB", "2025-12-31", 12, 100, 0.3, false),
  buyume("BBB", "2026-06-30", 6, 60, 0.3, false),
  buyume("CCC", "2025-12-31", 12, 100, 0.1, true, "USD"),
  buyume("CCC", "2026-06-30", 6, 60, 0.2),
  buyume("DDD", "2025-12-31", 12, 200, 0.02),
  buyume("DDD", "2026-06-30", 6, 110, -0.1),
];

test("satır kurma: dönem, söz yılı ve sayılan bildirimler", () => {
  const v = sozSatirlariKur(DUYURULAR, BUYUMELER)!;
  assert.equal(v.donem, "2026-06-30");
  assert.equal(v.sozYili, 2025);
  const aaa = v.satirlar.find((s) => s.ticker === "AAA")!;
  assert.equal(aaa.adet, 2);
  assert.equal(aaa.tl, 80);
  assert.equal(aaa.yogunluk, 80 / 400);
  assert.equal(aaa.buyume, 0.1);
});

test("satır kurma: yıl sınırı İstanbul saatiyle", () => {
  const v = sozSatirlariKur(DUYURULAR, BUYUMELER)!;
  const ddd = v.satirlar.find((s) => s.ticker === "DDD")!;
  assert.equal(ddd.tl, 20);
  assert.equal(ddd.adet, 1);
});

test("satır kurma: nominal ve TL dışı FY dışarıda, nominal ayrıca sayılır", () => {
  const v = sozSatirlariKur(DUYURULAR, BUYUMELER)!;
  assert.deepEqual(v.satirlar.map((s) => s.ticker).sort(), ["AAA", "DDD"]);
  assert.deepEqual(v.nominal, ["BBB"]);
});

test("satır kurma: büyüme dönemi yoksa null", () => {
  assert.equal(sozSatirlariKur(DUYURULAR, []), null);
});
