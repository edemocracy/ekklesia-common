from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Sequence,
    func,
    JSON
)
from sqlalchemy.orm import relationship, backref

from ekklesia_common.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('id_seq', optional=True), primary_key=True)


class OAuthToken(Base):
    __tablename__ = 'oauth_token'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship("User", backref=backref("oauth_token", uselist=False))
    token = Column(JSON)
    provider = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

