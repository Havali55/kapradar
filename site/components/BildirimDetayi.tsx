import type { Bildirim } from "@/lib/veri";
import {
  F_ORAN_METNI,
  SIKLIK_ORTA_ESIGI,
  SIKLIK_SIK_ESIGI,
  fOran,
  siklikRenk,
  skorRengi,
  tahtaRenk,
} from "@/lib/skor";
import {
  KADEME_ADI,
  SIKLIK_ADI,
  SIKLIK_NOTU,
  SKORA_GIREN,
  TAHTA_ADI,
  TAHTA_NOTU,
  TAHTA_SINIR_NOTU,
  TIP_ADI,
  VBTS_KADEME_ADI,
  isaretliYuzde,
  kalemTutari,
  kisaTarih,
  sayi,
  tamTarih,
  tamTl,
  yuzde,
} from "@/lib/bicim";

/**
 * Bir bildirimin ayrıntısı — üç modül, hesabın dökümü ve her sayının
 * ham cümlesi.
 *
 * Saf gösterim: durum yok, olay yok, `"use client"` yok. İki yerde
 * kullanılıyor — akıştaki yan panel (`DetayPanel`) ve kalıcı sayfa
 * (`/kap/[kap_id]`). Tek kopya olması şart: 2026-09-22'de f(r)'nin
 * ikinci kopyası eski tabanla kalıp panelde uyuşmayan bir çarpım
 * gösterdi. Aynı hata iki ayrı ayrıntı görünümüyle tekrar edecekti.
 */
export default function BildirimDetayi({
  bildirim: b,
  baslikEtiketi = "h2",
}: {
  bildirim: Bildirim;
  /** Panelde h2, kalıcı sayfada h1 — sayfada başlık bir kez ve en üstte. */
  baslikEtiketi?: "h1" | "h2";
}) {
  const renk = skorRengi(b.etki_skoru);
  const skoraGirenler = (b.tutarlar ?? []).filter((t) => SKORA_GIREN.has(t.tip));
  const disaridakiler = (b.tutarlar ?? []).filter((t) => !SKORA_GIREN.has(t.tip));
  const Baslik = baslikEtiketi;

  return (
    <>
      <p className="panel-ust">
        {b.sirket} · {tamTarih(b.yayin_zamani)} ·{" "}
        {b.guncelleme_mi ? "güncelleme bildirimi" : "ilk bildirim"}
      </p>
      <Baslik>{b.is_tanimi ?? "—"}</Baslik>
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
              <dt>{F_ORAN_METNI}</dt>
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
                    <span style={{ fontSize: 11, color: "var(--mut-2)" }}>
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
              değildir; skora katılsaydı hasılat oranı gerçekte olduğundan kat
              kat büyük çıkardı.
            </p>
          )}
        </>
      )}

      {/* --------------------------------------------- tahta */}
      {b.tahta && (
        <>
          <h3 className="bolum-bas mono">B · ŞİRKET BAĞLAMI · TAHTA</h3>
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
              <dt>Bildirim anında VBTS tedbiri</dt>
              <dd>
                {b.tahta_vbts_kademe
                  ? `${VBTS_KADEME_ADI[b.tahta_vbts_kademe]}${
                      b.tahta_vbts_bitis ? ` · bitiş ${kisaTarih(b.tahta_vbts_bitis)}` : ""
                    }`
                  : "yok"}
              </dd>
            </div>
            <div className="kutu-satir">
              <dt>Devre kesici günü · son 90 seans</dt>
              <dd className="mono">{b.tahta_v90 ?? "—"}</dd>
            </div>
            <div className="kutu-satir">
              <dt>Son 5 seansta</dt>
              <dd className="mono">{b.tahta_v5 ?? "—"}</dd>
            </div>
          </dl>
          <p className="tutar-yok-not">
            Tahta kalitesi skora girmez — bu bildirimin değil hissenin
            özelliğidir. Kaynak Borsa İstanbul&apos;un KAP&apos;taki kendi
            kayıtları: pay bazında devre kesici bildirimleri ve Volatilite
            Bazlı Tedbir Sistemi duyuruları. Yalnız bildirimden önce
            yayınlanmış olanlar sayılır. {TAHTA_SINIR_NOTU}
          </p>
        </>
      )}

      {/* ------------------------------------- bildirim yorgunluğu */}
      {b.siklik && (
        <>
          <h3 className="bolum-bas mono">B · ŞİRKET BAĞLAMI · BİLDİRİM SIKLIĞI</h3>
          <div className="tahta-satiri">
            <span
              className="tahta-nokta"
              style={{ background: `var(--${siklikRenk(b.siklik)})` }}
              aria-hidden="true"
            />
            <span className="tahta-ad">{SIKLIK_ADI[b.siklik]}</span>
          </div>
          <p className="tahta-not">{SIKLIK_NOTU[b.siklik]}</p>
          <dl className="kutu">
            <div className="kutu-satir">
              <dt>Yeni İş İlişkisi bildirimi · önceki 12 ay (bu dahil)</dt>
              <dd className="mono">{b.bildirim_sikligi ?? "—"}</dd>
            </div>
            <div className="kutu-satir">
              <dt>Tüm KAP özel durum açıklaması · önceki 12 ay</dt>
              <dd className="mono">{b.kap_aciklama_12a ?? "—"}</dd>
            </div>
            {b.siklik_arsiv_gun !== null && b.siklik_arsiv_gun < 365 && (
              <div className="kutu-satir">
                <dt>Şirketin KAP geçmişi</dt>
                <dd>yalnız {b.siklik_arsiv_gun} gün — 12 ay dolmadı</dd>
              </div>
            )}
            <div className="kutu-satir">
              <dt>Kademe eşikleri</dt>
              <dd className="mono">
                seyrek ≤ {SIKLIK_ORTA_ESIGI - 1} · sık ≥ {SIKLIK_SIK_ESIGI}
              </dd>
            </div>
          </dl>
          <p className="tutar-yok-not">
            Bildirim sıklığı skora girmez — tahta kalitesi gibi bu da
            şirketin özelliği, bildirimin değil. Ölçümde ln(sıklık)
            katsayısı −0,111, hisse-kümelenmiş t = −2,48 (p = 0,013): sık
            bildirim yapan şirketlerde bildirim başına tepki belirgin
            biçimde daha sönük.
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
              Bu hisse tedbirli tahtada. Ölçümlerimizde limit günü sayısı mutlak
              hareketi güçlü biçimde artırıyor ama yönle ilişkisi sıfır — yani
              buradaki dağılım fiyat oluşumunu değil oynaklığı anlatıyor.
            </p>
          )}
          {b.car_3g !== null && (
            <p className="tutar-yok-not">
              Bu bildirimin kendi 3 günlük anormal getirisi:{" "}
              <strong className="mono">{isaretliYuzde(b.car_3g)}</strong>.
              Geçmiş veridir, tahmin değildir.
            </p>
          )}
          {b.tepki_modeli === "piyasa" && b.beta !== null && (
            <p className="tutar-yok-not">
              Anormal getiri piyasa modeliyle hesaplanır: beklenen getiri
              hissenin endekse duyarlılığına (β) göre düşülür, endeksin tamamı
              değil. Bu hissede{" "}
              <strong className="mono">β = {sayi(b.beta, 2)}</strong>
              {b.beta_kaynak === "evren_ort"
                ? " — hisse yeni halka açıldığı için kendi betası tahmin edilemedi; evrenin ortalama betası kullanıldı."
                : " (bildirimden önceki 120 işlem gününden, evren ortalamasına küçültülmüş)."}
            </p>
          )}
        </>
      )}
    </>
  );
}
