from sqlalchemy import text

from app.db.session import async_session_factory
from app.schemas.system import DatabaseStatus


async def check_database() -> DatabaseStatus:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        return DatabaseStatus(connected=False, detail=exc.__class__.__name__)
    return DatabaseStatus(connected=True, detail="ok")
