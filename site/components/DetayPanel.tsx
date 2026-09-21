"use client";

import { useEffect, useRef, useState } from "react";
import type { Bildirim } from "@/lib/veri";
import {
  KADEME_ADI,
  SKORA_GIREN,
  TAHTA_ADI,
  TAHTA_NOTU,
  TIP_ADI,
  buyukTl,
  isaretliYuzde,
  kalemTutari,
  sayi,
  tamTarih,
  tamTl,
  yuzde,
} from "@/lib/bicim";
import { skorRengi, tahtaRenk } from "./Kart";

/**
 * f(r) — skoru YENİDEN HESAPLAMAK için değil, veritabanındaki sayının
 * nasıl çıktığını göstermek için. Kullanıcı 5·f(r)·K çarpımını kendi
 * yapıp `etki_skoru` ile karşılaştırabilsin diye duruyor.
 */
function fOran(r: number): number {
  if (r <= 0.01) return 0;
  if (r >= 1) return 1;
  return (Math.log10(r) + 2) / 2;
}

export default function DetayPanel({
  bildirim: b,
  onKapat,
  onOnceki,
  onSonraki,
  oncekiVar,
  sonrakiVar,
  konum,
}: {
  bildirim: Bildirim;
  onKapat: () => void;
  onOnceki: () => void;
  onSonraki: () => void;
  oncekiVar: boolean;
  sonrakiVar: boolean;
  konum: string;
}) {
  const [kopyaEtiketi, setKopyaEtiketi] = useState("Bağlantıyı kopyala");
  const kapatRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    kapatRef.current?.focus();
  }, []);

  useEffect(() => {
    setKopyaEtiketi("Bağlantıyı kopyala");
  }, [b.kap_id]);

  const kopyala = async () => {
    const adres = `${window.location.origin}${window.location.pathname}?b=${b.kap_id}`;
    try {
      await navigator.clipboard.writeText(adres);
      setKopyaEtiketi("Kopyalandı ✓");
    } catch {
      setKopyaEtiketi("Kopyalanamadı");
    }
  };

  const renk = skorRengi(b.etki_skoru);
  const skoraGirenler = (b.tutarlar ?? []).filter((t) => SKORA_GIREN.has(t.tip));
  const disaridakiler = (b.tutarlar ?? []).filter((t) => !SKORA_GIREN.has(t.tip));

  return (
    <>
      <button
        type="button"
        className="perde"
        onClick={onKapat}
        aria-label="Ayrıntı panelini kapat"
      />
      <aside
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-label={`${b.ticker} bildirim ayrıntısı`}
      >
        <div className="panel-bas">
          <span className="panel-ticker mono">{b.ticker}</span>
          <span className="mono" style={{ fontSize: 11, color: "var(--mut-2)" }}>
            {konum}
          </span>
          <div className="panel-gezin">
            <button
              type="button"
              className="panel-dugme"
              onClick={onOnceki}
              disabled={!oncekiVar}
              aria-label="Önceki bildirim"
              title="Önceki (↑)"
            >
              ↑
            </button>
            <button
              type="button"
              className="panel-dugme"
              onClick={onSonraki}
              disabled={!sonrakiVar}
              aria-label="Sonraki bildirim"
              title="Sonraki (↓)"
            >
              ↓
            </button>
            <button
              ref={kapatRef}
              type="button"
              className="panel-dugme"
              onClick={onKapat}
              aria-label="Kapat"
              title="Kapat (Esc)"
            >
              ×
            </button>
          </div>
        </div>

        <div className="panel-govde">
          <p className="panel-ust">
            {b.sirket} · {tamTarih(b.yayin_zamani)} ·{" "}
            {b.guncelleme_mi ? "güncelleme bildirimi" : "ilk bildirim"}
          </p>
          <h2>{b.is_tanimi ?? "—"}</h2>
          <p style={{ fontSize: 13, color: "var(--mut-2)", margin: "0 0 4px" }}>
            Karşı taraf: {b.karsi_taraf ?? "Açıklanmadı"}
            {b.karsi_taraf_niteligi ? ` · ${b.karsi_taraf_niteligi}` : ""}
          </p>
          {b.baslangic && (
            <p style={{ fontSize: 13, color: "var(--mut-2)", margin: 0 }}>
              Başlangıç: {b.baslangic}
            </p>
          )}

          {b.hap_ozet && b.hap_ozet.length > 0 && (
            <>
              <h3 className="bolum-bas mono">ÖZET</h3>
              <div>
                {b.hap_ozet.map((m, i) => (
                  <p className="ozet-madde" key={i}>
                    <span>{m}</span>
                  </p>
                ))}
              </div>
            </>
          )}

          {/* --------------------------------------------- hesap */}
          <h3 className="bolum-bas mono">A · BÜYÜKLÜK HESABI</h3>
          {b.etki_skoru !== null && b.ciro_orani !== null ? (
            <>
              <dl className="kutu">
                <div className="kutu-satir">
                  <dt>Net tutar (skora giren kalemler)</dt>
                  <dd className="mono">
                    {b.net_tutar_tl !== null ? tamTl(b.net_tutar_tl) : "—"}
                  </dd>
                </div>
                <div className="kutu-satir">
                  <dt>TTM hasılat (bildirim anında kamuya açık)</dt>
                  <dd className="mono">
                    {b.ttm_hasilat !== null ? tamTl(b.ttm_hasilat) : "—"}
                  </dd>
                </div>
                <div className="kutu-satir">
                  <dt>Hasılat oranı r</dt>
                  <dd className="mono">{yuzde(b.ciro_orani, 2)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>f(r) = (log₁₀ r + 2) / 2</dt>
                  <dd className="mono">{sayi(fOran(b.ciro_orani), 4)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>
                    K ({b.karsi_taraf ? "açık" : "gizli"} +{" "}
                    {b.guncelleme_mi ? "güncelleme" : "ilk"})
                  </dt>
                  <dd className="mono">{sayi(b.k)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt style={{ color: "var(--ink)", fontWeight: 600 }}>
                    Büyüklük skoru S
                  </dt>
                  <dd
                    className="mono"
                    style={{ color: renk, fontWeight: 700, fontSize: 15 }}
                  >
                    {sayi(b.etki_skoru)} / 5,00
                    {b.kademe ? ` · ${KADEME_ADI[b.kademe]}` : ""}
                  </dd>
                </div>
              </dl>
              <p className="formul-kutu mono" style={{ marginTop: 10 }}>
                S = 5 × {sayi(fOran(b.ciro_orani), 4)} × {sayi(b.k)} ={" "}
                {sayi(b.etki_skoru)}
              </p>
            </>
          ) : (
            <p className="tutar-yok-not" style={{ marginTop: 0 }}>
              Skor üretilmedi. Tutar ya da bildirim anındaki TTM hasılat
              çözülemediğinde skor gösterilmiyor — uydurma bir paydayla üretilen
              skor, skorsuzluktan kötüdür.
            </p>
          )}

          {/* --------------------------------------------- kalemler */}
          {(b.tutarlar?.length ?? 0) > 0 && (
            <>
              <h3 className="bolum-bas mono">
                ÇIKARILAN KALEMLER · HER SAYININ HAM CÜMLESİ
              </h3>
              <div className="kutu">
                {[...skoraGirenler, ...disaridakiler].map((t, i) => {
                  const girer = SKORA_GIREN.has(t.tip);
                  return (
                    <div className="kalem" key={i}>
                      <div className="kalem-ust">
                        <span className="kalem-tutar mono">
                          {kalemTutari(t.deger, t.para_birimi)}
                        </span>
                        <span
                          className={`cip mono ${girer ? "cip-mavi" : "cip-notr"}`}
                        >
                          {TIP_ADI[t.tip] ?? t.tip}
                        </span>
                        <span
                          style={{ fontSize: 11, color: "var(--mut-2)" }}
                        >
                          {girer ? "skora giriyor" : "skora girmiyor"}
                        </span>
                      </div>
                      <p className="kalem-alinti">“{t.alinti}”</p>
                    </div>
                  );
                })}
              </div>
              {disaridakiler.length > 0 && (
                <p className="tutar-yok-not">
                  Toplam sözleşme bedeli projenin kümülatif tutarıdır, yeni iş
                  değildir; skora katılsaydı hasılat oranı gerçekte olduğundan
                  kat kat büyük çıkardı.
                </p>
              )}
            </>
          )}

          {/* --------------------------------------------- tahta */}
          {b.tahta && (
            <>
              <h3 className="bolum-bas mono">B · TAHTA KALİTESİ</h3>
              <div className="tahta-satiri">
                <span
                  className="tahta-nokta"
                  style={{ background: `var(--${tahtaRenk(b.tahta)})` }}
                  aria-hidden="true"
                />
                <span className="tahta-ad">{TAHTA_ADI[b.tahta]}</span>
              </div>
              <p className="tahta-not">{TAHTA_NOTU[b.tahta]}</p>
              <dl className="kutu">
                <div className="kutu-satir">
                  <dt>Son 90 günde limit yakını gün</dt>
                  <dd className="mono">{b.tahta_v90 ?? "—"}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>Son 5 günde</dt>
                  <dd className="mono">{b.tahta_v5 ?? "—"}</dd>
                </div>
              </dl>
              <p className="tutar-yok-not">
                Tahta kalitesi skora girmez — bu bildirimin değil hissenin
                özelliğidir. Vekil ölçü: günlük getirisi ±%9&apos;u aşan gün
                sayısı (BIST limiti ±%10).
              </p>
            </>
          )}

          {/* --------------------------------------------- tepki */}
          {b.panel && (
            <>
              <h3 className="bolum-bas mono">C · BENZER BİLDİRİMLERİN TEPKİSİ</h3>
              <dl className="kutu">
                <div className="kutu-satir">
                  <dt>Medyan (3 günlük anormal getiri)</dt>
                  <dd className="mono">{isaretliYuzde(b.panel.medyan)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>Alt çeyrek – üst çeyrek</dt>
                  <dd className="mono">
                    {isaretliYuzde(b.panel.altCeyrek)} …{" "}
                    {isaretliYuzde(b.panel.ustCeyrek)}
                  </dd>
                </div>
                <div className="kutu-satir">
                  <dt>Pozitif sonuçlananlar</dt>
                  <dd className="mono">{yuzde(b.panel.pozitifOrani, 0)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>Akran grubu</dt>
                  <dd>
                    {b.panel.esas === "skor+tahta"
                      ? "aynı skor kademesi + aynı tahta"
                      : "aynı skor kademesi"}{" "}
                    <span className="mono">(n = {b.panel.n})</span>
                  </dd>
                </div>
              </dl>
              {!b.panel.guvenilir && (
                <p className="panel-uyari">
                  Bu hisse tedbirli tahtada. Ölçümlerimizde limit günü sayısı
                  mutlak hareketi güçlü biçimde artırıyor ama yönle ilişkisi
                  sıfır — yani buradaki dağılım fiyat oluşumunu değil oynaklığı
                  anlatıyor.
                </p>
              )}
              {b.car_3g !== null && (
                <p className="tutar-yok-not">
                  Bu bildirimin kendi 3 günlük anormal getirisi:{" "}
                  <strong className="mono">{isaretliYuzde(b.car_3g)}</strong>.
                  Geçmiş veridir, tahmin değildir.
                </p>
              )}
            </>
          )}

          <div className="panel-eylem">
            {b.kaynak_url && (
              <a
                className="bag"
                href={b.kaynak_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                KAP&apos;taki orijinal bildirim ↗
              </a>
            )}
            <button type="button" className="bag" onClick={kopyala}>
              {kopyaEtiketi}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
