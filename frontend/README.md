# Frontend Setup

## Prerequisites

- **Node.js** ≥22
- **Backend services** running (see ../backend/README.md)

## Setup

1. **Install dependencies:**

   ```bash
   cd frontend
   npm install
   ```

2. **Create `.env` file:**

   ```bash
   BACKEND_URL=http://localhost:8000

   NODE_TLS_REJECT_UNAUTHORIZED=0

   SESSION_SECRET=32_character_string
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

## After Running

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)

Make sure the backend is running on port 8000 before using the frontend. The application will automatically connect to the backend API for crawling and data retrieval.
