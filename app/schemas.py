from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# Shared base classes for DRY principle
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    is_tenant_admin: bool = False
    tenant_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True  # allow ORM objects to be returned as schema

class TenantBase(BaseModel):
    name: str = Field(..., max_length=100)
    subdomain: str = Field(..., pattern="^[a-zA-Z0-9_-]+$", max_length=50)


class TenantCreate(TenantBase):
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)

class TenantOut(TenantBase):
    id: int
    plan_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True

class PlanBase(BaseModel):
    name: str
    max_features: int = Field(..., ge=0, le=10)  # assuming no more than 10 features for example

class PlanCreate(PlanBase):
    pass

class PlanOut(PlanBase):
    id: int

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class FeatureUseRequest(BaseModel):
    feature: str = Field(..., pattern="^F[1-9][0-9]?$")  # matches "F1","F2",... up to F99 for example

class Message(BaseModel):
    detail: str
