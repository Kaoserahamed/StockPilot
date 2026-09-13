from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth / Users (FR-1, FR-3) ----------
class RegisterRequest(BaseModel):
    owner_name: str = Field(min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    business_name: str = Field(min_length=1, max_length=255)
    business_address: Optional[str] = None
    business_phone: Optional[str] = None


class LoginRequest(BaseModel):
    username: str  # email or phone
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    username: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(pattern="^(Owner|Manager|Cashier)$")


class EmployeeOut(BaseModel):
    membership_id: int
    user: UserOut
    role: str
    is_active: bool


class EmployeeRoleUpdate(BaseModel):
    role: str = Field(pattern="^(Owner|Manager|Cashier)$")


# ---------- Business (FR-2) ----------
class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    currency: Optional[str] = "BDT"
    tax_rate: Optional[float] = 0.0


class BusinessOut(BaseModel):
    id: int
    name: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    logo_path: Optional[str]
    currency: str
    tax_rate: float
    invoice_format: str
    min_stock_default: int

    class Config:
        from_attributes = True


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    invoice_format: Optional[str] = None
    min_stock_default: Optional[int] = None


# ---------- Category (FR-4) ----------
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ---------- Product (FR-5) ----------
class ProductCreate(BaseModel):
    name: str
    sku: str
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    unit: str = "pcs"
    purchase_price: float = 0
    selling_price: float = 0
    min_stock: int = 5


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    min_stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    barcode: Optional[str]
    category_id: Optional[int]
    brand: Optional[str]
    unit: str
    purchase_price: float
    selling_price: float
    min_stock: int
    quantity_on_hand: int
    is_active: bool
    image_path: Optional[str]

    class Config:
        from_attributes = True


# ---------- Supplier / Customer (FR-6, FR-7) ----------
class SupplierCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class SupplierOut(SupplierCreate):
    id: int
    outstanding_balance: float
    is_active: bool

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    credit_limit: float = 0


class CustomerOut(CustomerCreate):
    id: int
    outstanding_balance: float
    is_active: bool

    class Config:
        from_attributes = True


# ---------- Inventory (FR-8, FR-9) ----------
class AdjustRequest(BaseModel):
    product_id: int
    quantity_change: int
    reason: str = Field(min_length=1)


class InventoryTxOut(BaseModel):
    id: int
    product_id: int
    quantity_change: int
    tx_type: str
    reason: Optional[str]
    user_id: Optional[int]
    related_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PriceAdjustRequest(BaseModel):
    """Optional-field price adjustment: provide sell price, cost price or both."""
    product_id: int
    new_selling_price: Optional[float] = Field(default=None, ge=0)
    new_purchase_price: Optional[float] = Field(default=None, ge=0)
    reason: str = Field(min_length=1)


class PriceAdjustmentOut(BaseModel):
    id: int
    product_id: int
    old_selling_price: float
    new_selling_price: float
    old_purchase_price: float
    new_purchase_price: float
    reason: str
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Purchases (FR-10) ----------
class PurchaseItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_cost: float = Field(ge=0)


class PurchaseCreate(BaseModel):
    supplier_id: int
    items: list[PurchaseItemIn] = Field(min_length=1)
    discount_amount: float = 0
    tax_amount: float = 0
    paid_amount: float = 0
    note: Optional[str] = None


class PurchaseItemOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_cost: float
    line_total: float

    class Config:
        from_attributes = True


class PurchaseOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    purchase_date: datetime
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    payment_status: str
    status: str
    note: Optional[str] = None
    items: list[PurchaseItemOut] = []

    class Config:
        from_attributes = True


class PurchasePayRequest(BaseModel):
    amount: float = Field(gt=0)


# ---------- Sales / POS (FR-11, FR-12, FR-13) ----------
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[float] = None  # default: product.selling_price
    discount: float = 0


class CheckoutRequest(BaseModel):
    items: list[CartItemIn] = Field(min_length=1)
    customer_id: Optional[int] = None
    discount_amount: float = 0
    tax_percent: float = 0
    paid_amount: Optional[float] = None  # default: full total
    payment_method: str = "cash"


class SaleItemOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    discount: float
    line_total: float
    returned_qty: int

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    invoice_no: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    subtotal: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    payment_method: str
    payment_status: str
    status: str
    created_at: datetime
    items: list[SaleItemOut] = []

    class Config:
        from_attributes = True


# ---------- Returns (FR-14) ----------
class ReturnItemIn(BaseModel):
    sale_item_id: int
    quantity: int = Field(gt=0)


class ReturnCreate(BaseModel):
    sale_id: int
    reason: str = Field(min_length=1)
    items: list[ReturnItemIn] = Field(min_length=1)


class ReturnOut(BaseModel):
    id: int
    sale_id: int
    reason: str
    refund_amount: float
    created_at: datetime


class EmployeeResetRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class SaleCancelRequest(BaseModel):
    reason: str = Field(min_length=1)


# ---------- Phase 4: business settings / subscriptions (FR-28, FR-29) ----------
class SettingsOut(BaseModel):
    currency: str
    tax_rate: float
    invoice_format: str
    min_stock_default: int
    business_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class SettingsUpdate(BaseModel):
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    invoice_format: Optional[str] = None
    min_stock_default: Optional[int] = None
    business_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    product_limit: int
    employee_limit: int
    product_count: int
    employee_count: int
    product_usage_pct: float
    employee_usage_pct: float
    near_limit: bool
    at_limit: bool
    message: Optional[str] = None

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    plan: str = Field(pattern="^(free|basic|pro)$")


# ---------- Phase 5: AI (FR-30..FR-37) ----------
class AIChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    save: bool = True


class AIChatResponse(BaseModel):
    answer: str
    data: dict
    recommendation_id: Optional[int] = None


class AISummaryRequest(BaseModel):
    kind: str = Field(pattern="^(sales|expenses|inventory|profit)$")
    preset: str = "month"


class AIRecommendationOut(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    reviewed: bool
    acted_upon: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AIRecommendationUpdate(BaseModel):
    reviewed: Optional[bool] = None
    acted_upon: Optional[bool] = None


# ---------- Expenses (FR-15) ----------
class ExpenseCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    amount: float = Field(gt=0)
    description: Optional[str] = None
    expense_date: Optional[datetime] = None
    payment_method: str = "cash"


class ExpenseUpdate(BaseModel):
    category: Optional[str] = Field(default=None, max_length=50)
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = None
    expense_date: Optional[datetime] = None
    payment_method: Optional[str] = None


class ExpenseOut(BaseModel):
    id: int
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: datetime
    payment_method: str
    created_at: datetime

    class Config:
        from_attributes = True
