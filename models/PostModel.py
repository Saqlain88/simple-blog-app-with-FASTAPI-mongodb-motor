from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from datetime import datetime
from bson import ObjectId

PyObjectId = Annotated[str, BeforeValidator(str)]

class Post(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(...)
    description: str = Field(...)
    published: bool = True
    rating: float | Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "title": "Top 10 tourist vists",
                "description": "lorem ipsum lorem ipsum",
                "published": True,
                "rating": 3.0,
            }
        },
        populate_by_name=True
    )

class UpdatePostModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    published: Optional[bool] = None
    rating: Optional[float] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Top 10 tourist vists",
                "description": "lorem ipsum lorem ipsum",
                "published": True,
                "rating": 3.0,
            }
        },
        populate_by_name=True
    )
