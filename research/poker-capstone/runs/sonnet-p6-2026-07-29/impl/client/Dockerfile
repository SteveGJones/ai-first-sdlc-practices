FROM nginx:1.27-alpine

# Static client only (index.html + app.js + style.css) — no build step.
COPY index.html /usr/share/nginx/html/index.html
COPY app.js /usr/share/nginx/html/app.js
COPY style.css /usr/share/nginx/html/style.css

# The deep-link contract (?table=...&seat=...) is handled client-side by
# app.js reading window.location.search, so the default nginx config
# serving index.html at / is sufficient — no server-side routing needed.

EXPOSE 80
