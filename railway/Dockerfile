FROM node:24-alpine
WORKDIR /app
COPY railway-dist/ /app/
ENV DATA_DIR=/data
EXPOSE 3000
CMD ["node","server.mjs"]
