"use client";

import type { Bildirim } from "@/lib/veri";
import {
  KADEME_ADI,
  TAHTA_ADI,
  TAHTA_NOTU,
  buyukTl,
  gecenSure,
  isaretliYuzde,
  sayi,
  yuzde,
} from "@/lib/bicim";

/** Kutu çiziminin ölçeği: tepkilerin ezici çoğunluğu ±%8 içinde. */
const UC = 0.08;

export function skorRengi(skor: number | null): string {
  if (skor === null) return "var(--ken)";
  if (skor >= 3) return "var(--mavi-koyu)";
  if (skor >= 2) return "var(--mavi)";
  return "var(--mut-2)";
}

export function tahtaRenk(tahta: string): string {
  if (tahta === "temiz") return "yes";
  if (tahta === "hareketli") return "kehribar";
  return "kir";
}

function konum(v: number): string {
  const k = Math.max(-UC, Math.min(UC, v));
  return `${(((k + UC) / (2 * UC)) * 100).toFixed(1)}%`;
}

/**
 * Kart bir `article`; tıklanabilir alan içindeki tek butonun ::after
 * katmanı. Böylece hem tüm yüzey tıklanabiliyor hem de klavyeyle tek
 * odak durağı oluyor — `button` içine `dl` koyan geçersiz yapı yok.
 */
export default function Kart({
  bildirim: b,
  onAc,
}: {
  bildirim: Bildirim;
  onAc: () => void;
}) {
  const renk = skorRengi(b.etki_skoru);
  const tahta = b.tahta;

  return (
    <article className="kart">
      <span className="kart-ray" style={{ background: renk }} aria-hidden="true" />
      <div className="kart-ic">
        <div className="kart-ust">
          <button type="button" className="kart-ac" onClick={onAc}>
            <span className="kart-ticker mono">{b.ticker}</span>
            <span className="gizli-metin">
              {" "}
              — {b.is_tanimi ?? "bildirim"} ayrıntısını aç
            </span>
          </button>
          <span className="kart-sirket">{b.sirket}</span>
          {tahta && (
            <span className={`cip cip-${tahta} mono`}>{TAHTA_ADI[tahta]}</span>
          )}
          {b.guncelleme_mi && (
            <span className="cip cip-notr mono">GÜNCELLEME</span>
          )}
          <span className="kart-bos" />
          <time className="kart-zaman mono" dateTime={b.yayin_zamani}>
            {gecenSure(b.yayin_zamani)}
          </time>
        </div>

        <p className="kart-is">{b.is_tanimi ?? "—"}</p>
        <p className="kart-karsi">
          Karşı taraf: {b.karsi_taraf ?? "Açıklanmadı"}
          {b.karsi_taraf_niteligi ? ` · ${b.karsi_taraf_niteligi}` : ""}
        </p>

        <div className="moduller">
          {/* ------------------------------------------- A · büyüklük */}
          <section className="modul">
            <h3 className="modul-et mono">A · BÜYÜKLÜK SKORU</h3>
            {b.etki_skoru !== null ? (
              <>
                <div className="skor-satiri">
                  <span className="skor mono" style={{ color: renk }}>
                    {sayi(b.etki_skoru)}
                  </span>
                  <span className="skor-max mono">/ 5,00</span>
                  <span className="skor-kademe">
                    {b.kademe ? KADEME_ADI[b.kademe] : ""}
                  </span>
                </div>
                <div className="skor-cubuk">
                  <div
                    className="skor-dolgu"
                    style={{
                      width: `${(b.etki_skoru / 5) * 100}%`,
                      background: renk,
                    }}
                  />
                </div>
                <dl className="kv mono">
                  <dt>Net tutar</dt>
                  <dd>{b.net_tutar_tl !== null ? buyukTl(b.net_tutar_tl) : "—"}</dd>
                  <dt>TTM hasılat</dt>
                  <dd>{b.ttm_hasilat !== null ? buyukTl(b.ttm_hasilat) : "—"}</dd>
                  <dt>Hasılat oranı r</dt>
                  <dd className="vurgu">
                    {b.ciro_orani !== null ? yuzde(b.ciro_orani) : "—"}
                  </dd>
                  <dt>Şeffaflık K</dt>
                  <dd>{sayi(b.k)}</dd>
                </dl>
              </>
            ) : (
              <>
                <p className="tutar-yok">
                  {b.tutar_gizli ? "Tutar Açıklanmadı" : "Skor Üretilmedi"}
                </p>
                <p className="tutar-yok-not">
                  {b.net_tutar_tl === null
                    ? "Net tutar serbest metinden çıkarılamadığı için büyüklük skoru üretilmedi."
                    : "Bildirim anındaki TTM hasılat çözülemediği için skor üretilmedi."}
                </p>
                <dl className="kv mono" style={{ marginTop: 10 }}>
                  <dt>TTM hasılat</dt>
                  <dd>{b.ttm_hasilat !== null ? buyukTl(b.ttm_hasilat) : "—"}</dd>
                  <dt>Şeffaflık K</dt>
                  <dd>{sayi(b.k)}</dd>
                </dl>
              </>
            )}
          </section>

          {/* ------------------------------------------- B · tahta */}
          <section className="modul">
            <h3 className="modul-et mono">B · TAHTA KALİTESİ</h3>
            {tahta ? (
              <>
                <div className="tahta-satiri">
                  <span
                    className="tahta-nokta"
                    style={{ background: `var(--${tahtaRenk(tahta)})` }}
                    aria-hidden="true"
                  />
                  <span className="tahta-ad">{TAHTA_ADI[tahta]}</span>
                </div>
                <p className="tahta-not">{TAHTA_NOTU[tahta]}</p>
                <dl className="kv mono">
                  <dt>Limit yakını gün (90g)</dt>
                  <dd>{b.tahta_v90 ?? "—"}</dd>
                  <dt>Son 5 günde</dt>
                  <dd>{b.tahta_v5 ?? "—"}</dd>
                </dl>
              </>
            ) : (
              <p className="tutar-yok-not" style={{ marginTop: 0 }}>
                Bildirim anında yeterli fiyat geçmişi olmadığı için tahta
                kalitesi hesaplanamadı.
              </p>
            )}
          </section>

          {/* ------------------------------------------- C · tepki */}
          <section className="modul">
            <h3 className="modul-et mono">C · GEÇMİŞ TEPKİ [t₀, t₀+2]</h3>
            {b.panel ? (
              <>
                <div className="panel-medyan">
                  <span
                    className="panel-deger mono"
                    style={{
                      color:
                        b.panel.medyan > 0
                          ? "var(--yes)"
                          : b.panel.medyan < 0
                            ? "var(--kir)"
                            : "var(--mut-2)",
                    }}
                  >
                    {isaretliYuzde(b.panel.medyan)}
                  </span>
                  <span className="panel-et">medyan</span>
                </div>
                <div className="kutu-cizgi">
                  <span className="kutu-taban" />
                  <span
                    className="kutu-iqr"
                    style={{
                      left: konum(b.panel.altCeyrek),
                      width: `calc(${konum(b.panel.ustCeyrek)} - ${konum(
                        b.panel.altCeyrek,
                      )})`,
                    }}
                  />
                  <span className="kutu-sifir" />
                  <span
                    className="kutu-medyan"
                    style={{ left: konum(b.panel.medyan) }}
                  />
                </div>
                <div className="kutu-uc mono">
                  <span>{isaretliYuzde(b.panel.altCeyrek)}</span>
                  <span style={{ color: "var(--mut-3)" }}>Ç1 – Ç3</span>
                  <span>{isaretliYuzde(b.panel.ustCeyrek)}</span>
                </div>
                {b.panel.guvenilir ? (
                  <p className="panel-alt">
                    n = {b.panel.n} benzer bildirim · tahmin değil, dağılım
                  </p>
                ) : (
                  <p className="panel-uyari">
                    Tedbirli tahta: burada geçmiş hareket fiyat oluşumunu değil
                    oynaklığı yansıtıyor. n = {b.panel.n}
                  </p>
                )}
              </>
            ) : (
              <p className="tutar-yok-not" style={{ marginTop: 0 }}>
                Skor üretilmediği için akran grubu kurulamadı.
              </p>
            )}
          </section>
        </div>
      </div>
    </article>
  );
}
