import asyncio
from datetime import datetime
import uuid
from fastapi import Request
from passlib.context import CryptContext
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.apps.accounts.dependencies import get_ip_address, get_location
from src.apps.accounts.models import KnownIps, User, VerifiedEmail
from src.db.db import get_session
from src.utils.logger import LOGGER

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to get user input asynchronously
async def get_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)

# Function to hash password asynchronously
async def hash_password(password: str) -> str:
    return await asyncio.to_thread(pwd_context.hash, password)

async def create_superuser():
    async for session in get_session():
        # Get user input asynchronously
        email = await get_input("Enter email for superuser: ")
        password = await get_input("Enter password for superuser: ")
        ip = await get_input("Enter your IP: ")

        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.first()

        if existing_user:
            LOGGER.info(f"User with email {email} already exists.")
            return

        # Hash password asynchronously
        hashed_password = await hash_password(password)

        # Create superuser
        superuser = User(
            uid=uuid.uuid4(),
            email=email,
            passwordHash=hashed_password,
            isSuperuser=True,
            isCompany=True,
        )

        location= await get_location(ip)
        superuser.country = location.country
        superuser.countryCode = location.country_code
        superuser.countryCallingCode = location.country_calling_code
        superuser.inEu = location.in_eu
        superuser.currency = location.currency


        session.add(superuser)
        await session.commit()

        verified_email = VerifiedEmail(
            uid=uuid.uuid4(),
            user=superuser,
            userUid=superuser.uid,
            email=email,
            verifiedAt=datetime.utcnow()
        )

        session.add(verified_email)
        await session.commit()

        new_ip = KnownIps(
            uid=uuid.uuid4(),
            user=superuser,
            userUid=superuser.uid,
            ip=ip,
        )
        session.add(new_ip)
        await session.commit()


        LOGGER.info(f"Superuser {email} created successfully.")

if __name__ == "__main__":
    asyncio.run(create_superuser())
