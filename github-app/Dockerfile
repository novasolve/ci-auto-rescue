FROM node:18-slim

WORKDIR /app

# Install deps first (leverage Docker layer cache)
# Copy dependency manifests from the subdirectory (build context is repo root)
COPY github-app/package*.json ./
RUN npm install --production --no-audit --no-fund

# Copy app code from the subdirectory
COPY github-app/. .

ENV NODE_ENV=production \
    PORT=8080

EXPOSE 8080

CMD ["npm", "start"]


