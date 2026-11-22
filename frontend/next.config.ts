import type { NextConfig } from "next";

import { PUBLIC_PATHS } from "./src/lib/routes";

// Polish public URL -> English route, for running without nginx (`npm run dev`, Vercel).
// In Docker nginx does the same translation before requests reach Next.js.
const polishRoutes = Object.entries(PUBLIC_PATHS)
  .filter(([route, url]) => url !== `/${route}`)
  .flatMap(([route, url]) => [
    { source: url, destination: `/${route}` },
    { source: `${url}/:path*`, destination: `/${route}/:path*` },
  ]);

const nextConfig: NextConfig = {
  // Self-contained server bundle for a small production image (used by the deploy epic).
  output: "standalone",
  async rewrites() {
    const api = process.env.API_URL ?? "http://localhost:8000";
    return {
      beforeFiles: polishRoutes,
      afterFiles: [{ source: "/api/:path*", destination: `${api}/api/:path*` }],
      fallback: [],
    };
  },
};

export default nextConfig;
