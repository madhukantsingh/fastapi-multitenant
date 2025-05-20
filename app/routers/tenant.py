from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, security
from app.dependencies import get_db, get_current_user, get_current_tenant
from app.models import User, Tenant, Plan, Usage
from app.tasks.billing import send_billing_email  # Celery task
from datetime import datetime
from fastapi import Request
from typing import List



router = APIRouter(prefix="/tenant")


# Dependency that ensures we have a tenant context and a current user from that tenant
def tenant_user_required(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant)
):
    # Only allow if current_user is not superadmin and belongs to this tenant
    if current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Superadmin token not allowed here")
    if tenant is None or current_user.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Operation not allowed for this tenant")
    return {"user": current_user, "tenant": tenant}

@router.post("/login", response_model=schemas.TokenResponse)
def tenant_login(credentials: schemas.LoginRequest, 
                db: Session = Depends(get_db), 
                tenant: Tenant = Depends(get_current_tenant)):
    """Tenant user login (at subdomain). If first time, prompt plan selection after login."""
    if tenant is None:
        
        raise HTTPException(status_code=400, detail="Tenant login should be done on tenant subdomain")
    user = db.query(User).filter(User.email == credentials.email, User.tenant_id == tenant.id).first()
    if not user or not security.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Create token with user_id and tenant_id
    token_data = {"user_id": user.id, "tenant_id": tenant.id}
    access_token = security.create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/plans", response_model=List[schemas.PlanOut])
def get_available_plans(db: Session = Depends(get_db),
                        context: dict = Depends(tenant_user_required)):
    """Get available plans (for plan selection, accessible to tenant users)."""
    plans = db.query(Plan).all()
    return plans

@router.post("/plan/select", response_model=schemas.Message)
async def select_plan(
    request: Request,  
    db: Session = Depends(get_db),
    context: dict = Depends(tenant_user_required)
    ):
    current_user = context["user"]
    tenant = context["tenant"]

    if not current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Only tenant admin can select a plan")

    try:
        body = await request.json()
    except:
        body = {}

    plan_id = body.get("plan_id")
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")

    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    tenant.plan_id = plan.id
    db.commit()
    return {"detail": f"Plan '{plan.name}' has been assigned to tenant {tenant.name}."}


@router.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, 
                db: Session = Depends(get_db),
                context: dict = Depends(tenant_user_required)):
    """Create a new user under this tenant (tenant admin only)."""
    current_user = context["user"]
    tenant = context["tenant"]
    if not current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Only tenant admin can create users")
    # Check email not already used in this tenant
    if db.query(User).filter(User.tenant_id == tenant.id, User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already in use in this tenant")
    user = User(email=user_in.email,
                name=user_in.name,
                password_hash=security.hash_password(user_in.password),
                is_superadmin=False,
                is_tenant_admin=False,
                tenant_id=tenant.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/features/use", response_model=schemas.Message)
def use_feature(request: schemas.FeatureUseRequest,
                db: Session = Depends(get_db),
                context: dict = Depends(tenant_user_required)):
    """Trigger usage of a feature (F1-F4) by the current user."""
    current_user = context["user"]
    tenant = context["tenant"]
    # Ensure tenant has a plan
    if tenant.plan_id is None:
        raise HTTPException(status_code=402, detail="No plan selected. Please select a plan to use features.")
    plan = db.query(Plan).filter(Plan.id == tenant.plan_id).first()
    if not plan:
        raise HTTPException(status_code=500, detail="Plan assigned to tenant not found")
    feature_code = request.feature  # like "F3"
    # Determine feature index (e.g., "F3" -> 3)
    try:
        feature_index = int(feature_code[1:])
    except:
        feature_index = None
    if feature_index is None:
        raise HTTPException(status_code=400, detail="Invalid feature code")
    # Check plan allowance
    if feature_index > plan.max_features:
        raise HTTPException(status_code=403, detail=f"Feature {feature_code} is not available for your plan")
    # Record usage
    usage = Usage(tenant_id=tenant.id, user_id=current_user.id, feature=feature_code)
    db.add(usage)
    db.commit()
    return {"detail": f"Feature {feature_code} used successfully"}

@router.post("/billing/send", response_model=schemas.Message)
def send_billing(db: Session = Depends(get_db), context: dict = Depends(tenant_user_required)):
    """Trigger sending of billing email (async via Celery)."""
    current_user = context["user"]
    tenant = context["tenant"]
    # Only tenant admin can trigger billing email
    if not current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Only tenant admin can send billing")
    # Gather usage data (for simplicity, total count and by feature)
    usages = db.query(Usage).filter(Usage.tenant_id == tenant.id).all()
    total_usage = len(usages)
    usage_counts = {}
    for u in usages:
        usage_counts[u.feature] = usage_counts.get(u.feature, 0) + 1
    # In a real scenario, you might calculate costs here based on usage and plan.
    # Compose a summary message
    summary_lines = [f"{feat}: {count}" for feat, count in usage_counts.items()]
    summary = "; ".join(summary_lines) if summary_lines else "No usage."
    email_to = current_user.email  # assuming tenant admin's email for billing contact
    # Enqueue Celery task
    send_billing_email.delay(tenant.id, email_to, summary, total_usage)
    return {"detail": "Billing email has been queued for sending"}
