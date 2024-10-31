from enum import Enum


class UserRole(str, Enum):
    COMPANY = "company"
    INDIVIDUAL = "user"

    @classmethod
    def from_str(cls, enum: str) -> "UserRole":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not a valid UserRole")


class UserGender(str, Enum):
    MAN = "Man"
    WOMAN = "Woman"
    OTHERS = "Others"

    @classmethod
    def from_str(cls, enum: str) -> "UserGender":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not a valid UserGender")


class UserMaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOW = "Widow"
    WIDOWER = "Widower"

    @classmethod
    def from_str(cls, enum: str) -> "UserMaritalStatus":
        try:
            return cls(enum)
        except ValueError:
            raise ValueError(f"'{enum}' is not a valid Marital Status")
