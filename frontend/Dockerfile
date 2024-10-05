# build env
# При создании фронтенда разработчики использовали Node.js
# программу, выполняющую код на JavaScript.
FROM node:21.7.1-alpine
WORKDIR /app
# package*.json - это аналог requirements.txt
COPY package*.json ./
# npm (в Node.js) — это аналог pip (в Python)
RUN npm install --force
# Исходный код приложения копируется в образ
COPY . ./
# Выполняется сборка приложения для публикации на сервере
RUN npm run build
CMD cp -r build result_build
