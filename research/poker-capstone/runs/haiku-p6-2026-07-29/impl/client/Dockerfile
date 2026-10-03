FROM nginx:alpine

# Copy static files to nginx html directory
COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/

# Default nginx.conf serves static files on port 80
# No custom config needed - default Alpine nginx serves from /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
