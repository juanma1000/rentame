# Build context is `frontend/` (npm workspaces root) so this stage can see
# the sibling `@rentame/auth` workspace shell depends on.
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json eslint.config.mjs ./
COPY packages ./packages
COPY shell ./shell

RUN npm ci
RUN npm run build -w rentame-shell

FROM nginx:1.27-alpine
COPY --from=builder /app/shell/dist /usr/share/nginx/html
COPY shell/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
