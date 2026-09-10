from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Facility(Base):
    """Presidio sanitario censito dai dataset in `data/facilities/`."""

    __tablename__ = "facilities"
    # Deduplica i record che arrivano da dataset diversi ma descrivono lo stesso presidio.
    __table_args__ = (UniqueConstraint("name", "municipality", name="uq_facility_name_town"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[str] = mapped_column(String(32), index=True, default="altro")
    asl: Mapped[str | None] = mapped_column(String(120), index=True, default=None)
    municipality: Mapped[str | None] = mapped_column(String(120), index=True, default=None)
    province: Mapped[str | None] = mapped_column(String(8), default=None)
    address: Mapped[str | None] = mapped_column(String(255), default=None)
    postal_code: Mapped[str | None] = mapped_column(String(16), default=None)
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    beds: Mapped[int | None] = mapped_column(Integer, default=None)
    phone: Mapped[str | None] = mapped_column(String(64), default=None)
    source: Mapped[str] = mapped_column(String(255), default="")
