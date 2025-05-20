from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, security
from app.dependencies import get_db, get_current_user
from app.models import User, Tenant, Plan
from typing import List

router = APIRouter(prefix="/superadmin")

# Dependency specifically requiring superadmin privileges
def superadmin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin access required")
    return current_user

@router.post("/login", response_model=schemas.TokenResponse)
def superadmin_login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Superadmin login to get JWT token."""
    user = db.query(User).filter(User.email == credentials.email, User.is_superadmin == True).first()
    if not user or not security.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # Create JWT token with role
    token_data = {"user_id": user.id, "role": "superadmin"}
    access_token = security.create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/plans", response_model=schemas.PlanOut)
def create_plan(plan_in: schemas.PlanCreate, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(superadmin_required)):
    """Create a new subscription plan (superadmin only)."""
    # Ensure plan name is unique
    existing = db.query(Plan).filter(Plan.name == plan_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plan name already exists")
    plan = Plan(name=plan_in.name, max_features=plan_in.max_features)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/plans", response_model=List[schemas.PlanOut])
def list_plans(db: Session = Depends(get_db), current_user: User = Depends(superadmin_required)):
    """List all plans."""
    plans = db.query(Plan).all()
    return plans

@router.post("/tenants", response_model=schemas.TenantOut)
def create_tenant(tenant_in: schemas.TenantCreate, 
                  db: Session = Depends(get_db),
                  current_user: User = Depends(superadmin_required)):
    """Create a new tenant with an initial admin user."""
    # Check subdomain uniqueness
    if db.query(Tenant).filter(Tenant.subdomain == tenant_in.subdomain).first():
        raise HTTPException(status_code=400, detail="Subdomain already in use")
    # Check if admin email is used by any user (optional: ensure globally unique email)
    if db.query(User).filter(User.email == tenant_in.admin_email, User.tenant_id == None).first():
        # if the email is used by superadmin or another tenant? 
        # (We only ensure within same tenant via unique constraint, but superadmin email or reuse across tenants might be allowed in some cases)
        raise HTTPException(status_code=400, detail="Email already taken by another account")
    # Create tenant
    tenant = Tenant(name=tenant_in.name, subdomain=tenant_in.subdomain)
    db.add(tenant)
    db.flush()  # flush to get tenant.id for user relation
    # Create initial admin user for tenant
    admin_user = User(email=tenant_in.admin_email,
                      name=None,
                      password_hash=security.hash_password(tenant_in.admin_password),
                      is_superadmin=False,
                      is_tenant_admin=True,
                      tenant=tenant)
    db.add(admin_user)
    db.commit()
    db.refresh(tenant)
    return tenant

@router.get("/tenants", response_model=List[schemas.TenantOut])
def list_tenants(db: Session = Depends(get_db), current_user: User = Depends(superadmin_required)):
    """List all tenants."""
    tenants = db.query(Tenant).all()
    return tenants

@router.get("/tenants/{tenant_id}/users", response_model=List[schemas.UserOut])
def list_tenant_users(tenant_id: int, db: Session = Depends(get_db), current_user: User = Depends(superadmin_required)):
    """View all users under a particular tenant."""
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    return users
