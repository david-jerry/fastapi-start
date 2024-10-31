from datetime import datetime, timedelta
import random
import uuid
from itsdangerous import URLSafeTimedSerializer
import jwt  # type: ignore

from passlib.context import CryptContext
from pydantic import EmailStr  # type: ignore
from src.config.settings import Config
from src.utils.logger import LOGGER


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated='auto')


def generateHashKey(word: str) -> str:
    """
    The function `generateHashKey` takes a string input, hashes it using bcrypt, and returns the hashed
    value.

    :param word: The `generateHashKey` function takes a string `word` as input and generates a hash key
    using the `bcrypt_context.hash` function. The hash key is then returned as a string
    :type word: str
    :return: The function `generateHashKey` takes a string input `word`, hashes it using bcrypt, and
    returns the hashed value as a string.
    """
    hash = bcrypt_context.hash(word)
    return hash

def verifyHashKey(word: str, hash: str) -> bool:
    """
    The function `verifyHashKey` checks if a given word matches a given hash using bcrypt hashing.

    :param word: The `word` parameter is a string that represents the plaintext password that you want
    to verify against the hashed password
    :type word: str
    :param hash: The `hash` parameter in the `verifyHashKey` function is typically a hashed version of a
    password or some other sensitive information. It is used for comparison with the original plaintext
    value to verify its authenticity without storing the actual password in plain text
    :type hash: str
    :return: The function `verifyHashKey` is returning a boolean value indicating whether the provided
    `word` matches the `hash` value after verification using bcrypt.
    """
    correct = bcrypt_context.verify(word, hash)
    return correct

serializer = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY, salt="email-configuration"
)

def create_url_safe_token(data: dict):
    """
    The function `create_url_safe_token` generates a URL-safe token from a given dictionary using a
    serializer.

    :param data: A dictionary containing the data that needs to be serialized into a URL-safe token
    :type data: dict
    :return: A URL-safe token created by serializing the input data dictionary.
    """
    token = serializer.dumps(data)
    return token

def decode_url_safe_token(token: str):
    """
    The function `decode_url_safe_token` attempts to deserialize a token and return the decoded data,
    logging any exceptions that occur.

    :param token: The `decode_url_safe_token` function takes a `token` parameter, which is expected to
    be a string. The function attempts to decode the token using a serializer and returns the decoded
    token data if successful. If an exception occurs during the decoding process, the function logs the
    exception using a LOGGER object
    :type token: str
    :return: The function `decode_url_safe_token` is returning the decoded data from the token if
    successful. If an exception occurs during the decoding process, the function logs the exception
    using the LOGGER and does not return any data.
    """
    try:
        token_data = serializer.loads(token)
        return token_data
    except Exception as e:
        LOGGER.exception(str(e))

def create_access_token(
    user_data: dict, expiry: timedelta = None, refresh: bool = False
):
    """
    The function `create_access_token` generates a JWT access token with user data, expiry time, and
    refresh flag.

    :param user_data: The `user_data` parameter is a dictionary containing information about the user
    for whom the access token is being created. This information may include the user's ID, username,
    role, or any other relevant data needed for authentication and authorization purposes
    :type user_data: dict
    :param expiry: The `expiry` parameter in the `create_access_token` function is used to specify the
    duration for which the access token will be valid. It is of type `timedelta` and represents a time
    duration. If no `expiry` value is provided, the default expiry time is set to a predefined
    :type expiry: timedelta
    :param refresh: The `refresh` parameter in the `create_access_token` function is a boolean flag that
    indicates whether the access token being created is a refresh token or not. If `refresh` is set to
    `True`, it means that the access token being generated will be used for refreshing an expired token.
    If, defaults to False
    :type refresh: bool (optional)
    :return: The function `create_access_token` returns a JSON Web Token (JWT) that has been encoded
    using the provided payload, secret key, and algorithm.
    """
    payload = {}

    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
        expiry if expiry is not None else timedelta(seconds=Config.ACCESS_TOKEN_EXPIRY)
    )
    payload["jti"] = str(uuid.uuid4())

    payload["refresh"] = refresh

    token = jwt.encode(
        payload=payload, key=Config.SECRET_KEY, algorithm=Config.ALGORITHM
    )

    return token

def decode_token(token: str) -> dict:
    """
    The `decode_token` function decodes a JWT token using a secret key and algorithm specified in the
    Config class, handling any PyJWT errors that may occur.

    :param token: The `decode_token` function you provided seems to be a part of a larger codebase that
    involves decoding JWT tokens. In the function, it attempts to decode a JWT token using a secret key
    and algorithm specified in the `Config` class
    :type token: str
    :return: The `decode_token` function is returning a dictionary containing the decoded data from the
    token if decoding is successful. If there is an error during decoding (specifically a
    `jwt.PyJWTError`), it logs the exception and returns `None`.
    """
    try:
        token_data = jwt.decode(
            jwt=token, key=Config.SECRET_KEY, algorithms=[Config.ALGORITHM]
        )
        LOGGER.debug(token_data)
        return token_data
    except jwt.PyJWTError as e:
        LOGGER.exception(e)
        return None

def generate_verification_code() -> str:
    """
    The function generates a random 6-digit verification code for a given email address.

    :param email: The `generate_verification_code` function takes an email address as input and
    generates a random 6-digit verification code. The code is a string of 6 random digits
    :return: A verification code consisting of 6 random digits is being returned.
    """
    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
    return code

def generate_password_reset_code(email: EmailStr) -> str:
    """
    The function generates a random 6-digit verification code for a given email address.

    :param email: The `generate_verification_code` function takes an email address as input and
    generates a random 6-digit verification code. The code is a string of 6 random digits
    :return: A verification code consisting of 6 random digits is being returned.
    """
    code = create_url_safe_token({"email": email})
    return code

def generate_otp_code() -> str:
    """
    The function generates a 4-digit OTP code for a given email address.

    :param email: The `generate_otp_code` function takes an email address as input and generates a
    4-digit OTP (One Time Password) code. The code is a random sequence of 4 digits (0-9) and is
    returned as a string
    :return: A 4-digit random OTP (One Time Password) code is being returned.
    """
    code = ''.join(str(random.randint(0, 9)) for _ in range(4))
    return code
