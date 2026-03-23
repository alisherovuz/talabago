from sqlalchemy import select, func
from db.database import async_session
from db.models import User, Order, PaperType, OrderStatus
from datetime import datetime, timedelta


class DBService:
    
    async def get_or_create_user(self, telegram_id: int, username: str = None, full_name: str = None, referred_by: int = None):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name,
                    referred_by=referred_by
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                # Referral bonus berish (yangi user bo'lsa)
                if referred_by:
                    await self._add_referral_bonus(session, referred_by)
            else:
                # Update username/fullname if changed
                if username and user.username != username:
                    user.username = username
                if full_name and user.full_name != full_name:
                    user.full_name = full_name
                await session.commit()
            
            return user
    
    async def _add_referral_bonus(self, session, referrer_telegram_id: int):
        """Referral bonus qo'shish (ichki metod)."""
        result = await session.execute(
            select(User).where(User.telegram_id == referrer_telegram_id)
        )
        referrer = result.scalar_one_or_none()
        if referrer:
            referrer.referral_bonus = (referrer.referral_bonus or 0) + 1000
            await session.commit()
    
    async def create_order(self, telegram_id: int, topic: str, paper_type: str, language: str, price: int, pages: int = 10):
        async with async_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            order = Order(
                user_id=user.id,
                topic=topic,
                paper_type=PaperType(paper_type),
                language=language,
                requested_pages=pages,
                price=price,
                status=OrderStatus.pending
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order
    
    async def update_order_status(self, order_id: int, status: str):
        async with async_session() as session:
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            if order:
                order.status = OrderStatus(status)
                if status == "completed":
                    order.completed_at = datetime.utcnow()
                await session.commit()
            return order
    
    async def complete_order(self, order_id: int, word_count: int, page_count: int):
        async with async_session() as session:
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            if order:
                order.status = OrderStatus.completed
                order.word_count = word_count
                order.page_count = page_count
                order.completed_at = datetime.utcnow()
                await session.commit()
            return order
    
    async def get_order_by_id(self, order_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_orders(self, telegram_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return []
            
            result = await session.execute(
                select(Order)
                .where(Order.user_id == user.id)
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()
    
    # ==================== ADMIN METHODS ====================
    
    async def get_admin_stats(self):
        async with async_session() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Total users
            total_users_result = await session.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
            
            # Today users
            today_users_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= today)
            )
            today_users = today_users_result.scalar() or 0
            
            # Total orders
            total_orders_result = await session.execute(select(func.count(Order.id)))
            total_orders = total_orders_result.scalar() or 0
            
            # Today orders
            today_orders_result = await session.execute(
                select(func.count(Order.id)).where(Order.created_at >= today)
            )
            today_orders = today_orders_result.scalar() or 0
            
            # Pending orders
            pending_orders_result = await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.pending)
            )
            pending_orders = pending_orders_result.scalar() or 0
            
            # Completed orders
            completed_orders_result = await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.completed)
            )
            completed_orders = completed_orders_result.scalar() or 0
            
            # Total revenue (completed orders)
            total_revenue_result = await session.execute(
                select(func.sum(Order.price)).where(Order.status == OrderStatus.completed)
            )
            total_revenue = total_revenue_result.scalar() or 0
            
            # Today revenue
            today_revenue_result = await session.execute(
                select(func.sum(Order.price)).where(
                    Order.status == OrderStatus.completed,
                    Order.completed_at >= today
                )
            )
            today_revenue = today_revenue_result.scalar() or 0
            
            return {
                'total_users': total_users,
                'today_users': today_users,
                'total_orders': total_orders,
                'today_orders': today_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'total_revenue': total_revenue,
                'today_revenue': today_revenue
            }
    
    async def get_recent_users(self, limit: int = 20):
        async with async_session() as session:
            result = await session.execute(
                select(User)
                .order_by(User.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_recent_orders(self, limit: int = 20):
        async with async_session() as session:
            result = await session.execute(
                select(Order)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    # ==================== REGISTRATION ====================
    
    async def is_user_registered(self, telegram_id: int) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            return user is not None and user.is_registered == 1
    
    async def complete_registration(self, telegram_id: int, full_name: str, university: str, course: int):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.full_name = full_name
                user.university = university
                user.course = course
                user.is_registered = 1
                await session.commit()
            return user
    
    # ==================== BROADCAST ====================
    
    async def get_all_user_ids(self):
        async with async_session() as session:
            result = await session.execute(
                select(User.telegram_id)
            )
            return [row[0] for row in result.fetchall()]
    
    # ==================== REFERRAL SYSTEM ====================
    
    async def get_referral_count(self, telegram_id: int) -> int:
        """Foydalanuvchi nechta odam taklif qilganini hisoblash."""
        async with async_session() as session:
            result = await session.execute(
                select(func.count(User.id)).where(User.referred_by == telegram_id)
            )
            return result.scalar() or 0
    
    async def get_referral_bonus(self, telegram_id: int) -> int:
        """Foydalanuvchining referral bonusini olish."""
        async with async_session() as session:
            result = await session.execute(
                select(User.referral_bonus).where(User.telegram_id == telegram_id)
            )
            bonus = result.scalar()
            return bonus or 0
    
    async def use_referral_bonus(self, telegram_id: int, amount: int) -> bool:
        """Referral bonusdan foydalanish."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user and (user.referral_bonus or 0) >= amount:
                user.referral_bonus = (user.referral_bonus or 0) - amount
                await session.commit()
                return True
            return False


db_service = DBService()
