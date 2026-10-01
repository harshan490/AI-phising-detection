FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose port for Vite dev server (or build for production)
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
