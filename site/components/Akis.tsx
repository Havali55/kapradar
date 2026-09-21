"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Bildirim } from "@/lib/veri";
import { gunEtiketi } from "@/lib/bicim";
import Kart from "./Kart";
import DetayPanel from "./DetayPanel";

type Siralama = "yeni" | "skor";
type Aralik = "24" | "7" | "tum";
type SkorEsigi = 0 | 2 | 3;

type Durum = {
  arama: string;
  skor: SkorEsigi;
  aralik: Aralik;
  yalnizTemiz: boolean;
  yalnizAcik: boolean;
  sirala: Siralama;
};

const BASLANGIC: Durum = {
  arama: "",
  skor: 0,
  aralik: "tum",
  yalnizTemiz: false,
  yalnizAcik: false,
  sirala: "yeni",
};

const ARALIK_SAAT: Record<Aralik, number> = {
  "24": 24,
  "7": 168,
  tum: Number.POSITIVE_INFINITY,
};

export default function Akis({ bildirimler }: { bildirimler: Bildirim[] }) {
  const [durum, setDurum] = useState<Durum>(BASLANGIC);
  const [secili, setSecili] = useState<string | null>(null);

  const guncelle = useCallback(
    (yama: Partial<Durum>) => setDurum((d) => ({ ...d, ...yama })),
    [],
  );

  // Derin bağlantı: ?b=<kap_id> ile paylaşılan bildirim açılır.
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("b");
    if (id && bildirimler.some((b) => b.kap_id === id)) setSecili(id);
  }, [bildirimler]);

  const suzulmus = useMemo(() => {
    const q = durum.arama.trim().toLocaleUpperCase("tr");
    const simdi = Date.now();
    const enFazlaSaat = ARALIK_SAAT[durum.aralik];

    const liste = bildirimler.filter((b) => {
      if (q) {
        const ticker = b.ticker.toLocaleUpperCase("tr");
        const sirket = b.sirket.toLocaleUpperCase("tr");
        if (!ticker.startsWith(q) && !sirket.includes(q)) return false;
      }
      if (Number.isFinite(enFazlaSaat)) {
        const saat = (simdi - new Date(b.yayin_zamani).getTime()) / 3600000;
        if (saat > enFazlaSaat) return false;
      }
      if (durum.skor && (b.etki_skoru === null || b.etki_skoru < durum.skor))
        return false;
      if (durum.yalnizTemiz && b.tahta !== "temiz") return false;
      if (durum.yalnizAcik && b.karsi_taraf === null) return false;
      return true;
    });

    if (durum.sirala === "skor") {
      // Skorsuzlar sona: "—" bir değer değil, eksiklik.
      return [...liste].sort((a, b) => {
        const x = a.etki_skoru ?? -1;
        const y = b.etki_skoru ?? -1;
        return y - x;
      });
    }
    return liste;
  }, [bildirimler, durum]);

  // Panelde önceki/sonraki, kullanıcının GÖRDÜĞÜ sıraya göre ilerler.
  const seciliIndeks = secili
    ? suzulmus.findIndex((b) => b.kap_id === secili)
    : -1;
  const seciliBildirim = seciliIndeks >= 0 ? suzulmus[seciliIndeks] : null;

  const gezin = useCallback(
    (yon: -1 | 1) => {
      if (seciliIndeks < 0) return;
      const hedef = suzulmus[seciliIndeks + yon];
      if (hedef) setSecili(hedef.kap_id);
    },
    [seciliIndeks, suzulmus],
  );

  useEffect(() => {
    if (!seciliBildirim) return;
    const tus = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSecili(null);
      else if (e.key === "ArrowDown" || e.key === "j") {
        e.preventDefault();
        gezin(1);
      } else if (e.key === "ArrowUp" || e.key === "k") {
        e.preventDefault();
        gezin(-1);
      }
    };
    window.addEventListener("keydown", tus);
    return () => window.removeEventListener("keydown", tus);
  }, [seciliBildirim, gezin]);

  const cipler: { ad: string; temizle: () => void }[] = [];
  if (durum.arama)
    cipler.push({ ad: `"${durum.arama}"`, temizle: () => guncelle({ arama: "" }) });
  if (durum.skor)
    cipler.push({
      ad: `S ≥ ${durum.skor.toFixed(1)}`,
      temizle: () => guncelle({ skor: 0 }),
    });
  if (durum.aralik !== "tum")
    cipler.push({
      ad: durum.aralik === "24" ? "Son 24 saat" : "Son 7 gün",
      temizle: () => guncelle({ aralik: "tum" }),
    });
  if (durum.yalnizTemiz)
    cipler.push({
      ad: "Sadece temiz tahta",
      temizle: () => guncelle({ yalnizTemiz: false }),
    });
  if (durum.yalnizAcik)
    cipler.push({
      ad: "Karşı taraf açık",
      temizle: () => guncelle({ yalnizAcik: false }),
    });

  // Gün ayraçları: liste tarihe göre sıralıyken anlamlı, skora göre değil.
  const gunlu = durum.sirala === "yeni";
  let oncekiGun = "";

  return (
    <>
      <div className="filtre-cubugu">
        <div className="arama">
          <span className="mono" aria-hidden="true">
            ⌕
          </span>
          <input
            value={durum.arama}
            onChange={(e) => guncelle({ arama: e.target.value })}
            placeholder="ASELS, THYAO…"
            aria-label="Hisse kodu veya şirket adı ara"
          />
        </div>

        <div className="segment">
          <span className="segment-et mono">SKOR</span>
          {([0, 2, 3] as SkorEsigi[]).map((e) => (
            <button
              key={e}
              type="button"
              aria-pressed={durum.skor === e}
              onClick={() => guncelle({ skor: e })}
            >
              {e === 0 ? "Tümü" : `S ≥ ${e.toFixed(1)}`}
            </button>
          ))}
        </div>

        <div className="segment">
          <span className="segment-et mono">TARİH</span>
          {(
            [
              ["24", "24 saat"],
              ["7", "7 gün"],
              ["tum", "Tüm arşiv"],
            ] as [Aralik, string][]
          ).map(([d, ad]) => (
            <button
              key={d}
              type="button"
              aria-pressed={durum.aralik === d}
              onClick={() => guncelle({ aralik: d })}
            >
              {ad}
            </button>
          ))}
        </div>

        <div className="segment">
          <span className="segment-et mono">SIRA</span>
          {(
            [
              ["yeni", "En yeni"],
              ["skor", "En yüksek S"],
            ] as [Siralama, string][]
          ).map(([d, ad]) => (
            <button
              key={d}
              type="button"
              aria-pressed={durum.sirala === d}
              onClick={() => guncelle({ sirala: d })}
            >
              {ad}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="anahtar"
          aria-pressed={durum.yalnizTemiz}
          onClick={() => guncelle({ yalnizTemiz: !durum.yalnizTemiz })}
        >
          Sadece temiz tahta
        </button>
        <button
          type="button"
          className="anahtar"
          aria-pressed={durum.yalnizAcik}
          onClick={() => guncelle({ yalnizAcik: !durum.yalnizAcik })}
        >
          Karşı taraf açık
        </button>

        <div className="filtre-bos" />
        <span className="sonuc-say mono">
          {suzulmus.length} / {bildirimler.length} bildirim
        </span>
        {cipler.length > 0 && (
          <button
            type="button"
            className="sifirla"
            onClick={() => setDurum(BASLANGIC)}
          >
            sıfırla
          </button>
        )}
      </div>

      {cipler.length > 0 && (
        <div className="cip-satiri">
          <span className="cip-et mono">AKTİF FİLTRE</span>
          {cipler.map((c) => (
            <button
              key={c.ad}
              type="button"
              className="cip-filtre"
              onClick={c.temizle}
            >
              {c.ad} <span aria-hidden="true">×</span>
              <span className="gizli-metin"> filtresini kaldır</span>
            </button>
          ))}
          <button
            type="button"
            className="sifirla"
            onClick={() => setDurum(BASLANGIC)}
          >
            Tüm filtreleri temizle
          </button>
        </div>
      )}

      <div className="liste">
        {suzulmus.map((b) => {
          const gun = gunEtiketi(b.yayin_zamani);
          const ayracGoster = gunlu && gun !== oncekiGun;
          if (ayracGoster) oncekiGun = gun;
          return (
            <div key={b.kap_id}>
              {ayracGoster && (
                <div className="gun-ayraci">
                  <span className="mono">{gun.toLocaleUpperCase("tr")}</span>
                </div>
              )}
              <Kart bildirim={b} onAc={() => setSecili(b.kap_id)} />
            </div>
          );
        })}

        {suzulmus.length === 0 && (
          <div className="bos">
            <div className="bos-bas">Filtrelere uyan bildirim yok</div>
            <div className="bos-alt">
              Tarih aralığını genişletmeyi veya tahta filtresini kaldırmayı
              deneyin.
            </div>
          </div>
        )}
      </div>

      {seciliBildirim && (
        <DetayPanel
          bildirim={seciliBildirim}
          onKapat={() => setSecili(null)}
          onOnceki={() => gezin(-1)}
          onSonraki={() => gezin(1)}
          oncekiVar={seciliIndeks > 0}
          sonrakiVar={seciliIndeks < suzulmus.length - 1}
          konum={`${seciliIndeks + 1} / ${suzulmus.length}`}
        />
      )}
    </>
  );
}
