from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from datetime import datetime
from bson import ObjectId


PyObjectId = Annotated[str, BeforeValidator(str)]


class User(BaseModel):
    #id: Optional[PyObjectId] = Field(alias="_id")
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    is_admin: bool = False
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "fullname": "Abdulazeez Abdulazeez Adeshina",
                "email": "abdulazeez@x.com",
                "password": "weakpassword"
            }
        },
        populate_by_name=True
    )

class UserView(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    
class UserProfileUpdate(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)

class UserLogin(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)
    