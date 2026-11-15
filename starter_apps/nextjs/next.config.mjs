/** @type {import('next').NextConfig} */
const nextConfig = {
  // El Dockerfile copia .next/standalone: genera un servidor minimo con solo lo necesario.
  output: "standalone",
  poweredByHeader: false,
};

export default nextConfig;
