// Hisse hikâyesi ve dizin. `npm test`.
process.env.TZ = "UTC";

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  GUN_MS,
  aylaraBol,
  birimSec,
  ciroAn,
  dizinSatirlari,
  dizinSirala,
  gosterilenKalemler,
  gunlukSeri,
  guzelAdim,
  isleriSuz,
  karsiGorunen,
  kiminle,
  kisaAd,
  seriIliskisi,
  sonOnIkiAy,
  tabloSatirlari,
} from "./hikaye.ts";

const SIMDI = Date.parse("2026-09-27T12:00:00Z");
const once = (gun: number) => new Date(SIMDI - gun * GUN_MS).toISOString();
const basamak = (gun: number, hasilat: number | null, pb: string | null = "TL") => ({
  gecerlilik_basi: once(gun),
  hasilat,
  para_birimi: pb,
});

test("son 12 ay: 365 gün öncesi dahil değil, bugün dahil", () => {
  const isler = [{ yayin_zamani: once(0) }, { yayin_zamani: once(364) }, { yayin_zamani: once(365) }];
  assert.equal(sonOnIkiAy(isler, SIMDI).length, 2);
});

test("ciroAn: o ana kadarki son basamak; boşluk ve TL dışı null", () => {
  const b = [basamak(300, 100), basamak(100, 200), basamak(50, null), basamak(10, 300, "USD")];
  assert.equal(ciroAn(b, SIMDI - 200 * GUN_MS), 100);
  assert.equal(ciroAn(b, SIMDI - 60 * GUN_MS), 200);
  assert.equal(ciroAn(b, SIMDI - 20 * GUN_MS), null);
  assert.equal(ciroAn(b, SIMDI), null);
  assert.equal(ciroAn(b, SIMDI - 400 * GUN_MS), null);
});

test("günlük seri: son nokta bugün, kayan 12 ay toplamı", () => {
  const isler = [
    { yayin_zamani: once(10), net_tutar_tl: 5 },
    { yayin_zamani: once(200), net_tutar_tl: 7 },
    { yayin_zamani: once(500), net_tutar_tl: 100 },
  ];
  const s = gunlukSeri(isler, [basamak(400, 50)], SIMDI);
  assert.equal(s.length, 366);
  assert.equal(s.at(-1)!.t, SIMDI);
  assert.equal(s.at(-1)!.duyurulan, 12);
  // 365 gün önce: 500 gün önceki iş hâlâ o günün 12 ayının içinde
  assert.equal(s[0].duyurulan, 100);
  assert.equal(s[0].ciro, 50);
});

test("seri ilişkisi: her gün ölçülüyorsa üstte/altta, yoksa karışık", () => {
  const n = (d: number, c: number | null) => ({ t: 0, duyurulan: d, ciro: c });
  assert.equal(seriIliskisi([n(5, 3), n(6, 3)]), "ustte");
  assert.equal(seriIliskisi([n(1, 3), n(2, 3)]), "altta");
  assert.equal(seriIliskisi([n(5, 3), n(1, 3)]), "karisik");
  assert.equal(seriIliskisi([n(5, 3), n(6, null)]), "karisik");
  assert.equal(seriIliskisi([n(5, null)]), "ciro-yok");
});

test("güzel adım: 1, 2, 5 × 10^k", () => {
  assert.equal(guzelAdim(375.5e9), 1e11);
  assert.equal(guzelAdim(8e6), 2e6);
  assert.equal(guzelAdim(0), 1);
});

test("birim: milyar ya da milyon", () => {
  assert.equal(birimSec(4e11).ad, "milyar TL");
  assert.equal(birimSec(8e8).kisa, "Mn");
});

test("kısa ad: bilinen kurum, parantez kısaltması, ilk sözcük", () => {
  assert.equal(kisaAd("Türkiye Cumhuriyeti Cumhurbaşkanlığı Savunma Sanayii Başkanlığı"), "SSB");
  assert.equal(kisaAd("Askeri Fabrika ve Tersane İşletme A.Ş. (ASFAT)"), "ASFAT");
  assert.equal(kisaAd("TUSAŞ - Türk Havacılık ve Uzay Sanayii A.Ş."), "TUSAŞ");
  assert.equal(kisaAd("ROKETSAN ROKET SAN. VE TİC. A.Ş."), "ROKETSAN");
  assert.equal(kisaAd(null), null);
});

test("görünen karşı taraf: devlet ön eki kısalır", () => {
  assert.equal(
    karsiGorunen("Türkiye Cumhuriyeti Cumhurbaşkanlığı Savunma Sanayii Başkanlığı"),
    "Savunma Sanayii Başkanlığı",
  );
  assert.equal(karsiGorunen("ROKETSAN ROKET SAN. VE TİC. A.Ş."), "ROKETSAN ROKET SAN. VE TİC. A.Ş.");
});

test("kiminle: adı verilenler TL'ye göre, adsızlar tek satırda sonda", () => {
  const k = kiminle([
    { net_tutar_tl: 10, karsi: null },
    { net_tutar_tl: 5, karsi: "B" },
    { net_tutar_tl: 50, karsi: null },
    { net_tutar_tl: 20, karsi: "A" },
    { net_tutar_tl: 1, karsi: "B" },
  ]);
  assert.deepEqual(k, [
    { ad: "A", tl: 20, adet: 1 },
    { ad: "B", tl: 6, adet: 2 },
    { ad: null, tl: 60, adet: 2 },
  ]);
});

test("gösterilen kalemler toplam sözleşmeyi atlar", () => {
  assert.deepEqual(
    gosterilenKalemler([{ tip: "toplam_sozlesme" }, { tip: "ilave_siparis" }]),
    [{ tip: "ilave_siparis" }],
  );
  assert.deepEqual(gosterilenKalemler(null), []);
});

const is = (oran: number | null, tekrar = false, karsi: string | null = null) => ({
  zaman: once(1),
  oran,
  tekrar,
  karsi,
});

test("liste süzgeci: önemli ve üstü tekrarı saymaz; karşı tarafı belli", () => {
  const l = [is(0.2), is(0.2, true), is(0.01, false, "X"), is(null, false, "Y")];
  assert.equal(isleriSuz(l, "tum", 0.05).length, 4);
  assert.deepEqual(isleriSuz(l, "onemli", 0.05), [l[0]]);
  assert.deepEqual(isleriSuz(l, "acik", 0.05), [l[2], l[3]]);
});

test("aylara bölme İstanbul takvimiyle; sayı süzgecin tamamından", () => {
  const a = { zaman: "2026-09-30T21:30:00Z" }; // İstanbul'da 1 Ekim
  const b = { zaman: "2026-09-30T20:00:00Z" };
  const c = { zaman: "2026-09-01T08:00:00Z" };
  const g = aylaraBol([a, b, c], [a, b]);
  assert.deepEqual(
    g.map((x) => [x.ay, x.adet, x.isler.length]),
    [
      ["Ekim 2026", 1, 1],
      ["Eylül 2026", 2, 1],
    ],
  );
});

test("tablo satırları: son noktadan geriye her 30 günde bir", () => {
  const s = Array.from({ length: 366 }, (_, i) => i);
  const t = tabloSatirlari(s);
  assert.equal(t.length, 13);
  assert.equal(t.at(-1), 365);
  assert.equal(t[0], 5);
});

const satir = (
  ticker: string,
  gun: number,
  oran: number | null,
  tl: number | null,
  tur: string | null = null,
) => ({
  ticker,
  sirket: `${ticker} A.Ş.`,
  yayin_zamani: once(gun),
  ciro_orani: oran,
  net_tutar_tl: tl,
  onceki_tur: tur,
});
const sayilan = (s: { ciro_orani: number | null; onceki_tur: string | null }) =>
  s.ciro_orani !== null && s.onceki_tur !== "ayni_is";

test("dizin satırı: son 12 ay, kat, son bildirim, son dönem büyümesi", () => {
  const satirlar = [
    satir("AAA", 1, null, null), // en yeni: skorsuz ama son bildirim
    satir("AAA", 5, 0.1, 40),
    satir("AAA", 6, 0.1, 40, "ayni_is"),
    satir("AAA", 400, 0.1, 999),
    satir("BBB", 3, 0.2, 10),
  ];
  const seri = [
    { ticker: "AAA", ...basamak(30, 100) },
    { ticker: "BBB", ...basamak(30, null) },
  ];
  const buyumeler = [
    { ticker: "AAA", donem_sonu: "2026-06-30", ay_sayisi: 3, buyume: 0.9, reel: true },
    { ticker: "AAA", donem_sonu: "2026-06-30", ay_sayisi: 6, buyume: 0.2, reel: true },
    { ticker: "AAA", donem_sonu: "2025-12-31", ay_sayisi: 12, buyume: 0.5, reel: true },
    { ticker: "BBB", donem_sonu: "2026-06-30", ay_sayisi: 6, buyume: 0.3, reel: false },
  ];
  const [a, b] = dizinSatirlari(satirlar, seri, buyumeler, SIMDI, sayilan);
  assert.deepEqual(
    { t: a.ticker, n: a.adet12, kat: a.kat, son: a.sonIs, g: a.buyume, d: a.buyumeDonemi, nom: a.nominal },
    { t: "AAA", n: 1, kat: 0.4, son: once(1), g: 0.2, d: "2026-06-30", nom: false },
  );
  assert.equal(b.kat, null);
  assert.equal(b.buyume, null);
  assert.equal(b.nominal, true);
});

test("dizin sıralaması: boş değer her iki yönde sonda", () => {
  const r = [
    { ticker: "A", sirket: "", adet12: 1, sonIs: once(5), kat: null, buyume: 0.1 },
    { ticker: "B", sirket: "", adet12: 3, sonIs: once(1), kat: 2, buyume: null },
    { ticker: "C", sirket: "", adet12: 2, sonIs: once(3), kat: 0.5, buyume: 0.3 },
  ];
  assert.deepEqual(dizinSirala(r, "kat", true).map((x) => x.ticker), ["B", "C", "A"]);
  assert.deepEqual(dizinSirala(r, "kat", false).map((x) => x.ticker), ["C", "B", "A"]);
  assert.deepEqual(dizinSirala(r, "sonIs", true).map((x) => x.ticker), ["B", "C", "A"]);
  assert.deepEqual(dizinSirala(r, "ticker", false).map((x) => x.ticker), ["A", "B", "C"]);
});
