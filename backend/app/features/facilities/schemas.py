from pydantic import BaseModel, ConfigDict


class FacilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    asl: str | None = None
    municipality: str | None = None
    province: str | None = None
    address: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    beds: int | None = None
    phone: str | None = None
    source: str = ""


class FacilityList(BaseModel):
    items: list[FacilityRead]
    total: int
    limit: int
    offset: int


class TypeCount(BaseModel):
    type: str
    count: int


class AslCount(BaseModel):
    asl: str
    count: int


class FacilitySummary(BaseModel):
    total: int
    by_type: list[TypeCount]
    by_asl: list[AslCount]
    municipalities: int
