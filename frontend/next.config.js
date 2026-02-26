/** @type {import('next').NextConfig} */
const apiProxyTarget = process.env.API_PROXY_TARGET?.replace(/\/$/, '');

const nextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
      { protocol: 'http', hostname: '**' },
    ],
  },
  async rewrites() {
    if (!apiProxyTarget) {
      return [];
    }

    return [
      {
        source: '/api/:path*',
        destination: `${apiProxyTarget}/api/:path*/`,
      },
    ];
  },
};

module.exports = nextConfig;
