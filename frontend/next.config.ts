import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle for a small production image (used by the deploy epic).
  output: "standalone",
  // In Docker, nginx routes /api to the backend before requests reach Next.js.
  // This rewrite only matters when running `npm run dev` directly on your machine.
  async rewrites() {
    const api = process.env.API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
