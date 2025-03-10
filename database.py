import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

# Aggiorna l'URL del database se inizia con "postgresql://"
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Debug: Stampiamo l'URL del database per verificarlo
print(f"🔍 DEBUG - DATABASE_URL: {DATABASE_URL}")

# Test asincrono della connessione
async def test_connection():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: conn.execute("SELECT 1"))
        print("✅ Connessione a PostgreSQL riuscita!")
    except Exception as e:
        print(f"❌ Errore di connessione al database: {e}")

# Avviamo il test solo quando il file viene eseguito direttamente
if __name__ == "__main__":
    asyncio.run(test_connection())

# Creiamo l'engine effettivo dopo il test
engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
