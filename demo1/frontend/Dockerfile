FROM nginx:1.27-alpine
#/etc/nginx/conf.d/default.conf：这是 Nginx 默认读取配置的位置。
COPY nginx.conf /etc/nginx/conf.d/default.conf
# /usr/share/nginx/html：这是 Nginx 默认寻找 index.html 并对外展示的文件夹。
COPY web /usr/share/nginx/html  

EXPOSE 80
