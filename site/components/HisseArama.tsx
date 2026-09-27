"use client";

import { useRouter } from "next/navigation";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { hisseEsle, type HisseSecenek } from "@/lib/arama";

type Props = {
  hisseler: HisseSecenek[];
  /** Ana sayfanın büyük kutusu: daha iri, farklı yer tutucu. */
  buyuk?: boolean;
  /** "/" tuşu bu kutuya odaklansın mı? Sayfada yalnız bir kutu almalı. */
  kisayol?: boolean;
};

/**
 * Hisse arama kutusu: WAI-ARIA combobox + listbox. Seçim hisse sayfasına
 * gider. Liste derleme anında sayfaya gömülü (`hisseSecenekleriGetir`),
 * ağ isteği yok.
 */
export default function HisseArama({ hisseler, buyuk = false, kisayol = false }: Props) {
  const router = useRouter();
  const kutu = useRef<HTMLInputElement>(null);
  const listeId = useId();
  const [sorgu, setSorgu] = useState("");
  const [acik, setAcik] = useState(false);
  const [sec, setSec] = useState(0);
  const sonuc = hisseEsle(hisseler, sorgu);
  const gorunur = acik && sorgu.trim() !== "";

  // "/" her sayfada bu kutuya odaklanır. Sayfanın kendi araması varsa
  // (akış süzgeci) onun dinleyicisi yakalama aşamasında önce çalışıp
  // olayı işaretler; burada geri çekiliriz.
  useEffect(() => {
    if (!kisayol) return;
    const tus = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      const hedef = e.target as HTMLElement | null;
      if (
        hedef?.tagName === "INPUT" ||
        hedef?.tagName === "TEXTAREA" ||
        hedef?.isContentEditable
      ) {
        return;
      }
      e.preventDefault();
      kutu.current?.focus();
    };
    window.addEventListener("keydown", tus);
    return () => window.removeEventListener("keydown", tus);
  }, [kisayol]);

  const git = (ticker: string) => {
    setSorgu("");
    setAcik(false);
    kutu.current?.blur();
    router.push(`/hisse/${ticker}`);
  };

  const tus = (e: ReactKeyboardEvent<HTMLInputElement>) => {
    if ((e.key === "ArrowDown" || e.key === "ArrowUp") && sonuc.length) {
      e.preventDefault();
      setAcik(true);
      const adim = e.key === "ArrowDown" ? 1 : -1;
      setSec((s) => (s + adim + sonuc.length) % sonuc.length);
    } else if (e.key === "Enter" && gorunur && sonuc[sec]) {
      e.preventDefault();
      git(sonuc[sec].t);
    } else if (e.key === "Escape") {
      setAcik(false);
      kutu.current?.blur();
    }
  };

  return (
    <div className={buyuk ? "arama arama-buyuk" : "arama"}>
      <svg className="buyutec" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      <input
        ref={kutu}
        type="search"
        autoComplete="off"
        spellCheck={false}
        placeholder={buyuk ? "Bir hisse ya da şirket adı yazın" : "Hisse ara: ASELS, Aselsan…"}
        aria-label="Hisse ara"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={gorunur}
        aria-controls={listeId}
        aria-activedescendant={gorunur && sonuc[sec] ? `${listeId}-${sec}` : undefined}
        value={sorgu}
        onChange={(e) => {
          setSorgu(e.target.value);
          setSec(0);
          setAcik(true);
        }}
        onFocus={() => setAcik(true)}
        onBlur={() => setAcik(false)}
        onKeyDown={tus}
      />
      <kbd aria-hidden="true">{buyuk ? "Enter" : "/"}</kbd>
      {gorunur && (
        <ul className="oneriler" id={listeId} role="listbox" aria-label="Eşleşen hisseler">
          {sonuc.length > 0 ? (
            sonuc.map((h, i) => (
              <li
                key={h.t}
                id={`${listeId}-${i}`}
                role="option"
                aria-selected={i === sec}
                // mousedown + preventDefault: odak kutuda kalır, blur
                // listeyi tıklamadan önce kapatmaz.
                onMouseDown={(e) => {
                  e.preventDefault();
                  git(h.t);
                }}
                onMouseEnter={() => setSec(i)}
              >
                <span className="oneri-t mono">{h.t}</span>
                <span className="oneri-s unvan">{h.s}</span>
                <span className="oneri-n mono">{h.n} bildirim</span>
              </li>
            ))
          ) : (
            <li className="oneri-yok" role="option" aria-selected={false} aria-disabled="true">
              Bu adla bildirim yok; arşivde {hisseler.length} şirket var.
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
