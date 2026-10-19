from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.models import Base, Workspace, Profile
from app.observability.logger import logger

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Seed default workspace if empty
    db = SessionLocal()
    try:
        default_ws = db.query(Workspace).filter(Workspace.id == "default-workspace").first()
        if not default_ws:
            default_profile = db.query(Profile).filter(Profile.id == "default-user").first()
            if not default_profile:
                default_profile = Profile(
                    id="default-user",
                    email="admin@documind.ai",
                    full_name="Default Workspace Admin",
                    role="admin"
                )
                db.add(default_profile)
                db.commit()
            
            default_ws = Workspace(
                id="default-workspace",
                name="Default Workspace",
                description="Primary workspace for DocuMind AI documents",
                owner_id="default-user"
            )
            db.add(default_ws)
            db.commit()
            logger.info("Default workspace and admin profile seeded.")
    except Exception as e:
        logger.error(f"Error seeding default workspace: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
