import type { NextConfig } from "next";

// Where the FastAPI backend runs. Read on the server only, never sent to browsers.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // The browser only ever talks to this Next.js app. Requests to /api/* are
  // forwarded to the backend, so login cookies are first-party and no CORS
  // setup is needed.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
