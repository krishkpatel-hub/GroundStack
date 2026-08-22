from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.settings import get_settings

settings = get_settings()
connect_args = {"ssl": True} if settings.db_ssl_required else {}
engine = create_async_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=0,
    connect_args=connect_args,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
