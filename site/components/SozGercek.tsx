import { isaretliYuzde, kat, sayi, yilda } from "@/lib/bicim";
import {
  anlamliMi,
  donemAdi,
  okumaTuru,
  type OkumaTuru,
  type SozOzeti,
  type SozSatiriAyrintili,
  type SozVerisi,
} from "@/lib/soz";
import SozGrafigi from "./SozGrafigi";

// Cümle sonuçtan kurulur (tasarım §5.3): 9A2026 raporları gelip sonuç
// zayıflarsa metin de kendiliğinden değişir. "Vay, bulduk" kalıbı yok.
const OKUMA: Record<OkumaTuru, string> = {
  "onde-anlamli":
    "Dürüst okuma: en çok duyuran üçte bir belirgin önde ve ilişki istatistiksel olarak anlamlı; yine de tek dönemlik bir gözlem.",
  onde:
    "Dürüst okuma: grup medyanlarında evet, en çok duyuran üçte bir belirgin önde; ama güçlü bir kural değil.",
  ayrismiyor:
    "Dürüst okuma: hayır, en çok duyuran üçte bir ötekilerden belirgin biçimde ayrışmıyor.",
};

export default function SozGercek({
  veri,
  ozet,
}: {
  veri: SozVerisi;
  ozet: SozOzeti<SozSatiriAyrintili>;
}) {
  const donem = donemAdi(veri.donem);
  const anlamli = anlamliMi(ozet.t, ozet.n);
  return (
    <section className="ana-bolum soz" aria-labelledby="soz-bas">
      <div className="soz-sol">
        <div className="ust-yazi">Söz ve gerçek</div>
        <h2 id="soz-bas">Çok iş duyuran şirketler, ertesi yıl gerçekten büyüdü mü?</h2>
        <p>
          {yilda(veri.sozYili)} duyurulan işlerin toplamını şirketin {veri.sozYili}{" "}
          cirosuna böldük ve şirketleri bu orana göre üç eşit gruba ayırdık. Sonra
          her şirketin <b>enflasyondan arındırılmış</b> ciro büyümesine baktık ({donem}).
        </p>
        <dl className="uc-sayi">
          {ozet.gruplar.map((g, i) => (
            <div key={g.ad}>
              <dt>{g.ad}</dt>
              <dd style={i === 2 ? { color: "var(--seri-duyuru)" } : undefined}>
                {isaretliYuzde(g.medyanBuyume, 1)}
              </dd>
              <small>
                duyuru/ciro ~{kat(g.medyanYogunluk)} · {g.satirlar.length} şirket
              </small>
            </div>
          ))}
        </dl>
        <p className="durust">
          {OKUMA[okumaTuru(ozet)]} {ozet.n} şirkette sıra korelasyonu{" "}
          <b>{sayi(ozet.rho, 2)}</b> (t = {sayi(ozet.t, 2)}); %5 düzeyinde{" "}
          {anlamli ? "anlamlı" : "anlamlı değil"}. Tek dönem; sözleşmeler çok yıllık,
          ciroya yansıması gecikebilir. Bu bir neden-sonuç iddiası değil.
        </p>
      </div>
      <div className="plaka soz-plaka">
        <div className="plaka-ust">
          <h3 id="soz-grafik-bas">
            {ozet.n} şirket · {donem} reel ciro büyümesi
          </h3>
          <span className="ust-yazi">her nokta bir şirket</span>
        </div>
        <SozGrafigi
          gruplar={ozet.gruplar}
          sozYili={veri.sozYili}
          donem={donem}
          baslikId="soz-grafik-bas"
        />
        <p className="alt-not">
          Büyüme, şirketin kendi raporundaki &quot;geçen yılın aynı dönemi&quot;
          sütunundan: TMS 29 gereği iki dönem aynı satın alma gücüyle raporlanıyor,
          ayrıca TÜFE gerekmiyor.
          {veri.nominal.length > 0 &&
            ` Raporunu yeniden ifade etmeyen ${veri.nominal.length} şirketin büyümesi nominal olduğu için dışarıda.`}
        </p>
      </div>
    </section>
  );
}
