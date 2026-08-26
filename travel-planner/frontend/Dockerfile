FROM node:22-alpine AS build
WORKDIR /web
COPY package*.json ./
RUN npm ci
COPY . ./

# These are intentionally build args, not checked-in values. AMap browser keys are
# public by design but must be domain-restricted in the AMap console.
ARG VITE_AMAP_JS_KEY
ARG VITE_AMAP_SECURITY_JS_CODE
ARG VITE_API_BASE_URL=
ARG VITE_DEMO_MODE=false
ENV VITE_AMAP_JS_KEY=$VITE_AMAP_JS_KEY \
    VITE_AMAP_SECURITY_JS_CODE=$VITE_AMAP_SECURITY_JS_CODE \
    VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_DEMO_MODE=$VITE_DEMO_MODE
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
