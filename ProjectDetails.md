# Functional Requirements

## Inventory & POS SaaS for Small Businesses

### Phase 1 — Core Business & Inventory Management

### FR-1: User Registration and Authentication

1. The system shall allow a new business owner to register an account.
2. The system shall collect the owner's name, email/phone, password, and business information during registration.
3. The system shall authenticate users using valid credentials.
4. The system shall allow authenticated users to log out.
5. The system shall provide password reset functionality.
6. The system shall prevent access to protected resources by unauthenticated users.
7. The system shall maintain user session/token information securely.

### FR-2: Business Management

1. The system shall allow an authenticated owner to create a business profile.
2. The system shall store business name, address, contact information, logo, and other basic information.
3. The system shall associate users and business data with the corresponding business.
4. The system shall allow the owner to update business information.
5. The system shall prevent users from accessing data belonging to another business.

### FR-3: User and Role Management

1. The system shall allow the business owner to create employee accounts.
2. The system shall support predefined roles such as:

   * Owner
   * Manager
   * Cashier
3. The system shall assign a role to each employee.
4. The system shall restrict system operations according to the user's role.
5. The owner shall be able to activate, deactivate, or remove employee accounts.

### FR-4: Category Management

1. The system shall allow authorized users to create product categories.
2. The system shall allow authorized users to update categories.
3. The system shall allow authorized users to deactivate categories.
4. The system shall prevent deletion of categories that are associated with existing products unless appropriate reassignment is performed.

### FR-5: Product Management

1. The system shall allow authorized users to create products.
2. Each product shall contain, at minimum:

   * Product name
   * SKU
   * Barcode
   * Category
   * Brand
   * Unit
   * Purchase price
   * Selling price
   * Minimum stock level
   * Current availability status
3. The system shall allow users to upload a product image.
4. The system shall allow authorized users to update product information.
5. The system shall allow authorized users to deactivate products.
6. The system shall support product search by name, SKU, barcode, brand, and category.
7. The system shall prevent duplicate SKUs and barcodes within the same business.

### FR-6: Supplier Management

1. The system shall allow authorized users to create supplier records.
2. Supplier records shall contain company name, contact person, phone number, email, and address.
3. The system shall allow suppliers to be updated or deactivated.
4. The system shall maintain purchase history for each supplier.
5. The system shall calculate outstanding supplier balances where applicable.

### FR-7: Customer Management

1. The system shall allow authorized users to create customer records.
2. Customer records shall contain name, phone number, email, address, and optional credit information.
3. The system shall allow customer information to be updated.
4. The system shall maintain each customer's sales history.
5. The system shall calculate outstanding customer balances where credit sales are supported.

### FR-8: Inventory Management

1. The system shall maintain current stock quantities for every product.
2. The system shall increase inventory when a purchase is completed.
3. The system shall decrease inventory when a sale is completed.
4. The system shall update inventory for product returns.
5. The system shall allow authorized users to record manual stock adjustments.
6. The system shall record the reason for each manual adjustment.
7. The system shall maintain an inventory transaction history.
8. Inventory transactions shall identify the product, quantity, transaction type, user, timestamp, and related transaction where applicable.

### FR-9: Inventory Status

1. The system shall identify products whose stock is below the configured minimum level.
2. The system shall identify out-of-stock products.
3. The system shall display current available quantity for each product.
4. The system shall provide an inventory overview to authorized users.
5. The system shall allow inventory to be filtered by category, status, and stock condition.

---

# Phase 2 — Purchase & POS/Sales Management

### FR-10: Purchase Management

1. The system shall allow authorized users to create purchase orders/records.
2. A purchase shall contain:

   * Supplier
   * Purchase date
   * Purchased products
   * Quantity
   * Unit purchase price
   * Total amount
   * Payment status
3. The system shall allow multiple products to be included in one purchase.
4. The system shall calculate subtotal and total purchase value automatically.
5. The system shall update stock when a purchase is confirmed.
6. The system shall maintain purchase history by supplier.
7. The system shall allow authorized users to view individual purchase details.
8. The system shall track paid and outstanding supplier amounts.

### FR-11: Point of Sale (POS)

1. The system shall provide a dedicated POS interface.
2. Authorized cashiers and managers shall be able to search for products.
3. The POS shall support product selection by:

   * Product name
   * SKU
   * Barcode
4. The system shall allow a cashier to add multiple products to a cart.
5. The system shall allow quantity modification or removal of cart items.
6. The system shall calculate item subtotal, cart subtotal, discount, tax, and final payable amount.
7. The system shall prevent the sale of quantities greater than available stock.
8. The system shall allow a customer to be associated with a sale.
9. The system shall support multiple payment methods.
10. The system shall create a unique invoice number for every completed sale.

### FR-12: Sales Processing

1. The system shall create a sales transaction when checkout is completed.
2. The system shall store all products and quantities included in the sale.
3. The system shall automatically reduce corresponding inventory quantities.
4. The system shall record the employee who processed the sale.
5. The system shall record the payment method and payment status.
6. The system shall calculate the total sale amount automatically.
7. The system shall maintain sales history.
8. The system shall allow authorized users to search and filter sales.

### FR-13: Invoice Management

1. The system shall generate an invoice for every completed sale.
2. The invoice shall include:

   * Business information
   * Invoice number
   * Date/time
   * Customer information where available
   * Purchased items
   * Quantity
   * Unit price
   * Discount
   * Total
   * Payment method
3. The system shall allow authorized users to view an invoice.
4. The system shall support invoice printing.
5. The system shall support invoice download in PDF format.

### FR-14: Sales Return

1. The system shall allow authorized users to initiate a product return.
2. The system shall identify the original sale associated with the return.
3. The system shall allow full or partial item returns.
4. The system shall increase inventory when a valid return is completed.
5. The system shall record the reason for the return.
6. The system shall adjust the corresponding financial transaction.

---

# Phase 3 — Financial Management & Business Analytics

### FR-15: Expense Management

1. The system shall allow authorized users to create expense records.
2. Expenses shall contain:

   * Expense category
   * Amount
   * Description
   * Date
   * Payment method
3. The system shall support categories such as rent, salary, electricity, transport, maintenance, and miscellaneous expenses.
4. The system shall allow authorized users to update or remove expense records.
5. The system shall maintain an expense history.

### FR-16: Revenue Calculation

1. The system shall calculate total sales revenue for a selected period.
2. The system shall support daily, weekly, monthly, yearly, and custom date-range calculations.
3. The system shall exclude cancelled transactions from completed revenue calculations.
4. The system shall provide revenue trends over time.

### FR-17: Cost of Goods Sold (COGS)

1. The system shall calculate the cost associated with sold products.
2. The system shall use recorded purchase costs to determine product cost.
3. The system shall calculate COGS for selected periods.
4. The system shall provide product-level and overall COGS information.

### FR-18: Profit Calculation

1. The system shall calculate gross profit.
2. Gross profit shall be derived from revenue minus COGS.
3. The system shall calculate total operational expenses.
4. The system shall calculate net profit as applicable.
5. The system shall provide profit information for configurable date ranges.

### FR-19: Dashboard

1. The system shall provide a business dashboard for authorized users.
2. The dashboard shall display key indicators including:

   * Total sales
   * Number of orders
   * Revenue
   * Gross profit
   * Net profit
   * Expenses
   * Current inventory value
3. The dashboard shall display sales trends using charts.
4. The dashboard shall display top-selling products.
5. The dashboard shall display low-stock and out-of-stock products.
6. Dashboard data shall respect the user's business and role permissions.

### FR-20: Product Performance Analytics

1. The system shall calculate sales quantity by product.
2. The system shall calculate revenue generated by each product.
3. The system shall calculate estimated profit generated by each product.
4. The system shall identify best-selling products.
5. The system shall identify low-performing products.
6. The system shall allow product performance to be filtered by date range.

### FR-21: Customer Analytics

1. The system shall calculate total purchase value for each customer.
2. The system shall calculate the number of purchases made by each customer.
3. The system shall identify frequently returning customers.
4. The system shall identify top customers by spending.
5. The system shall display customer purchase history.

### FR-22: Supplier Analytics

1. The system shall maintain total purchase value per supplier.
2. The system shall display supplier purchase history.
3. The system shall display outstanding supplier balances where applicable.
4. The system shall allow supplier activity to be filtered by date range.

### FR-23: Reports

1. The system shall generate sales reports.
2. The system shall generate inventory reports.
3. The system shall generate purchase reports.
4. The system shall generate expense reports.
5. The system shall generate profit reports.
6. The system shall support date-based filtering.
7. The system shall support report export in CSV/Excel format.
8. The system shall support PDF report generation.

---

# Phase 4 — Multi-Tenant SaaS, RBAC & Business Administration

### FR-24: Multi-Tenant Business Architecture

1. The system shall support multiple independent businesses.
2. Each business shall have isolated business data.
3. Each user shall belong to one or more authorized business contexts as defined by the application.
4. All business-related records shall be associated with a business identifier.
5. Users shall only be able to access data belonging to businesses for which they have permission.
6. The system shall prevent cross-business access through both frontend and backend authorization checks.

### FR-25: Role-Based Access Control

1. The system shall enforce permissions on protected APIs.
2. The system shall restrict product management to authorized roles.
3. The system shall restrict employee management to owners or designated administrators.
4. The system shall restrict financial reports to authorized roles.
5. The system shall allow cashiers to process sales without granting unrestricted administrative access.
6. The system shall reject unauthorized API requests.

### FR-26: Employee Management

1. The owner shall be able to create employee accounts.
2. The owner shall be able to assign employee roles.
3. The owner shall be able to deactivate employees.
4. The owner shall be able to reset employee access where applicable.
5. The system shall maintain employee activity associated with sales, purchases, inventory adjustments, and other critical actions.

### FR-27: Audit Logging

1. The system shall record critical user actions.
2. Audit records shall include:

   * User
   * Action
   * Resource
   * Previous value where applicable
   * New value where applicable
   * Timestamp
3. The system shall record important actions such as:

   * Product price changes
   * Inventory adjustments
   * Sale cancellation
   * Purchase modification
   * Employee changes
4. Authorized administrators shall be able to view audit logs.
5. Audit records shall not be modifiable through normal application operations.

### FR-28: Business Settings

1. The system shall allow owners to configure business information.
2. The system shall allow configuration of:

   * Currency
   * Tax rate
   * Invoice format
   * Minimum stock defaults
   * Business contact information
3. The system shall allow owners to update these settings.
4. The system shall apply configured settings to relevant calculations and documents.

### FR-29: Subscription Management

1. The system shall support multiple SaaS subscription plans.
2. Each plan shall define feature and usage limits.
3. The system shall identify the business's current subscription plan.
4. The system shall enforce plan-based limits where applicable.
5. The system shall notify the owner when limits are reached or nearly reached.
6. Authorized users shall be able to view subscription status.

---

# Phase 5 — AI & Machine Learning Features

### FR-30: AI Business Assistant

1. The system shall provide an AI-powered business assistant.
2. Authorized users shall be able to submit natural-language business questions.
3. The system shall retrieve relevant business data before generating an answer.
4. The assistant shall be able to answer questions related to:

   * Sales
   * Revenue
   * Profit
   * Expenses
   * Products
   * Inventory
   * Customers
   * Suppliers
5. The assistant shall respect the user's business and role permissions.
6. The assistant shall not expose data belonging to another business.
7. The assistant shall provide responses based on current or selected historical business data.
8. The system shall maintain conversation history where enabled.

### FR-31: Natural-Language Business Queries

The system shall support queries such as:

* "What were my total sales this month?"
* "Which products sold the most?"
* "Why did profit decrease compared with last month?"
* "Which products are running low?"
* "Who are my top customers?"
* "Which supplier did I purchase the most from?"
* "What were my largest expenses this month?"

### FR-32: AI Business Insights

1. The system shall automatically generate business insights from available data.
2. The system shall identify significant sales changes.
3. The system shall identify unusual expenses or sales patterns.
4. The system shall identify products with significant changes in demand.
5. The system shall summarize important business trends.
6. The system shall present AI-generated insights through the dashboard.

### FR-33: Demand Forecasting

1. The system shall use historical sales data to estimate future product demand.
2. The system shall allow forecasting for selected products.
3. The system shall support configurable forecast periods.
4. The system shall display predicted demand values.
5. The system shall display historical versus predicted demand.
6. The system shall use available historical transaction data as model input.

### FR-34: Reorder Recommendation

1. The system shall calculate recommended reorder quantities.
2. Recommendations shall consider factors such as:

   * Current stock
   * Historical sales
   * Sales velocity
   * Minimum stock level
   * Predicted demand
3. The system shall identify products that may require replenishment.
4. The system shall display the recommended reorder quantity.
5. The system shall allow authorized users to review recommendations before creating a purchase.

### FR-35: Sales Anomaly Detection

1. The system shall identify unusual changes in sales patterns.
2. The system shall compare current activity with historical patterns.
3. The system shall flag potentially abnormal transactions or trends.
4. The system shall present detected anomalies to authorized users.
5. The system shall provide supporting information for each detected anomaly.

### FR-36: AI Report Summarization

1. The system shall allow authorized users to generate AI summaries of business reports.
2. The system shall summarize selected sales, expense, inventory, or profit reports.
3. The system shall highlight major positive and negative trends.
4. The system shall provide concise natural-language explanations of report data.
5. The system shall distinguish generated insights from raw financial records.

### FR-37: AI Recommendation History

1. The system shall optionally store generated AI recommendations.
2. The system shall associate recommendations with the relevant business.
3. Authorized users shall be able to review previous AI recommendations.
4. The system shall record when recommendations were generated.
5. The system shall allow users to mark recommendations as reviewed or acted upon.

---

# Phase 5 End-to-End Functional Workflow

A complete business workflow shall operate as follows:

```text
Business Registration
        ↓
Create Users / Roles
        ↓
Create Categories
        ↓
Create Products
        ↓
Add Suppliers
        ↓
Create Purchase
        ↓
Inventory Updated
        ↓
Customer Purchases Product
        ↓
POS Checkout
        ↓
Invoice Generated
        ↓
Inventory Reduced
        ↓
Financial Records Updated
        ↓
Dashboard Updated
        ↓
Reports Generated
        ↓
AI Analyzes Business Data
        ↓
Demand Forecast
        ↓
Reorder Recommendation
```

# Functional Scope by Phase

| Phase       | Primary Functional Scope                                                                              |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| **Phase 1** | Authentication, business, users, roles, products, categories, customers, suppliers, inventory         |
| **Phase 2** | Purchases, POS, sales, invoices, returns                                                              |
| **Phase 3** | Expenses, revenue, COGS, profit, dashboard, analytics, reports                                        |
| **Phase 4** | Multi-tenancy, RBAC, employees, audit logs, business settings, subscriptions                          |
| **Phase 5** | AI assistant, AI insights, demand forecasting, reorder recommendations, anomaly detection, AI reports |

# Core Actors

The main actors of the system shall be:

```text
1. Business Owner
2. Manager
3. Cashier
4. AI Assistant
5. System Administrator
```

| Layer           | Technology                        |
| --------------- | --------------------------------- |
| Frontend        | **Next.js + TypeScript**          |
| Styling         | **Tailwind CSS + shadcn/ui**      |
| Data fetching   | **TanStack Query**                |
| Charts          | **Recharts**                      |
| Backend         | **FastAPI + Python**              |
| ORM             | **SQLAlchemy**                    |
| Database        | **PostgreSQL**                    |
| Database GUI    | **pgAdmin**                       |
| Authentication  | **JWT + bcrypt/passlib**          |
| Validation      | **Pydantic**                      |
| AI              | **Gemini API**                    |
| ML              | **Pandas + NumPy + Scikit-learn** |
| File storage    | **Local filesystem** initially    |
| PDF             | **ReportLab**                     |
| Excel/CSV       | **Pandas + OpenPyXL**             |
| Testing         | **Pytest + Playwright**           |
| Version control | **Git + GitHub**                  |

