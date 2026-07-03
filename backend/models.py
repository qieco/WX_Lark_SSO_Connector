from pydantic import BaseModel, Field
from typing import Optional


class EndpointCreate(BaseModel):
    route_name: str = Field(
        ..., min_length=1, pattern=r"^[a-zA-Z0-9\-]+$",
        description="URL route name, alphanumeric and hyphens only"
    )
    instance_id: str = Field(..., min_length=1)
    app_id: str = Field(..., min_length=1)
    description: Optional[str] = ""


class EndpointUpdate(BaseModel):
    route_name: Optional[str] = Field(
        None, min_length=1, pattern=r"^[a-zA-Z0-9\-]+$"
    )
    instance_id: Optional[str] = Field(None, min_length=1)
    app_id: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None


class EndpointResponse(BaseModel):
    id: int
    route_name: str
    instance_id: str
    app_id: str
    description: str
    created_at: str
    updated_at: str


class SettingResponse(BaseModel):
    key: str
    value: str
    description: str


class SettingUpdate(BaseModel):
    value: str
