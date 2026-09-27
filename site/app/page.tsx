import Link from "next/link";
import CetvelPlakasi, { type CetvelIsi } from "@/components/CetvelPlakasi";
import HisseArama from "@/components/HisseArama";
import IsKarti from "@/components/IsKarti";
import IsSatiri from "@/components/IsSatiri";
import NasilCalisiyor from "@/components/NasilCalisiyor";
import SozGercek from "@/components/SozGercek";
import { cetvelPenceresi, enBuyukler, karsiTarafMetni, ozetMetni } from "@/lib/anasayfa";
import { gunAy, isaretliYuzde, kisaTarih, sayi } from "@/lib/bicim";
import { ozetle, sozSatirlariKur } from "@/lib/soz";
import {
  anaSatirlariGetir,
  hisseSecenekleriGetir,
  piyasaBandiGetir,
  reelBuyumeGetir,
} from "@/lib/veri";

// Veri hattı günde bir toplu koşuyor; saatlik tazeleme yeterli. Cetvel
// penceresi sayfanın üretildiği andan geriye sayılıyor.
export const revalidate = 3600;

const SAYI_ADI = ["", "", "iki ", "üç "];

export default async function AnaSayfa() {
  const [satirlar, buyumeler, bant, hisseler] = await Promise.all([
    anaSatirlariGetir(),
    reelBuyumeGetir(),
    piyasaBandiGetir(),
    hisseSecenekleriGetir(),
  ]);

  const pencere = cetvelPenceresi(satirlar, Date.now());
  const cetvelIsleri: CetvelIsi[] = pencere.isler.map((s) => ({
    kap_id: s.kap_id,
    ticker: s.ticker,
    oran: s.ciro_orani as number,
    tl: s.net_tutar_tl,
    ozet: ozetMetni(s),
    karsi: karsiTarafMetni(s),
    zaman: s.yayin_zamani,
  }));
  const ilkUc = enBuyukler(pencere.isler);
  const soz = sozSatirlariKur(satirlar, buyumeler);
  const sozOzeti = soz ? ozetle(soz.satirlar) : null;

  const sirketSayisi = new Set(satirlar.map((s) => s.ticker)).size;
  const son = satirlar[0]?.yayin_zamani ?? null;
  const ilk = satirlar.at(-1)?.yayin_zamani ?? null;
  const ciroluSirket = new Set(
    satirlar.filter((s) => s.ttm_hasilat !== null).map((s) => s.ticker),
  ).size;
  const elleKarar = satirlar.filter((s) => s.elle_karar != null).length;

  return (
    <main className="govde ana">
      <section className="ana-kahraman">
        <div>
          <div className="ust-yazi">Borsa İstanbul · yeni iş ilişkisi bildirimleri</div>
          <h1>
            Bir şirket yeni iş duyurdu. <em>Kendi cirosuna göre</em> ne kadar büyük?
          </h1>
          <p className="ana-giris">
            KAP&apos;taki her yeni iş bildirimini okuyor, tutarı çıkarıp şirketin son 12
            aylık cirosuna bölüyoruz. Tahmin yok; her sayının yanında bildirimin kendi
            cümlesi var.
          </p>
          <HisseArama hisseler={hisseler} buyuk />
          <div className="hizli">
            <span>En çok iş duyuranlar:</span>
            {hisseler.slice(0, 5).map((h) => (
              <Link key={h.t} href={`/hisse/${h.t}`}>
                {h.t}
              </Link>
            ))}
          </div>
          <p className="tazelik">
            Her iş günü 19:30&apos;da güncellenir · <b>{sayi(satirlar.length, 0)}</b> bildirim ·{" "}
            <b>{sirketSayisi}</b> şirket
            {son && (
              <>
                {" "}
                · son bildirim <b>{gunAy(son, true)}</b>
              </>
            )}
          </p>
        </div>
        <section className="plaka cetvel-plaka" aria-labelledby="cetvel-bas">
          <div className="plaka-ust">
            <h2 id="cetvel-bas">
              Son {pencere.gun} günde {cetvelIsleri.length} iş, şirketlerinin cirosuna göre
            </h2>
            <span className="ust-yazi">cironun yüzdesi · log ölçek</span>
          </div>
          <CetvelPlakasi isler={cetvelIsleri} baslikId="cetvel-bas" />
          <p className="alt-not">
            Her nokta bir iş duyurusu; yeri, işin şirketin son 12 aylık cirosuna oranı.
            Aynı tutar küçük şirkette sağa, büyük şirkette sola düşer. Noktanın üstüne
            gelin ya da Tab ile gezin; tıklayınca bildirimin kanıt sayfası açılır.
            {pencere.gun > 14 && " Son 14 günde 8'den az iş vardı, pencere 30 güne uzatıldı."}
          </p>
        </section>
      </section>

      {ilkUc.length > 0 && (
        <section className="ana-bolum" aria-labelledby="buyuk-bas">
          <div className="ana-bolum-bas">
            <h2 id="buyuk-bas">
              Son {pencere.gun} günün en büyük {SAYI_ADI[ilkUc.length]}işi
            </h2>
            <Link className="sag" href="/akis">
              Bütün bildirimler →
            </Link>
          </div>
          <div className="is-kartlari">
            {ilkUc.map((s) => (
              <IsKarti key={s.kap_id} s={s} />
            ))}
          </div>
        </section>
      )}

      {soz && sozOzeti && <SozGercek veri={soz} ozet={sozOzeti} />}

      <NasilCalisiyor
        yayinda={satirlar.length}
        ilk={ilk ? gunAy(ilk, true) + " " + ilk.slice(0, 4) : "—"}
        elleKarar={elleKarar}
        ciroluSirket={ciroluSirket}
      />

      <section className="ana-bolum" aria-labelledby="son-bas">
        <div className="ana-bolum-bas">
          <h2 id="son-bas">Son bildirimler</h2>
          <Link className="sag" href="/akis">
            Bütün bildirimler ve süzgeçler →
          </Link>
        </div>
        {bant && (
          <p className="piyasa-satiri">
            Piyasa bağlamı, son 5 seans ({kisaTarih(bant.son_tarih)} itibarıyla): eşit
            ağırlıklı BIST{" "}
            <b className="mono">{bant.ew_5s !== null ? isaretliYuzde(bant.ew_5s, 1) : "—"}</b> ·
            XU100{" "}
            <b className="mono">
              {bant.xu100_5s !== null ? isaretliYuzde(bant.xu100_5s, 1) : "—"}
            </b>
          </p>
        )}
        <div className="is-satirlari">
          {satirlar.slice(0, 8).map((s) => (
            <IsSatiri key={s.kap_id} s={s} />
          ))}
        </div>
      </section>
    </main>
  );
}
