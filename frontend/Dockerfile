FROM mirror.gcr.io/library/node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM mirror.gcr.io/library/node:18-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM mirror.gcr.io/library/node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Copy the static export output
COPY --from=builder /app/out ./out
COPY --from=builder /app/public ./public
# Install serve to serve static files
RUN npm install -g serve@latest

EXPOSE 3000
CMD ["serve", "-s", "out", "-l", "3000", "--no-clipboard"]
