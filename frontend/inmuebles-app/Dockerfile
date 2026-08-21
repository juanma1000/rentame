# Build context is `frontend/` (npm workspaces root) so this stage can see
# the sibling `@rentame/auth` workspace inmuebles-app depends on.
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json eslint.config.mjs ./
COPY packages ./packages
COPY inmuebles-app ./inmuebles-app

RUN npm ci

# INMUEBLES_API_URL is baked into the browser bundle at build time (Rspack
# DefinePlugin — there is no server-side runtime for a static remote). It
# must be an address the *browser* can reach, i.e. the published host port,
# not the in-network service name.
ARG INMUEBLES_API_URL=http://localhost:8000
ENV INMUEBLES_API_URL=$INMUEBLES_API_URL
RUN npm run build -w rentame-inmuebles-app

FROM nginx:1.27-alpine
COPY --from=builder /app/inmuebles-app/dist /usr/share/nginx/html
COPY inmuebles-app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
