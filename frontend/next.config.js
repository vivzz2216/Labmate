/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
  },
  trailingSlash: true, // Better for static hosting
  // Remove rewrites for static export (API calls will be direct)
}

module.exports = nextConfig
