# Build context is `frontend/` (npm workspaces root) so this stage can see
# the sibling `@rentame/auth`/`@rentame/ui`/`@rentame/design-tokens` workspaces
# arrendamiento-app depends on. Same pattern as inmuebles-app/Dockerfile.
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json eslint.config.mjs ./
COPY packages ./packages
COPY arrendamiento-app ./arrendamiento-app

RUN npm ci

# ARRENDAMIENTO_API_URL is baked into the browser bundle at build time
# (Rspack DefinePlugin — there is no server-side runtime for a static
# remote). It must be an address the *browser* can reach, i.e. the
# published host port, not the in-network service name.
ARG ARRENDAMIENTO_API_URL=http://localhost:8000
ENV ARRENDAMIENTO_API_URL=$ARRENDAMIENTO_API_URL
RUN npm run build -w rentame-arrendamiento-app

FROM nginx:1.27-alpine
COPY --from=builder /app/arrendamiento-app/dist /usr/share/nginx/html
COPY arrendamiento-app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
