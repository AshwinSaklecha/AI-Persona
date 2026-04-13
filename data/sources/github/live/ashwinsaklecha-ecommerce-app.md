# AshwinSaklecha/eCommerce-App

Source URL: https://github.com/AshwinSaklecha/eCommerce-App
Default branch: main
Visibility: public
Stars: 0
Forks: 0
Primary language summary: CSS, HTML, JavaScript, TypeScript

## Repository Description

No description provided.

## README Snapshot

Kindly refer to Readme files in frontend and backend folders.

Deployed Link - https://ecommerce-frontend-nzi8.onrender.com

## Additional README: backend

# E-commerce Backend

This is the backend service for the E-commerce platform selling fans and ACs.

## Setup Instructions

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in the root directory with the following variables:
```
PORT=5000
MONGODB_URI=mongodb://localhost:27017/ecommerce
JWT_SECRET=your_jwt_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

3. Start the development server:
```bash
npm run dev
```

## Project Structure

```
src/
├── config/         # Configuration files
├── middleware/     # Custom middleware
├── models/         # Database models
├── routes/         # API routes
└── index.js        # Entry point
```

## API Endpoints

### Authentication
- POST /api/auth/google
- GET /api/auth/google/callback

### Products
- GET /api/products
- GET /api/products/:id

### Orders
- POST /api/orders
- GET /api/orders
- GET /api/orders/:id
- PATCH /api/orders/:id/status

## Features

- Google OAuth authentication
- Role-based access control (admin, customer, rider)
- Product management
- Order management
- Rider assignment and tracking