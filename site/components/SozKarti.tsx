import { buyukTl, isaretliYuzde, kat, yilda } from "@/lib/bicim";
import {
  donemAdi,
  type SozOzeti,
  type SozSatiriAyrintili,
  type SozVerisi,
} from "@/lib/soz";

/**
 * Hisse sayfasının söz-gerçek kartı (tasarım §5.4). Ana sayfa modülünün
 * tanımı: söz, söz yılında duyurulan TL ÷ o yılın cirosu; gerçek, büyüme
 * döneminin reel ciro büyümesi. Söz gerçekten önce ölçülmüş olsun diye
 * "son 12 ay" değil söz yılı; son 12 ay tez cümlesinde.
 */
export default function SozKarti({
  ticker,
  veri,
  ozet,
}: {
  ticker: string;
  veri: SozVerisi;
  ozet: SozOzeti<SozSatiriAyrintili> | null;
}) {
  const s = veri.sirketler.get(ticker);
  if (!s) return null;
  const donem = donemAdi(veri.donem);
  const grup = s.reel
    ? ozet?.gruplar.find((g) => g.satirlar.some((x) => x.ticker === ticker))
    : undefined;

  return (
    <section className="soz-karti" aria-label="Söz ve gerçek">
      <span className="ust-yazi">Söz ve gerçek</span>
      <dl>
        <div>
          <dt>{yilda(veri.sozYili)} duyurulan</dt>
          <dd style={{ color: "var(--seri-duyuru)" }}>
            {s.yogunluk !== null ? kat(s.yogunluk) : buyukTl(s.tl)}
          </dd>
          <small>
            {s.yogunluk !== null
              ? `yıllık cirosu kadar iş · ${s.adet} iş`
              : `${s.adet} iş · ${veri.sozYili} cirosu bilinmiyor`}
          </small>
        </div>
        <div>
          <dt>Gerçekleşen · {donem}</dt>
          {s.buyume === null ? (
            <>
              <dd>—</dd>
              <small>Bu dönemin raporu yok.</small>
            </>
          ) : s.reel ? (
            <>
              <dd>{isaretliYuzde(s.buyume, 1)}</dd>
              <small>
                ciro büyümesi, enflasyondan arındırılmış
                {s.kaynakIndex !== null && (
                  <>
                    {" · "}
                    <a
                      href={`https://www.kap.org.tr/tr/Bildirim/${s.kaynakIndex}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      rapor ↗
                    </a>
                  </>
                )}
              </small>
            </>
          ) : (
            <>
              <dd>—</dd>
              <small>
                Şirket raporunu enflasyona göre yeniden ifade etmiyor; reel büyüme
                hesaplanamıyor.
              </small>
            </>
          )}
        </div>
      </dl>
      {grup && (
        <p className="soz-karti-alt">
          {grup.ad} grubunda; grubun medyanı {isaretliYuzde(grup.medyanBuyume, 1)}.
          Grupların nasıl kurulduğu ana sayfadaki &ldquo;Söz ve gerçek&rdquo;
          bölümünde.
        </p>
      )}
    </section>
  );
}
