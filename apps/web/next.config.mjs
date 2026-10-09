/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output is used in the Docker image (Linux). On Windows dev machines pnpm symlinks
  // can make standalone tracing fail, so it is opt-in via NEXT_OUTPUT=standalone.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  outputFileTracingRoot: import.meta.dirname,
  reactStrictMode: true,
  poweredByHeader: false,
};
export default nextConfig;
