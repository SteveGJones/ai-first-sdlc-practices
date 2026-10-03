# --- Build stage -------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src

RUN npm install
RUN npm run build

# --- Runtime stage -------------------------------------------------------
# Serves the static, built client bundle over plain HTTP on container
# port 80. The bundle itself determines the game server's address at
# runtime from window.location.hostname (see src/net/serverConfig.ts) —
# nothing server-related is baked in at build/serve time.
FROM nginx:1.27-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
