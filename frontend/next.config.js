/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
    formats: ['image/avif', 'image/webp'],
  },
  trailingSlash: true, // Better for static hosting
  compress: true, // Enable gzip compression
  poweredByHeader: false, // Remove X-Powered-By header
  generateEtags: true, // Enable ETags for caching
  // Remove rewrites for static export (API calls will be direct)
  
  // Note: Headers should be configured at the server/CDN level for static export
  // Recommended headers:
  // - X-Frame-Options: SAMEORIGIN
  // - X-Content-Type-Options: nosniff
  // - Referrer-Policy: origin-when-cross-origin
  // - Cache-Control: public, max-age=31536000, immutable (for /_next/static/)
}

module.exports = nextConfig
