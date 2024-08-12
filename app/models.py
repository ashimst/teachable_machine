from pydantic import BaseModel,EmailStr,Field,ConfigDict
from typing import Dict, Optional,List,Any
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from datetime import datetime
from bson import ObjectId
from enum import Enum

PyObjectId = Annotated[str, BeforeValidator(str)]


class Role(str, Enum):
    user = "user"
    admin = "admin"
    superadmin="superadmin"


class UserModel(BaseModel):
    id: Optional[PyObjectId]=Field(alias="_id",default=None)
    first_name: str= Field(...)
    last_name: str=Field(...)
    username: str=Field(...)
    email: EmailStr=Field(...)
    password: str= Field(...)
    birthdate:datetime = Field(..., description="The user's birthdate in YYYY-MM-DD format")
    role:Optional[Role] = Role.admin,
    is_verified:bool = False

    model_config=ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed= True,
        json_schema_extra={
            "example":{
                "first_name":"Jane",
                "last_name":"Doe",
                "email":"jdoe@example.com",
                "username":"test",
                "password":"string",
                "birthdate":"2022-01-01",
                "role":"user",
                "is_verified": False
            }
            },
    )
def user_serializer(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "birthdate": user.get("birthdate"),
        "role": user["role"],
        "is_verified":user["is_verified"]
    }
def user_serializer_auth(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "birthdate": user.get("birthdate"),
        "role": user["role"],
        "password":user["password"]
    }

def user_otp_serializer(user: dict) -> dict:
    return {
        "role":user["role"],
        "is_verified": user["is_verified"],
        "otp":user["otp"]
    }



class ProjectModel(BaseModel):
    id: Optional[PyObjectId]=Field(alias="_id",default=None)
    project_id:Optional[str]=Field(default=None)
    creator: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    classes: List[Dict[str, List[str]]] = Field(default_factory=list)
    model: Optional[str] = Field(default=None, description="Path to the project's model")
    
    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_schema_extra = {
            "example": {
                "creator": None,
                "name": None,
                "project_id":None,
                "classes": [],
                "model": None
            }
        }
    )

def project_serializer(project: dict) -> dict:
    return {
        "id": str(project["_id"]) if project.get("_id") else None,
        "creator": project.get("creator"),
        "name": project.get("name"),
        "classes": project.get("classes", []),
        "model": project.get("model")
    }

        

