#!/bin/bash
# Complete deployment setup script for StockPilot
set -e

echo "======================================"
echo "StockPilot - Azure Deployment Setup"
echo "======================================"
echo ""

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
GITHUB_REPO="Kaoserahamed/StockPilot"

# Step 1: Azure Login
echo "🔐 Step 1: Azure Authentication"
if ! az account show &>/dev/null; then
    echo "Please log in to Azure..."
    az login
fi
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✅ Using subscription: $SUBSCRIPTION_ID"
echo ""

# Step 2: Create Resource Group
echo "📦 Step 2: Creating Resource Group"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo "✅ Resource group created: $RESOURCE_GROUP"
echo ""

# Step 3: Create Azure Container Registry
echo "🐳 Step 3: Creating Azure Container Registry"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --output none
echo "✅ ACR created: $ACR_NAME"
echo ""

# Step 4: Create App Service Plan
echo "🖥️  Step 4: Creating App Service Plan"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1 \
  --output none
echo "✅ App Service Plan created"
echo ""

# Step 5: Create PostgreSQL Database
echo "🗄️  Step 5: Creating PostgreSQL Server"
DB_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --version 15 \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255 \
  --output none

az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME \
  --output none
echo "✅ PostgreSQL server and database created"
echo ""

# Step 6: Create Backend Web App
echo "🚀 Step 6: Creating Backend Web App"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $BACKEND_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/stockpilot-backend:latest \
  --output none

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

ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az webapp config container set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/stockpilot-backend:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password "$ACR_PASSWORD" \
  --output none

az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --health-check-path "/health" \
  --output none

echo "✅ Backend Web App configured"
echo ""

# Step 7: Create Frontend Web App
echo "🌐 Step 7: Creating Frontend Web App"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $FRONTEND_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/stockpilot-frontend:latest \
  --output none

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $FRONTEND_APP_NAME \
  --settings \
    NEXT_PUBLIC_API_URL="https://${BACKEND_APP_NAME}.azurewebsites.net" \
    WEBSITES_PORT="3000" \
  --output none

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

# Step 8: Create Service Principal for GitHub Actions
echo "🔑 Step 8: Creating Service Principal for GitHub Actions"
AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
  --name "stockpilot-github-actions" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)
echo "✅ Service Principal created"
echo ""

# Step 9: Set up GitHub Secrets
echo "🔐 Step 9: Setting up GitHub Secrets"
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI not found. Install from: https://cli.github.com/"
    echo "After installation, run the following commands manually:"
    echo ""
    echo "gh auth login"
    echo "echo '$AZURE_CREDENTIALS' | gh secret set AZURE_CREDENTIALS --repo $GITHUB_REPO"
    echo ""
else
    if ! gh auth status &>/dev/null; then
        echo "Authenticating with GitHub..."
        gh auth login
    fi
    
    echo "$AZURE_CREDENTIALS" | gh secret set AZURE_CREDENTIALS --repo $GITHUB_REPO
    echo "✅ GitHub secrets configured"
fi
echo ""

# Step 10: Build and Push Initial Images
echo "🏗️  Step 10: Building and Pushing Initial Docker Images"
az acr build \
  --registry $ACR_NAME \
  --image stockpilot-backend:latest \
  --file backend/Dockerfile \
  backend/

az acr build \
  --registry $ACR_NAME \
  --image stockpilot-frontend:latest \
  --file frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://${BACKEND_APP_NAME}.azurewebsites.net \
  frontend/

echo "✅ Initial images built and pushed"
echo ""

# Step 11: Restart Web Apps
echo "🔄 Step 11: Restarting Web Apps"
az webapp restart --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --output none
az webapp restart --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --output none
echo "✅ Web Apps restarted"
echo ""

echo "======================================"
echo "✅ Deployment Setup Complete!"
echo "======================================"
echo ""
echo "📝 Configuration Summary:"
echo ""
echo "Resource Group:    $RESOURCE_GROUP"
echo "Location:          $LOCATION"
echo "ACR:              $ACR_NAME.azurecr.io"
echo ""
echo "🌐 Application URLs:"
echo "Frontend:  https://${FRONTEND_APP_NAME}.azurewebsites.net"
echo "Backend:   https://${BACKEND_APP_NAME}.azurewebsites.net"
echo ""
echo "🔐 Database Connection (save securely):"
echo "Server:    ${DB_SERVER_NAME}.postgres.database.azure.com"
echo "Database:  $DB_NAME"
echo "Username:  $DB_ADMIN_USER"
echo "Password:  $DB_ADMIN_PASSWORD"
echo ""
echo "🚀 Next Steps:"
echo "1. Run database migrations:"
echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   cd /app && alembic upgrade head"
echo ""
echo "2. Set up Git remote and push code:"
echo "   git remote add origin https://github.com/$GITHUB_REPO.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. GitHub Actions will automatically deploy on push to main branch"
echo ""
