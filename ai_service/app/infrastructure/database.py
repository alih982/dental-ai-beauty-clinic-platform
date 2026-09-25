# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import logging

# logger = logging.getLogger(__name__)

# # Try PostgreSQL first (psycopg v3), fall back to SQLite
# try:
#     from app.config import settings
#     engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
#     logger.info("Connected to PostgreSQL database.")
# except Exception as e:
#     logger.warning(f"PostgreSQL not available: {e}. Using SQLite fallback.")
#     engine = create_engine(
#         "sqlite:///./ai_service.db",
#         connect_args={"check_same_thread": False}
#     )

# # Create SessionLocal class
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base class for models
# Base = declarative_base()


# def get_db():
#     """Dependency for getting DB session"""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

