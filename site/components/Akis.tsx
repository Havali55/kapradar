"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Bildirim } from "@/lib/veri";
import { gunEtiketi } from "@/lib/bicim";
import { MEGA_ESIGI, ONEMLI_ESIGI } from "@/lib/skor";
import Kart from "./Kart";
import DetayPanel from "./DetayPanel";

type Siralama = "yeni" | "buyuk";
type Aralik = "24" | "7" | "tum";
// Filtre kartın diliyle aynı: kademe adları, S eşiği değil. Eşikler
// kademelerin kendisi — eskiden 2,0/3,0'dı ve "S ≥ 3" filtresi kartında
// "Önemli iş" yazan bildirimleri de getiriyordu.
type Buyukluk = "tum" | "onemli" | "mega";
const BUYUKLUK_ESIGI: Record<Buyukluk, number> = {
  tum: 0,
  onemli: ONEMLI_ESIGI,
  mega: MEGA_ESIGI,
};
const BUYUKLUK_ADI: Record<Buyukluk, string> = {
  tum: "Tümü",
  onemli: "Önemli iş ve üstü",
  mega: "Mega iş",
};

type Durum = {
  arama: string;
  buyukluk: Buyukluk;
  /** Skorsuzlar varsayılan gizli: kartta yalnız "skor yok" diyen bir kutu,
      akışta yer kaplıyordu. Saklanmıyorlar — tek tıkla açılıyorlar. */
  skorsuzlar: boolean;
  aralik: Aralik;
  yalnizTemiz: boolean;
  yalnizAcik: boolean;
  sirala: Siralama;
};

const BASLANGIC: Durum = {
  arama: "",
  buyukluk: "tum",
  skorsuzlar: false,
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
      if (b.etki_skoru === null) {
        if (!durum.skorsuzlar || durum.buyukluk !== "tum") return false;
      } else if (b.etki_skoru < BUYUKLUK_ESIGI[durum.buyukluk]) return false;
      if (durum.yalnizTemiz && b.tahta !== "temiz") return false;
      if (durum.yalnizAcik && b.karsi_taraf === null) return false;
      return true;
    });

    if (durum.sirala === "buyuk") {
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

  // Klavye: panel açıkken J/K bildirimler arasında gezer; kapalıyken
  // akışta bir imleç gezdirir, Enter açar. "/" aramaya odaklanır.
  // Yazı yazılırken (input) yalnız Esc dinlenir.
  const [imlec, setImlec] = useState(-1);
  const aramaRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setImlec(-1);
  }, [durum]);

  useEffect(() => {
    const tus = (e: KeyboardEvent) => {
      const hedef = e.target as HTMLElement | null;
      const yaziyor = hedef?.tagName === "INPUT" || hedef?.tagName === "TEXTAREA";
      if (e.key === "Escape") {
        if (yaziyor) hedef?.blur();
        else setSecili(null);
        return;
      }
      if (yaziyor || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "/") {
        e.preventDefault();
        aramaRef.current?.focus();
        return;
      }
      const ileri = e.key === "j" || e.key === "ArrowDown";
      const geri = e.key === "k" || e.key === "ArrowUp";
      if (seciliBildirim) {
        if (ileri || geri) {
          e.preventDefault();
          gezin(ileri ? 1 : -1);
        }
        return;
      }
      if (ileri || geri) {
        if (suzulmus.length === 0) return;
        e.preventDefault();
        setImlec((i) =>
          Math.max(0, Math.min(suzulmus.length - 1, i < 0 ? 0 : i + (ileri ? 1 : -1))),
        );
      } else if (e.key === "Enter" && imlec >= 0 && suzulmus[imlec]) {
        e.preventDefault();
        setSecili(suzulmus[imlec].kap_id);
      }
    };
    window.addEventListener("keydown", tus);
    return () => window.removeEventListener("keydown", tus);
  }, [seciliBildirim, gezin, suzulmus, imlec]);

  // Panelde gezinirken imleç de takip etsin: panel kapanınca kullanıcı
  // listede kaldığı yerden devam eder.
  useEffect(() => {
    if (seciliIndeks >= 0) setImlec(seciliIndeks);
  }, [seciliIndeks]);

  const cipler: { ad: string; temizle: () => void }[] = [];
  if (durum.arama)
    cipler.push({ ad: `"${durum.arama}"`, temizle: () => guncelle({ arama: "" }) });
  if (durum.buyukluk !== "tum")
    cipler.push({
      ad: BUYUKLUK_ADI[durum.buyukluk],
      temizle: () => guncelle({ buyukluk: "tum" }),
    });
  if (durum.skorsuzlar)
    cipler.push({
      ad: "Skoru olmayanlar görünür",
      temizle: () => guncelle({ skorsuzlar: false }),
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

  const skorsuzSayisi = bildirimler.filter((b) => b.etki_skoru === null).length;

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
            ref={aramaRef}
            value={durum.arama}
            onChange={(e) => guncelle({ arama: e.target.value })}
            placeholder="ASELS, THYAO…"
            aria-label="Hisse kodu veya şirket adı ara"
          />
          <kbd className="tus">/</kbd>
        </div>

        <div className="segment">
          <span className="segment-et mono">BÜYÜKLÜK</span>
          {(["tum", "onemli", "mega"] as Buyukluk[]).map((e) => (
            <button
              key={e}
              type="button"
              aria-pressed={durum.buyukluk === e}
              onClick={() => guncelle({ buyukluk: e })}
            >
              {BUYUKLUK_ADI[e]}
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
              ["buyuk", "En büyük iş"],
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
          aria-pressed={durum.skorsuzlar}
          onClick={() => guncelle({ skorsuzlar: !durum.skorsuzlar })}
          title="Tutarı açıklanmamış ya da cirosu bilinmeyen bildirimler"
        >
          Skoru olmayanlar ({skorsuzSayisi})
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

      <p className="tus-yardim">
        <span>
          <kbd className="tus">J</kbd> <kbd className="tus">K</kbd> gez
        </span>
        <span>
          <kbd className="tus">↵</kbd> aç
        </span>
        <span>
          <kbd className="tus">/</kbd> ara
        </span>
        <span>
          <kbd className="tus">Esc</kbd> kapat
        </span>
      </p>

      <div className="liste">
        {suzulmus.map((b, i) => {
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
              <Kart
                bildirim={b}
                imlec={i === imlec}
                onAc={() => setSecili(b.kap_id)}
              />
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
