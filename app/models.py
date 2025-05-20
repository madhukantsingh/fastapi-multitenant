from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subdomain = Column(String(50), nullable=False, unique=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)  # Tenant may select a plan later
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan", back_populates="tenants")
    users = relationship("User", back_populates="tenant")
    usages = relationship("Usage", back_populates="tenant")

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    max_features = Column(Integer, nullable=False)  # how many features (F1...Fn) are allowed
    # e.g., Basic = 2, Advanced = 4, corresponding to features F1..F4 allowed

    tenants = relationship("Tenant", back_populates="plan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    name = Column(String(100), nullable=True)
    password_hash = Column(String(128), nullable=False)
    is_superadmin = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_user_email_per_tenant"),)

    tenant = relationship("Tenant", back_populates="users")

class Usage(Base):
    __tablename__ = "usages"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    feature = Column(String(10), nullable=False)  # e.g., "F1", "F2", etc.
    timestamp = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="usages")
