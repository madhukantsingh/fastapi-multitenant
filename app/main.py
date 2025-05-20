from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routers import superadmin, tenant
from app.dependencies import get_current_tenant, get_current_user, engine
from app import models
import os

app = FastAPI(title="Multi-Tenant SaaS API")

# Include routers
app.include_router(superadmin.router)
app.include_router(tenant.router)

# Enable CORS (if needed, e.g., for local development with a frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create initial superadmin and default plans if not already present (one-time setup)
@app.on_event("startup")
def startup_setup():
    # Create superadmin user if not exists, using env credentials
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    super_email = os.getenv("SUPERADMIN_EMAIL")
    super_pass = os.getenv("SUPERADMIN_PASSWORD")
    if super_email and super_pass:
        existing = db.query(models.User).filter(models.User.is_superadmin == True).first()
        if not existing:
            super_user = models.User(
                email=super_email,
                name="Superadmin",
                password_hash=__import__('app.security').security.hash_password(super_pass),
                is_superadmin=True,
                is_tenant_admin=False
            )
            db.add(super_user)
            db.commit()
    # Optionally, create default plans Basic and Advanced if not exist
    default_plans = [("Basic", 2), ("Advanced", 4)]
    for name, max_feat in default_plans:
        if not db.query(models.Plan).filter(models.Plan.name == name).first():
            plan = models.Plan(name=name, max_features=max_feat)
            db.add(plan)
    db.commit()
    db.close()
