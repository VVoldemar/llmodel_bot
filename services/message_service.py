import typing

import aiogram
import sqlalchemy.orm
import sqlalchemy.exc

import models.db_session
import models.user
import models.message

def add_message(session: sqlalchemy.orm.Session, content: str, user: models.user.User, is_from_user: bool=True):
    """add message to messages table"""
    new_message = models.message.Message(
        content=content,
        owner_id=user.id,
        is_from_user=is_from_user
    )
    try:
        session.add(new_message)
        session.flush()
    except sqlalchemy.exc.SQLAlchemyError as error:
        print(f"Failed to add message for user {user.id}: {error}")
        raise

def delete_messages(session: sqlalchemy.orm.Session, user: models.user.User):
    """delete all messages that belongs to specified user"""
    try:
        messages_to_delete = session.query(models.message.Message).filter(models.message.Message.owner_id == user.id).all()
        for msg in messages_to_delete:
            session.delete(msg)
        session.flush()
    except sqlalchemy.exc.SQLAlchemyError as error:
        print(f"Failed to delete messages for user {user.id}: {error}")
        raise

def get_context_messages(session: sqlalchemy.orm.Session, user: models.user.User):
    """returns list of dicts with messages for specified user chat in OpenAI format"""
    messages = user.messages
    context = []
    for msg in messages:
        role = "user" if msg.is_from_user else "assistant"
        context.append({"role": role, "content": msg.content})
    return context