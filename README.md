FastAPI Multitenant Application
====================================

This project is a simplified multi-tenant backend built using FastAPI, Celery, MySQL, and Redis.

Features:
- Superadmin can create tenants and plans
- Each tenant has its own users and login
- Tenants select plans (Basic or Advanced)
- Feature usage billing and Celery-based email notification

---------------------------------------------------------
STEP 1: Clone This Repository
---------------------------------------------------------

git clone https://github.com/madhukantsingh/fastapi-multitenant.git
cd fastapi-multitenant

---------------------------------------------------------
STEP 2: Install Docker
---------------------------------------------------------

Install Docker Desktop from:
https://www.docker.com/products/docker-desktop

Verify installation:
docker --version
docker-compose --version

---------------------------------------------------------
STEP 3: Start the Project
---------------------------------------------------------

docker-compose up --build

If there is any error, use:
docker-compose down
docker-compose up --build

---------------------------------------------------------
STEP 4: Import Postman Collection
---------------------------------------------------------

1. Open Postman
2. Click "Import"
3. Choose the file named: fastapi-multitenant.postman_collection.json

---------------------------------------------------------
API FLOW EXPLANATION
---------------------------------------------------------

1. Superadmin Login
--------------------
POST /superadmin/login

Body:
{
  "email": "superadmin@example.com",
  "password": "superpass123"
}

Copy the access_token from the response to use in all future requests.

2. Create Plans
--------------------
POST /superadmin/plans

Body:
{
  "name": "Basic",
  "max_features": 2
}

Repeat with:
{
  "name": "Advanced",
  "max_features": 4
}

3. Create Tenant
--------------------
POST /superadmin/tenants

Body:
{
  "name": "Company ABC",
  "subdomain": "abc",
  "admin_email": "admin@abc.com",
  "admin_password": "adminpass"
}

4. Tenant Login
--------------------
POST /tenant/login

Body:
{
  "email": "admin@abc.com",
  "password": "adminpass"
}

Save this token for tenant-specific actions.

5. Select Plan
--------------------
POST /tenant/plan/select

Body:
{
  "plan_id": 1
}

6. Create Tenant Users
--------------------
POST /tenant/users

Body:
{
  "email": "user1@abc.com",
  "name": "User One",
  "password": "userpass"
}

7. Use a Feature
--------------------
POST /tenant/features/use

Body:
{
  "feature": "F2"
}

8. Send Billing Email
--------------------
POST /tenant/billing/send

No body needed. It will send a usage summary email (via Celery).

---------------------------------------------------------
OPTIONAL: Set Up Localhost Subdomains (abc.localhost)
---------------------------------------------------------

To simulate subdomains like abc.localhost:

1. Edit your system's hosts file:

Windows:
C:\Windows\System32\drivers\etc\hosts

Add lines:
127.0.0.1 abc.localhost
127.0.0.1 xyz.localhost

2. Or in Postman, use:
URL: http://localhost:8000
Header: Host: abc.localhost

---------------------------------------------------------
Done!
Now you're ready to test and build on this multitenant backend.
---------------------------------------------------------
