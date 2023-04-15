import datetime as dt
import json

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FlashCard(Base):
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    def get_prompt_text(self) -> str:
        return f"Flash Card\nFront: {self.front} \nBack: {self.back}"

    def to_json(self) -> str:
        return {
            'front': self.front,
            'back': self.back,
        }