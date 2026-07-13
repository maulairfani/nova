FROM node:22-slim AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# NEXT_PUBLIC_* vars are inlined into the client bundle at build time, not
# read at container runtime - must be passed as a build-arg, not a
# docker-compose `environment:` entry. Defaults to the local dev backend
# URL - an ARG with no default resolves to an empty string (not unset),
# which would silently defeat the app code's own `?? "http://localhost:8000"`
# fallback (`??` only catches null/undefined, not ""). release.yml
# overrides this for production via --build-arg.
ARG NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
