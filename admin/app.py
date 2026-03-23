from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session
from db.models import User, Order, OrderStatus
from datetime import datetime, timedelta
import os

app = FastAPI(title="TalabaGo Admin", docs_url=None, redoc_url=None)

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Simple auth (production'da yaxshiroq auth kerak)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "talabago2024")


def check_auth(request: Request):
    """Session orqali auth tekshirish."""
    if request.cookies.get("admin_auth") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    return True


# ==================== AUTH ====================

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.cookies.get("admin_auth") == ADMIN_PASSWORD:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie("admin_auth", password, httponly=True, max_age=86400)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Parol noto'g'ri"})


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("admin_auth")
    return response


# ==================== DASHBOARD ====================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if request.cookies.get("admin_auth") != ADMIN_PASSWORD:
        return RedirectResponse("/", status_code=302)
    
    async with async_session() as session:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Stats
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        today_users = (await session.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )).scalar() or 0
        
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0
        today_orders = (await session.execute(
            select(func.count(Order.id)).where(Order.created_at >= today)
        )).scalar() or 0
        
        pending_orders = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.pending)
        )).scalar() or 0
        
        completed_orders = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.completed)
        )).scalar() or 0
        
        total_revenue = (await session.execute(
            select(func.sum(Order.price)).where(Order.status == OrderStatus.completed)
        )).scalar() or 0
        
        today_revenue = (await session.execute(
            select(func.sum(Order.price)).where(
                Order.status == OrderStatus.completed,
                Order.completed_at >= today
            )
        )).scalar() or 0
        
        # Recent orders
        recent_orders = (await session.execute(
            select(Order).order_by(desc(Order.created_at)).limit(10)
        )).scalars().all()
        
        # Recent users
        recent_users = (await session.execute(
            select(User).order_by(desc(User.created_at)).limit(10)
        )).scalars().all()
    
    stats = {
        "total_users": total_users,
        "today_users": today_users,
        "total_orders": total_orders,
        "today_orders": today_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_revenue": f"{total_revenue:,}",
        "today_revenue": f"{today_revenue:,}",
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_orders": recent_orders,
        "recent_users": recent_users
    })


# ==================== USERS ====================

@app.get("/users", response_class=HTMLResponse)
async def users_list(request: Request, page: int = 1):
    if request.cookies.get("admin_auth") != ADMIN_PASSWORD:
        return RedirectResponse("/", status_code=302)
    
    per_page = 20
    offset = (page - 1) * per_page
    
    async with async_session() as session:
        total = (await session.execute(select(func.count(User.id)))).scalar() or 0
        users = (await session.execute(
            select(User).order_by(desc(User.created_at)).offset(offset).limit(per_page)
        )).scalars().all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "page": page,
        "total_pages": total_pages,
        "total": total
    })


# ==================== ORDERS ====================

@app.get("/orders", response_class=HTMLResponse)
async def orders_list(request: Request, page: int = 1, status: str = None):
    if request.cookies.get("admin_auth") != ADMIN_PASSWORD:
        return RedirectResponse("/", status_code=302)
    
    per_page = 20
    offset = (page - 1) * per_page
    
    async with async_session() as session:
        query = select(Order)
        count_query = select(func.count(Order.id))
        
        if status:
            query = query.where(Order.status == OrderStatus(status))
            count_query = count_query.where(Order.status == OrderStatus(status))
        
        total = (await session.execute(count_query)).scalar() or 0
        orders = (await session.execute(
            query.order_by(desc(Order.created_at)).offset(offset).limit(per_page)
        )).scalars().all()
        
        # Get user info for each order
        for order in orders:
            user = (await session.execute(
                select(User).where(User.id == order.user_id)
            )).scalar_one_or_none()
            order.user = user
    
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": orders,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "current_status": status
    })
