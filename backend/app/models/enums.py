import enum


class Role(str, enum.Enum):
    OWNER = "Owner"
    MANAGER = "Manager"
    CASHIER = "Cashier"


class InventoryTxType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
