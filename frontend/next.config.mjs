/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Production optimizations
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
  // NOTE: Do NOT set NEXT_PUBLIC_API_URL here via `env:`.
  // NEXT_PUBLIC_* vars are inlined at build time from the environment.
  // Setting a fallback here would bake 'http://localhost:8000' into the
  // production bundle. The Dockerfile passes the real URL via build-arg.
  // Experimental features
  experimental: {
    optimizePackageImports: ['recharts', '@tanstack/react-query'],
  },
  // Headers for security
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ];
  },
};

export default nextConfig;
