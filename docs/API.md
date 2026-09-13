# StockPilot API Documentation

## Overview

StockPilot is a multi-tenant Inventory & POS SaaS platform. This document provides
complete API reference for integration and development.

- **Base URL**: `https://your-domain.com/api/v1`
- **Protocol**: HTTPS only
- **Format**: JSON
- **Version**: v1

---

## Authentication

All endpoints (except auth) require a Bearer token:

```
Authorization: Bearer <access_token>
X-Business-Id: <business_id>
```

### Token Refresh
Access tokens expire in **15 minutes**. Use the refresh token to get a new pair:

```
POST /api/v1/auth/refresh
{"refresh_token": "<your_refresh_token>"}
```

Response includes a new `access_token` and `refresh_token`.

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Default | 100/minute |
| Auth (login/register) | 5/minute |
| AI endpoints | 10/minute |
| Reports | 20/minute |

---

## Error Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": 422,
    "message": "Request validation failed",
    "details": { "fields": [...] }
  }
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 504 | Request Timeout |

---

## Versioning

The API uses URL-based versioning: `/api/v1/`. Deprecated versions will be
supported for 6 months with warnings in response headers.

---

## Endpoints

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account + business |
| POST | `/auth/login` | Login, get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout (client discards) |
| GET | `/auth/me` | Current user info |

### Products
| Method | Path | Description |
|--------|------|-------------|
| GET | `/products` | List (paginated, filterable) |
| POST | `/products` | Create product |
| GET | `/products/{id}` | Get single |
| PATCH | `/products/{id}` | Update |
| POST | `/products/{id}/deactivate` | Soft delete |
| POST | `/products/{id}/activate` | Reactivate |

### Sales
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sales/checkout` | Create sale |
| GET | `/sales` | List sales |
| GET | `/sales/{id}` | Get sale details |
| POST | `/sales/{id}/cancel` | Cancel + restock |
| GET | `/pos/search` | POS product search |

### Inventory
| Method | Path | Description |
|--------|------|-------------|
| GET | `/inventory/overview` | Stock overview |
| GET | `/inventory/low-stock` | Low stock alerts |
| POST | `/inventory/adjust` | Stock adjustment |
| POST | `/inventory/adjust-price` | Price change |

### Finance
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | Dashboard metrics |
| GET | `/analytics/top-products` | Best sellers |
| GET | `/analytics/customer-stats` | Customer analytics |

### AI
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/chat` | Ask AI assistant |
| GET | `/ai/insights` | Get insights |

---

## Postman Collection

Import `stockpilot-api.postman_collection.json` from this directory into Postman
to get started quickly.

