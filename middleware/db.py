from typing import Callable, Dict, Any, Awaitable, Optional

import aiogram
import sqlalchemy.exc

import models.db_session
import services.user_service
import models


class DbSessionMiddleware(aiogram.BaseMiddleware):

    async def __call__(self,
                       handler: Callable[[aiogram.types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: aiogram.types.TelegramObject,
                       data: Dict[str, Any]):
        session = models.db_session.get_session()
        data["session"] = session

        telegram_user: Optional[aiogram.types.User] = data.get("event_from_user", None)
        if telegram_user:
            try:
                user = await services.user_service.get_or_create_user(session=session, telegram_user=telegram_user)
                data["user"] = user
            except sqlalchemy.exc.SQLAlchemyError as error:
                print(f"Database error fetching/creating user {telegram_user.id}: {error}")
                session.rollback()
                session.close()
                return
            except ValueError as ve:
                print(f"Could not create user {telegram_user.id}: {ve}")
                pass  # if telegram_user.username does not exist

        try:
            result = await handler(event, data)
            session.commit()
            return result
        except Exception as error:
            print(f"Error in handler for user")
            session.rollback()  # TODO: add error logging
            raise
        finally:
            session.close()