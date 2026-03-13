# AgriSense — Agricultural Intelligence Platform

AI-powered agricultural intelligence platform built for Indian farmers.

## Features

| Feature | Description |
|---|---|
| **Disease Detection** | Upload crop leaf photos → instant disease diagnosis with chemical, organic & prevention treatments |
| **Soil Health Analysis** | Enter soil test values → ICAR-standard analysis with crop-specific fertilizer recommendations |
| **Weather & Pest Forecast** | 7-day weather forecast with pest risk alerts and spray window suggestions |
| **Crop Calendar** | Day-by-day growing schedule for Rice, Wheat, Tomato, Cotton, Potato, Maize |
| **Market Prices** | Live mandi prices for 10 commodities with MSP comparison and selling advisory |
| **Farmer Community** | Q&A forum with expert answers, categories, and crop-specific discussions |

## Crops Supported

Rice, Wheat, Tomato, Cotton, Potato, Maize, Sugarcane, Soybean, Groundnut, Onion

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite/PostgreSQL, Pydantic v2
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Zustand
- **AI/ML**: ONNX Runtime (production), Knowledge-base (development)
- **APIs**: OpenWeatherMap, data.gov.in (market prices)

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Backend runs on `http://localhost:8000`, Frontend on `http://localhost:3000`.

## API Endpoints

| Route | Description |
|---|---|
| `POST /auth/register` | Register new farmer |
| `POST /auth/login` | Login |
| `POST /disease/scan` | Upload image for disease detection |
| `POST /soil/analyze` | Analyze soil test values |
| `GET /weather/forecast` | Weather + pest risk forecast |
| `POST /calendar/create` | Create crop calendar |
| `GET /market/prices/{commodity}` | Get mandi prices |
| `GET /community/posts` | List community posts |

## License

MIT
