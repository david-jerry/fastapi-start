from typing import Any, Callable
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status
from pydantic_core import ValidationError

def get_ip_address(request: Request):
    ip = request.headers.get("next-ip")

    if ip is None and request.url.hostname in ["localhost", "api.jeremiahedavid.online", "api.jeremiahedavid.com.ng"]:
        ip = request.headers.get("X-Forwarded-For")
        if ip:
            ip = ip.split(',')[0].strip()  # Use the first IP in the chain (the client)
        else:
            ip = request.headers.get("X-Real-IP", request.client.host)

    return ip or "127.0.0.1"



class NextStocksException(Exception):
    """Next exceptions class for all NextStock Errors."""
    pass


# Token and Authentication Errors
class InvalidToken(NextStocksException):
    """User has provided an invalid or expired token."""
    pass


class RevokedToken(NextStocksException):
    """User has provided a token that has been revoked."""
    pass


class AccessTokenRequired(NextStocksException):
    """User has provided a refresh token when an access token is needed."""
    pass


class RefreshTokenRequired(NextStocksException):
    """User has provided an access token when a refresh token is needed."""
    pass


# FAQ-related Errors
class FAQNotFound(NextStocksException):
    """Faq not found"""
    pass


class TestimonialNotFound(NextStocksException):
    """Testimonial not found"""
    pass


class ProjectNotFound(NextStocksException):
    """Project not found"""
    pass


class ServiceNotFound(NextStocksException):
    """Service not found"""
    pass


class RequestNotFound(NextStocksException):
    """Service Request not found"""
    pass


class MilestoneNotFound(NextStocksException):
    """Milestone not found"""
    pass


# User-related Errors
class UserAlreadyExists(NextStocksException):
    """User has provided an email for a user who exists during sign up."""
    pass


class PasswordsDoNotMatch(NextStocksException):
    """Passwords do not match."""
    pass


class UserNotFound(NextStocksException):
    """User not found."""
    pass


class UnknownIpConflict(NextStocksException):
    """A new ip address has accessed your account."""
    pass


class BannedIp(NextStocksException):
    """This ip has been banned for a specific user."""
    pass


class ProxyConflict(NextStocksException):
    """You might be hiding behind a proxy or VPN."""
    pass


class UserBlocked(NextStocksException):
    """This user has been blocked due to suspicious attempts to login from a new IP address."""
    pass


class InvalidCredentials(NextStocksException):
    """User has provided wrong email or password during log in."""
    pass


class InsufficientPermission(NextStocksException):
    """User does not have the necessary permissions to perform an action."""
    pass


class AccountNotVerified(NextStocksException):
    """Account not yet verified."""
    pass


# Transaction-related Errors
class TransactionNotFound(NextStocksException):
    """Transaction not found."""
    pass


class InvalidTransactionPin(NextStocksException):
    """You have inputted a wrong transfer pin."""
    pass


class InvalidTransactionAmount(NextStocksException):
    """Invalid transaction amount specified."""
    pass


class BankAccountNotFound(NextStocksException):
    """Bank account not found."""
    pass


class InsufficientFunds(NextStocksException):
    """Bank account has insufficient funds."""
    pass


# New Error Classes for Additional Scenarios
class AnalysisDataUnavailable(NextStocksException):
    """Requested analysis data is unavailable."""
    pass


class PageViewDataUnavailable(NextStocksException):
    """Requested page view data is unavailable."""
    pass


class IPConflictDetected(NextStocksException):
    """Multiple or conflicting IPs detected from a user."""
    pass


class PortfolioAssetUnavailable(NextStocksException):
    """Requested portfolio asset is unavailable for trading."""
    pass


class InsufficientPortfolioBalance(NextStocksException):
    """Portfolio balance is less than the required amount to perform trade."""
    pass


# User-related Errors
class CardNotFound(NextStocksException):
    """Debit Card not found."""
    pass


class CardAlreadyExists(NextStocksException):
    """Card Already Exists"""
    pass


class WrongCvv(NextStocksException):
    """Wrong card CVV number."""
    pass


class FormDataRequired(NextStocksException):
    """Form Data Required."""
    pass


# Exception handler generator
def create_exception_handler(
    status_code: int, initial_detail: Any
) -> Callable[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, exc: NextStocksException):
        return JSONResponse(content=initial_detail, status_code=status_code)

    return exception_handler


# Register all error handlers
def register_all_errors(app: FastAPI):
    # User-related Error Handlers
    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError):
        error_messages = []
        for error in exc.errors():
            message = error["msg"]
            input = error["input"][0]
            error_messages.append({f"{input}": f"{message}"})

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "model field errors",
                "source_errors": jsonable_encoder(error_messages),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(request: Request, exc: RequestValidationError):
        error_messages = []
        for error in exc.errors():
            field = error["loc"][-1]  # Get the field name
            message = error["msg"]
            error_messages.append({f"{field}": f"{message}"})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": jsonable_encoder(error_messages),
                "source_errors": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(ResponseValidationError)
    async def response_validation_error(request: Request, exc: ResponseValidationError):
        error_messages = []
        for error in exc.errors():
            field = error["loc"][-1]  # Get the field name
            message = error["msg"]
            error_messages.append({f"{field}": f"{message}"})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Response errors",
                "source_errors": jsonable_encoder(error_messages),
            },
        )

    @app.exception_handler(UnknownIpConflict)
    async def UnknownIpConflictError(request: Request, exc: UnknownIpConflict):
        ip = get_ip_address(request)
        return JSONResponse(
            status_code=status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED,
            content={"message": f"Unknown Ip Address: {ip}", "ip":ip, "error_code": "proxy_conflict"}
        )

    @app.exception_handler(BannedIp)
    async def BannedIpError(request: Request, exc: BannedIp):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Banned Ip Address", "error_code": "banned_ip"}
        )

    @app.exception_handler(InvalidToken)
    async def InvalidTokenError(request: Request, exc: InvalidToken):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Token is invalid or expired.", "error_code": "invalid_token"}
        )

    @app.exception_handler(RevokedToken)
    async def RevokedTokenError(request: Request, exc: RevokedToken):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Token is invalid or has been revoked.", "error_code": "token_revoked"}
        )

    @app.exception_handler(AccessTokenRequired)
    async def AccessTokenRequiredError(request: Request, exc: AccessTokenRequired):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Please provide a valid access token.", "error_code": "access_token_required"}
        )

    @app.exception_handler(AccountNotVerified)
    async def AccountNotVerifiedError(request: Request, exc: AccountNotVerified):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Please verify your email address.", "error_code": "account_not_verified"}
        )

    @app.exception_handler(FormDataRequired)
    async def FormDataRequiredError(request: Request, exc: FormDataRequired):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Please provide a body/data to submit into the form.", "error_code": "account_not_verified"}
        )

    @app.exception_handler(RefreshTokenRequired)
    async def RefreshTokenRequiredError(request: Request, exc: RefreshTokenRequired):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Please provide a valid refresh token.", "error_code": "refresh_token_required"}
        )

    @app.exception_handler(InsufficientPermission)
    async def InsufficientPermissionError(request: Request, exc: InsufficientPermission):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized access restricted.", "error_code": "unauthorized_access"}
        )

    @app.exception_handler(InvalidCredentials)
    async def InvalidCredentialsError(request: Request, exc: InvalidCredentials):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password.", "error_code": "invalid_email_or_password"}
        )

    @app.exception_handler(UserBlocked)
    async def UserBlockedError(request: Request, exc: UserBlocked):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "This account has been blocked.", "error_code": "user_blocked"}
        )

    @app.exception_handler(UserAlreadyExists)
    async def UserAlreadyExistsError(request: Request, exc: UserAlreadyExists):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "User with this email already exists", "error_code": "user_already_exist"}
        )

    @app.exception_handler(UserNotFound)
    async def UserNotFoundError(request: Request, exc: UserNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "User does not exist", "error_code": "user_not_found"}
        )

    @app.exception_handler(FAQNotFound)
    async def FAQNotFoundError(request: Request, exc: FAQNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "FAQ does not exist", "error_code": "faq_not_found"}
        )

    @app.exception_handler(FAQNotFound)
    async def ProjectNotFoundError(request: Request, exc: FAQNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Project does not exist", "error_code": "project_not_found"}
        )

    @app.exception_handler(ServiceNotFound)
    async def ServiceNotFoundError(exec: ServiceNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Service does not exist", "error_code": "service_not_found"}
        )

    @app.exception_handler(RequestNotFound)
    async def RequestNotFoundError(exec: RequestNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Service request does not exist", "error_code": "requested_service_not_found"}
        )

    @app.exception_handler(MilestoneNotFound)
    async def MilestoneNotFoundError(exec: MilestoneNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Milestone does not exist", "error_code": "milestone_not_found"}
        )

    @app.exception_handler(FAQNotFound)
    async def TestimonialNotFoundError(request: Request, exc: FAQNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Testimonial does not exist", "error_code": "testimonial_not_found"}
        )

    @app.exception_handler(ProxyConflict)
    async def ProxyConflictError(request: Request, exc: ProxyConflict):
        ip = get_ip_address(request)
        return JSONResponse(
            status_code=status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED,
            content={"message": "You are probably hiding behind a proxy (VPN) as such we could not determine your ip address", "ip": ip, "error_code": "proxy_conflict"}
        )

    @app.exception_handler(CardNotFound)
    async def CardNotFoundError(request: Request, exc: CardNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "This card does not exist", "error_code": "card_not_found"}
        )

    @app.exception_handler(CardAlreadyExists)
    async def CardAlreadyExistsError(request: Request, exc: CardAlreadyExists):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "This card already exists", "error_code": "card_exists"}
        )

    @app.exception_handler(PasswordsDoNotMatch)
    async def PasswordsDoNotMatchError(request: Request, exc: PasswordsDoNotMatch):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Password is incorrect", "error_code": "incorrect_password"}
        )
