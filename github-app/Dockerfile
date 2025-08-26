FROM node:18-slim

WORKDIR /app

# Install deps first (leverage Docker layer cache)
COPY package*.json ./
RUN npm install --production --no-audit --no-fund

# Copy app code
COPY . .

ENV NODE_ENV=production \
    PORT=8080

EXPOSE 8080

CMD ["npm", "start"]


