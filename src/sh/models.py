from sqlalchemy import Column, Integer, String, DateTime, UUID, ForeignKey, Boolean, func
from datetime import datetime, timezone
from src.models import Base

class ShortLink(Base):
    __tablename__ = "short_links"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    clicks = Column(Integer, default=0)

    def is_expired(self) -> bool:
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return True
        return False