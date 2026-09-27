"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Kabın gerçek genişliği. Sunucu ve ilk istemci çizimi `varsayilan` ile
 * aynı SVG'yi üretir: hidrasyon uyuşur, JS kapalıyken de grafik görünür
 * (viewBox ölçeklenir). Ölçüm gelince grafik gerçek genişlikte yeniden
 * yerleşir; yazılar ölçeklenmez, telefonda da 11 px kalır.
 */
export function useGenislik<T extends HTMLElement>(varsayilan: number) {
  const ref = useRef<T>(null);
  const [genislik, setGenislik] = useState(varsayilan);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const gozlem = new ResizeObserver(([g]) => {
      const w = Math.round(g.contentRect.width);
      if (w > 0) setGenislik(w);
    });
    gozlem.observe(el);
    return () => gozlem.disconnect();
  }, []);
  return [ref, genislik] as const;
}
