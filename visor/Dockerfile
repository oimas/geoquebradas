FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html config.js /usr/share/nginx/html/
COPY img /usr/share/nginx/html/img
EXPOSE 80
