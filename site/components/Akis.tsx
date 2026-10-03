"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Bildirim } from "@/lib/veri";
import { gunEtiketi } from "@/lib/bicim";
import { MEGA_ORAN, ONEMLI_ORAN } from "@/lib/skor";
import Kart from "./Kart";
import DetayPanel from "./DetayPanel";

type Siralama = "yeni" | "buyuk";
type Aralik = "24" | "7" | "tum";
// Filtre kartın diliyle aynı: kademe adları, S eşiği değil. Eşikler
// kademelerin kendisi ve kart gibi CİRO ORANINA bakıyor — S'ye bakan bir
// filtre, K çarpanı yüzünden kartında "Mega iş" yazan bildirimi saklardı.
type Buyukluk = "tum" | "onemli" | "mega";
const BUYUKLUK_ESIGI: Record<Buyukluk, number> = {
  tum: 0,
  onemli: ONEMLI_ORAN,
  mega: MEGA_ORAN,
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
  yalnizAcik: boolean;
  sirala: Siralama;
};

const BASLANGIC: Durum = {
  arama: "",
  buyukluk: "tum",
  skorsuzlar: false,
  aralik: "tum",
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

  // Gün başlığındaki "Bugün" / "Dün" saate bağlı; sayfa sunucuda önceden
  // üretiliyor, tarayıcı başka bir anda çalışıyor. İlk çizim mutlak
  // tarihle, göreli ad yalnız tarayıcıda, açıldıktan sonra.
  const [simdi, setSimdi] = useState<Date | null>(null);
  useEffect(() => setSimdi(new Date()), []);
  const enYeni = useMemo(
    () => bildirimler.reduce((m, b) => (b.yayin_zamani > m ? b.yayin_zamani : m), ""),
    [bildirimler],
  );
  const gunAdi = (iso: string) => gunEtiketi(iso, simdi, enYeni || undefined);

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
      if (b.ciro_orani === null) {
        if (!durum.skorsuzlar || durum.buyukluk !== "tum") return false;
      } else if (b.ciro_orani < BUYUKLUK_ESIGI[durum.buyukluk]) return false;
      // Aynı iş daha önce duyuruldu: büyüklük filtresinde ikinci kez çıkmasın.
      if (b.oncedenDuyuruldu && durum.buyukluk !== "tum") return false;
      if (durum.yalnizAcik && !b.karsiTarafAcik) return false;
      return true;
    });

    if (durum.sirala === "buyuk") {
      // Skorsuzlar sona: "—" bir değer değil, eksiklik.
      // Önceden duyurulan iş skorluların arkasına: sıralamada iki kez yer almasın.
      const anahtar = (b: Bildirim) =>
        b.oncedenDuyuruldu ? -0.5 : (b.ciro_orani ?? -1);
      return [...liste].sort((a, b) => anahtar(b) - anahtar(a));
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
    // Yakalama aşaması: başlıktaki hisse araması da "/" dinliyor. Akış
    // önce çalışıp olayı işaretliyor (preventDefault), başlık da
    // `defaultPrevented` görünce geri çekiliyor; bu sayfada "/" akışın
    // kendi süzgecine gider.
    window.addEventListener("keydown", tus, true);
    return () => window.removeEventListener("keydown", tus, true);
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
      ad: "Büyüklüğü bilinmeyenler görünür",
      temizle: () => guncelle({ skorsuzlar: false }),
    });
  if (durum.aralik !== "tum")
    cipler.push({
      ad: durum.aralik === "24" ? "Son 24 saat" : "Son 7 gün",
      temizle: () => guncelle({ aralik: "tum" }),
    });
  if (durum.yalnizAcik)
    cipler.push({
      ad: "Karşı tarafı belli",
      temizle: () => guncelle({ yalnizAcik: false }),
    });

  const skorsuzSayisi = bildirimler.filter((b) => b.ciro_orani === null).length;

  // Gün başlıkları: liste tarihe göre sıralıyken anlamlı, büyüklüğe göre
  // değil. Başlık o günün kaç bildirimi olduğunu da söylüyor.
  const gunlu = durum.sirala === "yeni";
  const gunSayisi = new Map<string, number>();
  if (gunlu) {
    for (const b of suzulmus) {
      const g = gunAdi(b.yayin_zamani);
      gunSayisi.set(g, (gunSayisi.get(g) ?? 0) + 1);
    }
  }
  let oncekiGun = "";

  const hap = <T extends string>(
    secenekler: [T, string][],
    secili: T,
    sec: (v: T) => void,
  ) =>
    secenekler.map(([v, ad]) => (
      <button key={v} type="button" aria-pressed={secili === v} onClick={() => sec(v)}>
        {ad}
      </button>
    ));

  return (
    <>
      <div className="akis-suzgec">
        <div className="akis-suzgec-ust">
          <div className="akis-arama">
            <svg className="buyutec" viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" />
              <path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
            <input
              ref={aramaRef}
              type="search"
              autoComplete="off"
              spellCheck={false}
              value={durum.arama}
              onChange={(e) => guncelle({ arama: e.target.value })}
              placeholder="Süz: ticker ya da unvan"
              aria-label="Bildirimleri hisse kodu ya da şirket adıyla süz"
            />
            <kbd aria-hidden="true">/</kbd>
          </div>
          <span className="akis-sayi" aria-live="polite">
            <b>{suzulmus.length.toLocaleString("tr-TR")}</b> /{" "}
            {bildirimler.length.toLocaleString("tr-TR")} bildirim
          </span>
          {cipler.length > 0 && (
            <button type="button" className="sifirla" onClick={() => setDurum(BASLANGIC)}>
              Süzgeçleri temizle
            </button>
          )}
          <p className="tus-yardim" aria-hidden="true">
            <kbd className="tus">J</kbd>
            <kbd className="tus">K</kbd> gez · <kbd className="tus">↵</kbd> aç ·{" "}
            <kbd className="tus">Esc</kbd> kapat
          </p>
        </div>

        <div className="akis-suzgec-alt">
          <div className="suzgec-grup" role="group" aria-label="Büyüklük">
            <span className="suzgec-et">Büyüklük</span>
            <div className="suzgec">
              {hap(
                (["tum", "onemli", "mega"] as Buyukluk[]).map((e) => [e, BUYUKLUK_ADI[e]]),
                durum.buyukluk,
                (v) => guncelle({ buyukluk: v }),
              )}
            </div>
          </div>
          <div className="suzgec-grup" role="group" aria-label="Tarih">
            <span className="suzgec-et">Tarih</span>
            <div className="suzgec">
              {hap<Aralik>(
                [
                  ["24", "24 saat"],
                  ["7", "7 gün"],
                  ["tum", "Tüm arşiv"],
                ],
                durum.aralik,
                (v) => guncelle({ aralik: v }),
              )}
            </div>
          </div>
          <div className="suzgec-grup" role="group" aria-label="Sıra">
            <span className="suzgec-et">Sıra</span>
            <div className="suzgec">
              {hap<Siralama>(
                [
                  ["yeni", "En yeni"],
                  ["buyuk", "En büyük iş"],
                ],
                durum.sirala,
                (v) => guncelle({ sirala: v }),
              )}
            </div>
          </div>
          <div className="suzgec-grup" role="group" aria-label="Yalnız şunlar">
            <span className="suzgec-et">Göster</span>
            <div className="suzgec">
              <button
                type="button"
                aria-pressed={durum.yalnizAcik}
                onClick={() => guncelle({ yalnizAcik: !durum.yalnizAcik })}
                title="Şirketin iş yaptığı tarafın adını açıkladığı bildirimler"
              >
                Karşı tarafı belli
              </button>
              <button
                type="button"
                aria-pressed={durum.skorsuzlar}
                onClick={() => guncelle({ skorsuzlar: !durum.skorsuzlar })}
                title="Tutarı açıklanmamış ya da cirosu bilinmeyen bildirimler; varsayılan gizli"
              >
                Büyüklüğü bilinmeyenler ({skorsuzSayisi})
              </button>
            </div>
          </div>
        </div>
      </div>

      {cipler.length > 0 && (
        <div className="cip-satiri">
          <span className="cip-et">Süzgeç</span>
          {cipler.map((c) => (
            <button key={c.ad} type="button" className="cip-filtre" onClick={c.temizle}>
              {c.ad} <span aria-hidden="true">×</span>
              <span className="gizli-metin"> süzgecini kaldır</span>
            </button>
          ))}
        </div>
      )}

      <div className="akis-liste">
        {suzulmus.map((b, i) => {
          const gun = gunAdi(b.yayin_zamani);
          const ayracGoster = gunlu && gun !== oncekiGun;
          if (ayracGoster) oncekiGun = gun;
          return (
            <div key={b.kap_id}>
              {ayracGoster && (
                <h2 className="as-gun">
                  <b>{gun}</b>
                  <span>{gunSayisi.get(gun)} bildirim</span>
                </h2>
              )}
              <Kart
                bildirim={b}
                imlec={i === imlec}
                gunlu={gunlu}
                onAc={() => setSecili(b.kap_id)}
              />
            </div>
          );
        })}

        {suzulmus.length === 0 && (
          <div className="bos">
            <div className="bos-bas">Süzgeçlere uyan bildirim yok</div>
            <div className="bos-alt">
              Tarih aralığını genişletmeyi ya da bir süzgeci kaldırmayı deneyin.
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
