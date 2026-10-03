import type { Bildirim } from "@/lib/veri";
import { SIKLIK_ORTA_ESIGI, SIKLIK_SIK_ESIGI, siklikRenk, oranRengi } from "@/lib/skor";
import {
  KADEME_ADI,
  SIKLIK_ADI,
  SIKLIK_NOTU,
  SKORA_GIREN,
  TIP_ADI,
  VBTS_KADEME_ADI,
  buyukTl,
  istanbulGunu,
  kalemTutari,
  kisaTarih,
  sayi,
  tamTarih,
  tamTl,
  yuzde,
  yuzdeIyelik,
} from "@/lib/bicim";

/**
 * Bir bildirimin ayrıntısı: büyüklük, hesabın dökümü, her sayının ham
 * cümlesi ve şirket bağlamı.
 *
 * Saf gösterim: durum yok, olay yok, `"use client"` yok. İki yerde
 * kullanılıyor: akıştaki yan panel (`DetayPanel`) ve kalıcı sayfa
 * (`/kap/[kap_id]`). Tek kopya olması şart: aynı hesabın iki görünümü
 * ayrışırsa okur iki farklı sayı görür.
 */
export default function BildirimDetayi({
  bildirim: b,
  baslikEtiketi = "h2",
}: {
  bildirim: Bildirim;
  /** Panelde h2, kalıcı sayfada h1 — sayfada başlık bir kez ve en üstte. */
  baslikEtiketi?: "h1" | "h2";
}) {
  const renk = oranRengi(b.ciro_orani);
  const skoraGirenler = (b.tutarlar ?? []).filter((t) => SKORA_GIREN.has(t.tip));
  const disaridakiler = (b.tutarlar ?? []).filter((t) => !SKORA_GIREN.has(t.tip));
  const Baslik = baslikEtiketi;
  // Şirketin yazdığı tanım isim değilse bile bilgi taşıyabilir
  // ("Yurt dışı yerleşik"); tek nokta gibi harfsiz değerler gösterilmez.
  const tanim =
    b.karsi_taraf && /[A-Za-zÇĞİÖŞÜçğıöşü]{3}/.test(b.karsi_taraf)
      ? b.karsi_taraf
      : null;

  return (
    <>
      <p className="panel-ust">
        {b.sirket} · {tamTarih(b.yayin_zamani)} ·{" "}
        {b.guncelleme_mi ? "güncelleme bildirimi" : "ilk bildirim"}
      </p>
      <Baslik>{b.is_tanimi ?? "—"}</Baslik>
      <p style={{ fontSize: 13, color: "var(--mut-2)", margin: "0 0 4px" }}>
        Karşı taraf:{" "}
        {b.karsiTarafAcik && tanim
          ? tanim
          : tanim
            ? `adı verilmemiş (şirketin yazdığı: “${tanim}”)`
            : "adı verilmemiş"}
        {b.karsi_taraf_niteligi ? ` · ${b.karsi_taraf_niteligi}` : ""}
      </p>
      {b.baslangic && (
        <p style={{ fontSize: 13, color: "var(--mut-2)", margin: 0 }}>
          Başlangıç: {b.baslangic}
        </p>
      )}
      <OncekiBag b={b} />

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

      {/* --------------------------------------------- büyüklük */}
      <h3 className="bolum-bas mono">A · BU İŞ ŞİRKET İÇİN NE KADAR BÜYÜK</h3>
      {b.elle_not && (
        <p className="elle-not">
          <strong>Elle incelendi.</strong> {b.elle_not}
        </p>
      )}
      {b.ciro_orani !== null ? (
        <>
          <p className="duz-cumle">
            Bu iş, şirketin son 12 aylık cirosunun{" "}
            <strong style={{ color: renk }}>{yuzdeIyelik(b.ciro_orani)}</strong>{" "}
            kadar
            {b.kademe && (
              <>
                {" "}
                · <strong>{b.kademe === "rutin" ? "Rutin iş" : KADEME_ADI[b.kademe]}</strong>
              </>
            )}
            .
          </p>
          <dl className="kutu">
            <div className="kutu-satir">
              <dt>İşin tutarı (TL karşılığı)</dt>
              <dd className="mono">
                {b.net_tutar_tl !== null ? tamTl(b.net_tutar_tl) : "—"}
              </dd>
            </div>
            <div className="kutu-satir">
              <dt>Şirketin son 12 aylık cirosu</dt>
              <dd className="mono">
                {b.ttm_hasilat !== null ? tamTl(b.ttm_hasilat) : "—"}
              </dd>
            </div>
            <div className="kutu-satir">
              <dt>Oran</dt>
              <dd className="mono" style={{ color: renk, fontWeight: 700 }}>
                {yuzde(b.ciro_orani, 2)}
              </dd>
            </div>
          </dl>
          <p className="tutar-yok-not">
            %5 ve üstü önemli iş, %15 ve üstü mega iş sayılır. Ciro, bildirim
            anında KAP&apos;ta yayınlanmış son finansal raporlardan hesaplanır
            (sonradan açıklanan rapor kullanılmaz); enflasyon muhasebesi
            nedeniyle farklı dönemlerin rakamları aynı TL birimine getirilir.
          </p>
        </>
      ) : b.elle_karar === "skorsuz" ? null : (
        <p className="tutar-yok-not" style={{ marginTop: 0 }}>
          Büyüklük hesaplanamadı: işin tutarı ya da bildirim anındaki şirket
          cirosu bilinmiyor. Uydurma bir paydayla hesaplanan oran, hiç oran
          olmamasından kötüdür.
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
                      {girer ? "hesaba giriyor" : "hesaba girmiyor"}
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
              değildir; hesaba katılsaydı oran gerçekte olduğundan kat kat
              büyük çıkardı.
            </p>
          )}
        </>
      )}

      {/* ------------------------------- borsa tedbiri (bildirim anı) */}
      {b.tahta_vbts_kademe != null && b.tahta_vbts_kademe > 0 && (
        <>
          <h3 className="bolum-bas mono">B · BORSA TEDBİRİ (BİLDİRİM ANINDA)</h3>
          <p className="tahta-not">
            Borsa İstanbul&apos;un volatilite tedbiri yürürlükteydi:{" "}
            {VBTS_KADEME_ADI[b.tahta_vbts_kademe] ?? `kademe ${b.tahta_vbts_kademe}`}
            {b.tahta_vbts_bitis ? `, bitiş ${kisaTarih(b.tahta_vbts_bitis)}` : ""}.
            Kaynak: Borsa İstanbul&apos;un KAP&apos;taki kayıtları. Büyüklüğe girmez.
          </p>
        </>
      )}

      {/* ------------------------------------- bildirim yorgunluğu */}
      {b.siklik && (
        <>
          <h3 className="bolum-bas mono">B · ŞİRKET BU TÜR DUYURUYU NE SIKLIKTA YAPIYOR</h3>
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
              <dt>Yeni iş ilişkisi duyurusu · önceki 12 ay (bu dahil)</dt>
              <dd className="mono">{b.bildirim_sikligi ?? "—"}</dd>
            </div>
            <div className="kutu-satir">
              <dt>KAP&apos;taki bütün özel durum açıklamaları · önceki 12 ay</dt>
              <dd className="mono">{b.kap_aciklama_12a ?? "—"}</dd>
            </div>
            {b.siklik_arsiv_gun !== null && b.siklik_arsiv_gun < 365 && (
              <div className="kutu-satir">
                <dt>Şirketin KAP geçmişi</dt>
                <dd>yalnız {b.siklik_arsiv_gun} gün — 12 ay dolmadı</dd>
              </div>
            )}
          </dl>
          <details className="acilir">
            <summary>Bu bilgi ne söylüyor, ne söylemiyor?</summary>
            <p className="tutar-yok-not">
              Seyrek: 12 ayda en fazla {SIKLIK_ORTA_ESIGI - 1} duyuru; sık: en az{" "}
              {SIKLIK_SIK_ESIGI}. Sıklık büyüklüğe girmez; şirketin
              özelliğidir, bildirimin değil. Şirketin ne sıklıkla duyuru
              yaptığını söyler, duyurunun önemini söylemez.
            </p>
          </details>
        </>
      )}

      {/* ------------------------------- fon sahipliği (bildirim anı) */}
      {/* `!= null`, `!==` değil: fon sütunları view'a sonradan eklendi ve
          Next'in fetch önbelleği eski şekilli satırları (alan hiç yok,
          yani undefined) bir süre daha sunabiliyor. 2026-09-23'te build
          664 eski kayıt yüzünden buyukTl(undefined) ile düştü. */}
      {b.fon_sayisi != null && b.fon_tl != null && (
        <>
          <h3 className="bolum-bas mono">B · ŞİRKET BAĞLAMI · FONLAR (BİLDİRİM ANINDA)</h3>
          <dl className="kutu">
            <div className="kutu-satir">
              <dt>Pozisyon açıklayan fonlar</dt>
              <dd className="mono">
                {b.fon_sayisi} fon · {buyukTl(b.fon_tl)}
                {b.gunluk_hacim_tl
                  ? ` · ≈ ${sayi(b.fon_tl / b.gunluk_hacim_tl, 1)} günlük hacim`
                  : ""}
              </dd>
            </div>
            {b.fon_tasfiye_tl !== null && b.fon_tasfiye_tl > 0 && (
              <div className="kutu-satir">
                <dt>Bunun tasfiyedeki fonlarda olan kısmı</dt>
                <dd className="mono">{buyukTl(b.fon_tasfiye_tl)}</dd>
              </div>
            )}
          </dl>
          <p className="tutar-yok-not">
            Her fonun bu bildirimden önce KAP&apos;ta yayınlanmış son Portföy
            Dağılım Raporu. Hissenin bugünkü fon durumu için hisse sayfasına
            bakın. Fon pozisyonu skora girmez.
          </p>
        </>
      )}
    </>
  );
}

/**
 * Önceki bildirime bağ (`kap_radar.bag`). Düzeltilen bildirim yayından
 * kalktığı için ona bağlantı verilmez; diğerlerinde verilir.
 */
function OncekiBag({ b }: { b: Bildirim }) {
  if (!b.onceki_tur || !b.onceki_yayin || !b.onceki_kap_id) return null;
  const gun = istanbulGunu(b.onceki_yayin);
  const bag = <a href={`/kap/${b.onceki_kap_id}`}>{gun} tarihli bildirim</a>;
  return (
    <p className="bag-not">
      {b.onceki_tur === "duzeltme" ? (
        <>Bu bildirim {gun} tarihli bildirimi düzeltiyor; düzeltilen bildirim yayından kaldırıldı.</>
      ) : b.onceki_tur === "ayni_is" ? (
        <>Bu iş aynı tutarla {bag} ile duyurulmuştu; burada yeni iş olarak sayılmıyor.</>
      ) : (
        <>Bu bildirim, {bag} ile duyurulan işin güncellemesi.</>
      )}
    </p>
  );
}
