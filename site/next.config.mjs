/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Veri saatlik tazeleniyor: KAP bildirimleri gün içinde düşüyor ama
  // skor/tepki hattı toplu koşuyor, dakikalık yenilemenin karşılığı yok.
  experimental: {},
};

export default nextConfig;
