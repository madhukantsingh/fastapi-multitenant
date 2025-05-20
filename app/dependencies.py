from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app import models, security
from app.models import Base, User, Tenant
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os, time

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")  # Optionally use a single URL env var
if not DATABASE_URL:
    # Compose DB URL from components if provided
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "password")
    db_host = os.getenv("DB_HOST", "db")
    db_name = os.getenv("DB_NAME", "multitenant")
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
# Note: using PyMySQL driver for MySQL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (for dev/demo purposes; in production use migrations)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # If DB is not ready, we can retry a few times
    retries = 5
    while retries:
        time.sleep(3)
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as err:
            retries -= 1
            if retries == 0:
                print("Error: Could not create tables:", err)
                raise

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user from token
def get_current_user(token: str = Depends(lambda: None),  # placeholder, will override in router
                     db: Session = Depends(get_db),
                     request: Request = None):
    # We will manually extract token from Authorization header since we can't easily inject OAuth2 in two contexts
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    try:
        payload = security.decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    # Fetch user from DB
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    # If token is from a tenant user, ensure tenant matches the subdomain (for extra security)
    tenant_id = payload.get("tenant_id")
    if user.is_superadmin:
        # Superadmin token should not have a tenant_id
        tenant_id = None
    # Attach the token payload info to user object for reference
    user.token_payload = payload
    return user

# Dependency to get current tenant based on subdomain (Host header)
def get_current_tenant(request: Request, db: Session = Depends(get_db)):
    host = request.headers.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Bad request: no host header")
    # Remove port if present
    host_without_port = host.split(":")[0]
    # If host is just "localhost" (or any base domain without subdomain), we consider it superadmin context
    if host_without_port == "localhost" or host_without_port == "127.0.0.1":
        return None
    # If host is like "abc.localhost" or "abc.example.com"
    subdomain = None
    if host_without_port.endswith(".localhost"):
        # e.g., "abc.localhost"
        subdomain = host_without_port.split(".")[0]
    else:
        # general case: take the first segment as subdomain for custom domains
        parts = host_without_port.split(".")
        if len(parts) > 2:
            subdomain = parts[0]
    if not subdomain:
        return None
    tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
