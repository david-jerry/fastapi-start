from enum import Enum


class TransactionStatus(str, Enum):
    CONFIRMED = "Confirmed"
    PENDING = "Pending"
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    REVERSED = "Reversed"

    @classmethod
    def from_str(cls, enum: str) -> "TransactionStatus":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not a valid TransactionStatus")


class TransactionPaymentType(str, Enum):
    DEBIT = "Debit"
    FUNDING = "Funding"
    WITHDRAWAL = "Withdrawal"
    EARNING = "Earning"

    @classmethod
    def from_str(cls, enum: str) -> "TransactionPaymentType":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not a valid Transaction Payment type")


class TransactionPaymentMethod(str, Enum):
    CREDITCARD = "CreditCard"
    BANKTRANSFER = "BankTransfer"
    PAYPAL = "Paypal"

    @classmethod
    def from_str(cls, enum: str) -> "TransactionPaymentMethod":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not an approved payment method")
