# StockPilot - Inventory & POS SaaS

A modern, full-stack Point of Sale and Inventory Management system built with FastAPI (Python) and Next.js (React/TypeScript).

## Features

- 🔐 **Multi-tenant SaaS** - Support for multiple businesses with role-based access
- 📊 **Inventory Management** - Track products, stock levels, and movements
- 💰 **Point of Sale** - Fast checkout with barcode scanning support
- 📈 **Financial Reports** - Revenue tracking, expense management, and profit/loss analysis
- 👥 **Party Management** - Handle customers, suppliers, and transactions
- 🧾 **Invoicing** - Generate and manage sales invoices
- 🤖 **AI Insights** - Business analytics powered by Gemini AI
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 15
- SQLAlchemy ORM
- Alembic migrations
- JWT authentication
- Pydantic validation

**Frontend:**
- Next.js 14
- TypeScript
- TailwindCSS
- React Query
- Axios

**Deployment:**
- Azure App Service (Docker containers)
- Azure Container Registry
- Azure Database for PostgreSQL
- GitHub Actions CI/CD

## Architecture

```
StockPilot/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── core/     # Configuration & security
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   ├── alembic/      # Database migrations
│   └── tests/        # Backend tests
│
├── frontend/         # Next.js frontend
│   ├── app/          # Pages (App Router)
│   ├── components/   # React components
│   ├── lib/          # Utilities & API client
│   └── hooks/        # Custom React hooks
│
└── .github/workflows/  # CI/CD pipelines
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL

# Start development server
npm run dev
```

Frontend runs at http://localhost:3000

## Deployment

### Azure Resources

The application is deployed on Azure using:
- **Resource Group**: `stockpilot-rg`
- **Container Registry**: `stockpilotacr.azurecr.io`
- **Backend API**: https://stockpilot-api.azurewebsites.net
- **Frontend Web**: https://stockpilot-web.azurewebsites.net
- **Database**: PostgreSQL Flexible Server (B1ms - Free tier)

### CI/CD Pipeline

GitHub Actions automatically deploys on push to `main` branch:

1. **Build** - Docker images are built using Azure ACR
2. **Push** - Images tagged with commit SHA and `latest`
3. **Deploy** - Web apps are restarted with new images

### Manual Deployment

```bash
# Build and push images
az acr build --registry stockpilotacr \
  --image stockpilot-backend:latest \
  --file backend/Dockerfile backend/

az acr build --registry stockpilotacr \
  --image stockpilot-frontend:latest \
  --file frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://stockpilot-api.azurewebsites.net \
  frontend/

# Restart apps
az webapp restart --name stockpilot-api --resource-group stockpilot-rg
az webapp restart --name stockpilot-web --resource-group stockpilot-rg
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Run via Azure SSH
az webapp ssh --name stockpilot-api --resource-group stockpilot-rg
cd /app && alembic upgrade head
```

## Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key
- `CORS_ORIGINS` - Allowed origins (comma-separated)
- `GEMINI_API_KEY` - Google Gemini AI key (optional)

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL

## API Documentation

Interactive API docs available at:
- Swagger UI: https://stockpilot-api.azurewebsites.net/docs
- ReDoc: https://stockpilot-api.azurewebsites.net/redoc

## License

Private - All Rights Reserved

## Contact

For issues or questions, contact: [Your Contact Info]
