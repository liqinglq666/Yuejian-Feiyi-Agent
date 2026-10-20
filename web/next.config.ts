import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{
      source: "/api/v1/:path*",
      destination: `${process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000"}/v1/:path*`,
    }];
  },
};

export default nextConfig;
