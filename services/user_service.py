import logging
import typing

import aiogram
import sqlalchemy.orm
import sqlalchemy.exc

import models.db_session
import models.user


async def get_or_create_user(session: sqlalchemy.orm.Session, telegram_user: aiogram.types.User) -> models.user.User:
    user: typing.Optional[models.user.User] = session.get(models.user.User, telegram_user.id)

    if user:
        print(f"User {telegram_user.id} found in DB.")
        needs_flush = False

        if telegram_user.username and telegram_user.username != user.username:
            user.username = telegram_user.username
            needs_flush = True

        if needs_flush:
            try:
                session.add(user)
                session.flush()
                print(f"Flushed updates for user {user.id}")
            except sqlalchemy.exc.SQLAlchemyError as error:
                print(f"Failed to flush updates for user {user.id}: {error}")
                raise  # TODO: Add `error` logging

        return user
    else:
        print(f"User {telegram_user.id} not found. Creating...")
        username_to_save = telegram_user.username or f"user_{telegram_user.id}"
        new_user = models.user.User(id=telegram_user.id, username=username_to_save)

        try:
            session.add(new_user)
            session.flush()
            print(f"User {telegram_user.id} ({username_to_save}) created and flushed to session.")

            return new_user
        except sqlalchemy.exc.SQLAlchemyError as error:
            print(f"Failed to flush new user {telegram_user.id}: {error}")
            raise  # TODO: Add `error` logging


def get_user_instruction(session: sqlalchemy.orm.Session):
    user: models.user.User = session.get(models.user.User)


async def set_instruction(instruction: str, session: sqlalchemy.orm.Session, user: models.user.User):
    user.instruction = instruction
    session.flush()