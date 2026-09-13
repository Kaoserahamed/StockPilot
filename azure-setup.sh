#!/bin/bash
# Azure Infrastructure Setup Script for StockPilot
# This script creates all necessary Azure resources for deployment

set -e

# Configuration
RESOURCE_GROUP="stockpilot-rg"
LOCATION="southeastasia"
ACR_NAME="stockpilotacr"
APP_SERVICE_PLAN="stockpilot-plan"
BACKEND_APP_NAME="stockpilot-api"
FRONTEND_APP_NAME="stockpilot-web"
DB_SERVER_NAME="stockpilot-db"
DB_NAME="stockpilot"
DB_ADMIN_USER="stockpilot_admin"
POSTGRES_VERSION="15"

echo "======================================"
echo "StockPilot Azure Infrastructure Setup"
echo "======================================"
echo ""

# Check if user is logged in
if ! az account show &>/dev/null; then
    echo "❌ Not logged in to Azure. Please run: az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "📋 Using subscription: $SUBSCRIPTION_ID"
echo ""

# Create Resource Group
echo "📦 Creating resource group: $RESOURCE_GROUP"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

echo "✅ Resource group created"
echo ""

# Create Azure Container Registry
echo "🐳 Creating Azure Container Registry: $ACR_NAME"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --output none

echo "✅ Container Registry created"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
echo ""

# Create App Service Plan
echo "🖥️  Creating App Service Plan: $APP_SERVICE_PLAN"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1 \
  --output none

echo "✅ App Service Plan created"
echo ""

# Create PostgreSQL Flexible Server
echo "🗄️  Creating PostgreSQL Flexible Server: $DB_SERVER_NAME"
echo "⏳ This may take several minutes..."

# Generate a random password
DB_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --version $POSTGRES_VERSION \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255 \
  --output none

echo "✅ PostgreSQL server created"
echo ""

# Create database
echo "📊 Creating database: $DB_NAME"
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME \
  --output none

echo "✅ Database created"
echo ""

# Create Backend Web App
echo "🚀 Creating Backend Web App: $BACKEND_APP_NAME"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $BACKEND_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/stockpilot-backend:latest \
  --output none

# Configure Backend Web App
echo "⚙️  Configuring Backend Web App..."
DATABASE_URL="postgresql+psycopg2://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_SERVER_NAME}.postgres.database.azure.com:5432/${DB_NAME}?sslmode=require"
SECRET_KEY=$(openssl rand -base64 48)

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --settings \
    DATABASE_URL="$DATABASE_URL" \
    SECRET_KEY="$SECRET_KEY" \
    ENVIRONMENT="production" \
    CORS_ORIGINS="https://${FRONTEND_APP_NAME}.azurewebsites.net" \
    LOG_LEVEL="INFO" \
    JSON_LOGS="true" \
    ALGORITHM="HS256" \
    ACCESS_TOKEN_EXPIRE_MINUTES="15" \
    REFRESH_TOKEN_EXPIRE_DAYS="7" \
    UPLOAD_DIR="/home/uploads" \
    WEBSITES_PORT="8000" \
  --output none

# Configure ACR credentials for backend
az webapp config container set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/stockpilot-backend:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password "$ACR_PASSWORD" \
  --output none

echo "✅ Backend Web App configured"
echo ""

# Create Frontend Web App
echo "🌐 Creating Frontend Web App: $FRONTEND_APP_NAME"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $FRONTEND_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/stockpilot-frontend:latest \
  --output none

# Configure Frontend Web App
echo "⚙️  Configuring Frontend Web App..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $FRONTEND_APP_NAME \
  --settings \
    NEXT_PUBLIC_API_URL="https://${BACKEND_APP_NAME}.azurewebsites.net" \
    WEBSITES_PORT="3000" \
  --output none

# Configure ACR credentials for frontend
az webapp config container set \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/stockpilot-frontend:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password "$ACR_PASSWORD" \
  --output none

echo "✅ Frontend Web App configured"
echo ""

# Enable continuous deployment
echo "🔄 Enabling continuous deployment..."
az webapp deployment container config \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-cd true \
  --output none

az webapp deployment container config \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-cd true \
  --output none

echo "✅ Continuous deployment enabled"
echo ""

# Configure health checks
echo "💓 Configuring health checks..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --health-check-path "/health" \
  --output none

echo "✅ Health checks configured"
echo ""

# Get service principal credentials for GitHub Actions
echo "🔐 Creating service principal for GitHub Actions..."
SP_NAME="stockpilot-github-actions"
AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
  --name $SP_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo "✅ Service principal created"
echo ""

echo "======================================"
echo "✅ Azure Infrastructure Setup Complete!"
echo "======================================"
echo ""
echo "📝 IMPORTANT: Save these credentials securely!"
echo ""
echo "=== GitHub Secrets Required ==="
echo ""
echo "AZURE_CREDENTIALS:"
echo "$AZURE_CREDENTIALS"
echo ""
echo "ACR_USERNAME: $ACR_USERNAME"
echo ""
echo "ACR_PASSWORD: $ACR_PASSWORD"
echo ""
echo "NEXT_PUBLIC_API_URL: https://${BACKEND_APP_NAME}.azurewebsites.net"
echo ""
echo "=== Database Connection ==="
echo "DATABASE_URL: $DATABASE_URL"
echo ""
echo "=== Application URLs ==="
echo "Backend:  https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "Frontend: https://${FRONTEND_APP_NAME}.azurewebsites.net"
echo ""
echo "=== Next Steps ==="
echo "1. Add the GitHub secrets listed above to your repository"
echo "2. Build and push initial Docker images:"
echo "   docker build -t $ACR_NAME.azurecr.io/stockpilot-backend:latest ./backend"
echo "   docker build -t $ACR_NAME.azurecr.io/stockpilot-frontend:latest ./frontend"
echo "   docker push $ACR_NAME.azurecr.io/stockpilot-backend:latest"
echo "   docker push $ACR_NAME.azurecr.io/stockpilot-frontend:latest"
echo "3. Run database migrations on the backend app"
echo "4. Push code to trigger the GitHub Actions workflow"
echo ""
