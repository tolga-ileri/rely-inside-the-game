# Build context: apps/web.  docker build --build-arg NEXT_PUBLIC_API_URL=https://<api-host> apps/web
FROM node:22-alpine AS deps
WORKDIR /app
RUN npm install -g pnpm@10.18.3 --silent
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS build
WORKDIR /app
RUN npm install -g pnpm@10.18.3 --silent
ARG NEXT_PUBLIC_API_URL=http://127.0.0.1:8100
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_OUTPUT=standalone NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S rely && adduser -S rely -G rely
COPY --from=build --chown=rely:rely /app/.next/standalone ./
COPY --from=build --chown=rely:rely /app/.next/static ./.next/static
USER rely
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD wget -qO- http://127.0.0.1:3000/health || exit 1
CMD ["node", "server.js"]
