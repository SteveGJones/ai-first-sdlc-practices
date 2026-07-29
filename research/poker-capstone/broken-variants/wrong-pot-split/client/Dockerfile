FROM nginx:alpine

COPY index.html style.css app.js /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -q -O /dev/null http://localhost:80/ || exit 1
