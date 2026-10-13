FROM node:18-alpine AS build
WORKDIR /app
RUN npm install -g @quasar/cli
COPY package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY . .
# The source hard-codes the backend address; point it at the nginx /be proxy instead.
RUN grep -rl "http://localhost:5030" src | xargs sed -i 's#http://localhost:5030#/be#g'
RUN quasar build

FROM nginx:1.27-alpine
COPY nginx/container.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/spa /usr/share/nginx/html
