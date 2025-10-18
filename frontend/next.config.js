/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Proxy configuration is now handled by custom server.js
  skipTrailingSlashRedirect: true,
}

module.exports = nextConfig
