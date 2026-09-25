import type { Bildirim } from "@/lib/veri";
import {
  F_ORAN_METNI,
  SIKLIK_ORTA_ESIGI,
  SIKLIK_SIK_ESIGI,
  fOran,
  siklikRenk,
  oranRengi,
} from "@/lib/skor";
import {
  KADEME_ADI,
  SIKLIK_ADI,
  SIKLIK_NOTU,
  SKORA_GIREN,
  TAHTA_SINIR_NOTU,
  TIP_ADI,
  VBTS_KADEME_ADI,
  buyukTl,
  isaretliYuzde,
  kalemTutari,
  kisaTarih,
  sayi,
  tamTarih,
  tahtaGorunumu,
  tamTl,
  yuzde,
  yuzdeIyelik,
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
  const renk = oranRengi(b.ciro_orani);
  const skoraGirenler = (b.tutarlar ?? []).filter((t) => SKORA_GIREN.has(t.tip));
  const disaridakiler = (b.tutarlar ?? []).filter((t) => !SKORA_GIREN.has(t.tip));
  const Baslik = baslikEtiketi;
  const tahta = tahtaGorunumu(
    b.tahta,
    b.tahta_v90,
    b.tahta_v5,
    b.tahta_vbts_kademe,
  );
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
          {b.etki_skoru !== null && (
            <details className="acilir">
              <summary>Büyüklük skoru nasıl hesaplandı?</summary>
              <dl className="kutu">
                <div className="kutu-satir">
                  <dt>{F_ORAN_METNI}</dt>
                  <dd className="mono">{sayi(fOran(b.ciro_orani), 4)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>
                    Bilginin netliği K (müşteri adı{" "}
                    {b.karsiTarafAcik ? "açık" : "verilmemiş"} ·{" "}
                    {b.guncelleme_mi ? "güncelleme duyurusu" : "ilk duyuru"})
                  </dt>
                  <dd className="mono">{sayi(b.k)}</dd>
                </div>
                <div className="kutu-satir">
                  <dt>Büyüklük skoru S</dt>
                  <dd className="mono" style={{ fontWeight: 700 }}>
                    {sayi(b.etki_skoru)} / 5,00
                  </dd>
                </div>
              </dl>
              <p className="formul-kutu mono" style={{ marginTop: 10 }}>
                S = 5 × {sayi(fOran(b.ciro_orani), 4)} × {sayi(b.k)} ={" "}
                {sayi(b.etki_skoru)}
              </p>
              <p className="tutar-yok-not">
                S, oranı logaritmik bir ölçeğe taşır (%0,25 → 0, %100 → 5) ve
                bilginin netliğine göre ayarlar: müşterinin adı verilmemişse ya
                da duyuru önceki bir işin güncellemesiyse K 1&apos;in altına
                iner. Kartta görünen kademe S&apos;den değil doğrudan orandan
                gelir; S aşağıdaki &ldquo;benzer duyurular&rdquo;ı gruplamak
                için kullanılır.
              </p>
            </details>
          )}
        </>
      ) : (
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

      {/* --------------------------------------------- tahta */}
      {tahta && (
        <>
          <h3 className="bolum-bas mono">B · HİSSENİN SON 3 AYI</h3>
          <div className="tahta-satiri">
            <span
              className="tahta-nokta"
              style={{ background: `var(--${tahta.renk})` }}
              aria-hidden="true"
            />
            <span className="tahta-ad">{tahta.ad}</span>
          </div>
          <p className="tahta-not">{tahta.not}</p>
          <details className="acilir">
            <summary>Ayrıntı ve kaynak</summary>
            <dl className="kutu">
              <div className="kutu-satir">
                <dt>Bildirim anında borsa tedbiri (VBTS)</dt>
                <dd>
                  {b.tahta_vbts_kademe
                    ? `${VBTS_KADEME_ADI[b.tahta_vbts_kademe]}${
                        b.tahta_vbts_bitis ? ` · bitiş ${kisaTarih(b.tahta_vbts_bitis)}` : ""
                      }`
                    : "yok"}
                </dd>
              </div>
              <div className="kutu-satir">
                <dt>Devre kesicinin tetiklendiği gün · son 90 seans</dt>
                <dd className="mono">{b.tahta_v90 ?? "—"}</dd>
              </div>
              <div className="kutu-satir">
                <dt>Son 5 seansta</dt>
                <dd className="mono">{b.tahta_v5 ?? "—"}</dd>
              </div>
            </dl>
            <p className="tutar-yok-not">
              Sakin: 90 seansta en fazla 4 gün ve son 5 seansta hiç. Çok oynak:
              90 seansta 8 günden fazla ya da son 5 seansta en az 2 gün. Borsa
              tedbiri altında: bildirim anında Borsa İstanbul&apos;un volatilite
              tedbiri yürürlükte. Arası oynak. Bu bilgi büyüklüğe girmez;
              bildirimin değil hissenin özelliğidir. Kaynak Borsa
              İstanbul&apos;un KAP&apos;taki kendi kayıtları; yalnız
              bildirimden önce yayınlanmış olanlar sayılır. {TAHTA_SINIR_NOTU}
            </p>
          </details>
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
              özelliğidir, bildirimin değil. İlk ölçümde (2025-09 → 2026-09,
              613 bildirim) sık duyuru yapan şirketlerde duyuru başına ilgi
              belirgin biçimde daha sönüktü (t = −2,48). Önceki 12 ayda (690
              bildirim) aynı ilişki tekrarlanmadı (t = −0,74). Bu yüzden
              etiket yalnız olguyu söyler; tepki hakkında bir şey söylemez.
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

      {/* --------------------------------------------- tepki */}
      {b.panel && (
        <>
          <h3 className="bolum-bas mono">C · BENZER DUYURULARDAN SONRA HİSSELER NE YAPTI</h3>
          <p className="duz-cumle">
            Benzer {b.panel.n} duyurudan sonraki 3 günde hisseler piyasaya göre
            tipik olarak <strong className="mono">{isaretliYuzde(b.panel.medyan)}</strong>{" "}
            hareket etti; ortadaki yarısı{" "}
            <span className="mono">{isaretliYuzde(b.panel.altCeyrek)}</span> ile{" "}
            <span className="mono">{isaretliYuzde(b.panel.ustCeyrek)}</span>{" "}
            arasında kaldı, <span className="mono">{yuzde(b.panel.pozitifOrani, 0)}</span>&apos;i
            piyasayı geçti.
          </p>
          <p className="tutar-yok-not">
            Karşılaştırılan duyurular:{" "}
            {b.panel.esas === "skor+tahta"
              ? "büyüklük skoru aynı kademede ve hissenin son 3 ayı aynı durumda olanlar."
              : "büyüklük skoru aynı kademede olanlar (hissenin son 3 ayı aynı olan 20 duyuru bulunamadı)."}{" "}
            Geçmişin özetidir, bu hisse için tahmin değildir.
          </p>
          {!b.panel.guvenilir && tahta && (
            <p className="panel-uyari">
              Bu hisse son 3 ayda {tahta.ad.toLocaleLowerCase("tr")}. İki ayrı
              yılın verisinde de çok oynak ya da borsa tedbiri altındaki
              hisselerde duyuru sonrası ortalama tepki, sakin hisselerdekinden
              belirgin biçimde düşük çıktı; nedeni bilinmiyor.
            </p>
          )}
          {b.car_3g !== null && (
            <p className="tutar-yok-not">
              Bu duyurudan sonraki 3 günde hisse piyasaya göre{" "}
              <strong className="mono">{isaretliYuzde(b.car_3g)}</strong> hareket
              etti. Geçmiş veridir, tahmin değildir.
            </p>
          )}
          <details className="acilir">
            <summary>Bu rakamlar nasıl hesaplandı?</summary>
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
                <dt>Pozitif anormal getiri</dt>
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
            {(b.tepki_modeli === "ew" || b.tepki_modeli === "piyasa") &&
              b.beta !== null && (
                <p className="tutar-yok-not">
                  &ldquo;Piyasaya göre&rdquo; anormal getiri demek: hissenin{" "}
                  {b.tepki_modeli === "ew"
                    ? "eşit ağırlıklı BIST'e (≈630 hissenin ortalaması)"
                    : "XU100'e"}{" "}
                  göre beklenen getirisinden sapması. Beklenen getiri hissenin
                  bu kıyasa duyarlılığıyla (β) hesaplanır. Bu hissede{" "}
                  <strong className="mono">β = {sayi(b.beta, 2)}</strong>
                  {b.beta_kaynak === "evren_ort"
                    ? " — hisse yeni halka açıldığı için kendi betası tahmin edilemedi; evrenin ortalama betası kullanıldı."
                    : " (bildirimden önceki 120 işlem gününden, evren ortalamasına küçültülmüş)."}
                  {b.tepki_modeli === "ew" &&
                    " Kıyas XU100 değil, çünkü bu evrenin hisseleri büyük endeksi değil küçük hisselerin ortak hareketini izliyor."}
                </p>
              )}
          </details>
        </>
      )}
    </>
  );
}
