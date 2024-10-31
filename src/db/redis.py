from typing import Optional
import uuid
import redis.asyncio as aioredis
from src.config.settings import (
    broker_url,
)
from src.utils.logger import LOGGER

# Redis connection pool settings
REDIS_POOL_SIZE = 10
REDIS_TIMEOUT = 5
JTI_EXPIRY = 3600
VERIFICATION_CODE_EXPIRY = 900  # 15 minutes
SECURITY_EXPIRY = 2592000  # 1 month

# Initialize Redis with connection pooling
redis_pool = aioredis.ConnectionPool.from_url(
    broker_url, max_connections=REDIS_POOL_SIZE, socket_timeout=REDIS_TIMEOUT
)
redis_client = aioredis.Redis(connection_pool=redis_pool)


# Password Reset Code
async def store_password_reset_code(
    user_id: uuid.UUID, code: str, expiry: int = VERIFICATION_CODE_EXPIRY
):
    await redis_client.set(f"reset_code:{user_id}", code, ex=expiry)


async def store_new_ip(
    user_id: uuid.UUID, new_ip: str, attempts: int
):
    await redis_client.set(f"new_ip:{user_id}:{new_ip}", attempts, ex=SECURITY_EXPIRY)

async def store_allowed_ip(
    user_id: uuid.UUID, new_ip: str
):
    banned_ip = await redis_client.get(f"new_ip:{user_id}:{new_ip}")
    if banned_ip:
        delete_ip_security(user_id,new_ip)
    await redis_client.set(f"allowed:{user_id}:{new_ip}", new_ip, ex=None)

async def delete_ip_security(
    user_id: uuid.UUID, new_ip: str
):
    await redis_client.delete(f"new_ip:{user_id}:{new_ip}")

async def delete_allowed_ip(
    user_id: uuid.UUID, new_ip: str
):
    await redis_client.delete(f"allowed:{user_id}:{new_ip}")

# Get the reset code from Redis
async def get_password_reset_code(user_id: uuid.UUID) -> Optional[str]:
    return await redis_client.get(f"reset_code:{user_id}")


# Email Verification Code
async def store_verification_code(user_id: uuid.UUID, code: str) -> None:
    """Stores the verification code in Redis with an expiry time."""
    await redis_client.hset(
        f"verification_code:{user_id}", mapping={"code": code, "verified": "false"}
    )
    await redis_client.expire(f"verification_code:{user_id}", VERIFICATION_CODE_EXPIRY)


async def get_verification_status(user_id: uuid.UUID) -> dict:
    """Retrieves the verification code and status from Redis."""
    data = await redis_client.hgetall(f"verification_code:{user_id}")
    return {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}


async def mark_email_verified(user_id: uuid.UUID) -> None:
    """Marks the email as verified."""
    await redis_client.hset(f"verification_code:{user_id}", "verified", "true")


# Blacklisting
async def add_jti_to_blocklist(jti: str) -> None:
    """Adds a JTI (JWT ID) to the Redis blocklist with an expiry."""
    # Use the 'set' command with an expiry to add the JTI to the blocklist
    await redis_client.set(jti, "", ex=JTI_EXPIRY)


async def token_in_blocklist(jti: str) -> bool:
    """Checks if a JTI (JWT ID) is in the Redis blocklist."""
    # Use 'exists' instead of 'get' for better performance
    is_blocked = await redis_client.exists(jti)
    LOGGER.debug(f"Token is locked: {is_blocked == 1}")
    return is_blocked == 1
