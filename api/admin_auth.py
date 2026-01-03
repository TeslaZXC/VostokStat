from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
import bcrypt
from database import AsyncSessionLocal, AdminUser
from sqlalchemy.future import select

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Fetch user from DB
        async with AsyncSessionLocal() as session:
            stmt = select(AdminUser).filter(AdminUser.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()

        if not user:
            return False

        # Verify password
        try:
            if bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
                request.session.update({"token": username})
                return True
        except Exception:
            return False
            
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # Simple token check
        token = request.session.get("token")
        return token is not None
