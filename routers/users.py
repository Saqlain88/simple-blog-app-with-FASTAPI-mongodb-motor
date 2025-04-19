import bcrypt
from bson import ObjectId
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Body, APIRouter, status, Response
from models.UserModel import User, UserLogin, UserView, UserProfileUpdate
from pymongo import ReturnDocument
from auth.auth_bearer import JWTBearer
from auth.auth_handler import sign_jwt

###### USER

router = APIRouter()

# Hash a password using bcrypt
def hash_password(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password

# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password, hashed_password):
    password_byte_enc = plain_password.encode('utf-8')
    return bcrypt.checkpw(password = password_byte_enc , hashed_password = hashed_password)

async def check_user(email_address: str, password: str):
    result = await router.mongodb["user"].find_one({"email": email_address})
    if result is not None:
        hashed_password= result["password"]
        return verify_password(password, hashed_password)
    else: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"Invalid! email")
    

@router.post("/user/login/", tags=["user"])
async def login(user: UserLogin = Body(...)):
    if await check_user(user.email, user.password):
        return sign_jwt(user.email)
    return {
        "error": "Wrong login details!"
    }


@router.post("/user/signup/", tags=["user"])
async def signup(user: User = Body(...)):
    user.password = hash_password((user.password))
    result = await router.mongodb["user"].insert_one(user.dict())
    inserted_user = await router.mongodb["user"].find_one({"_id": result.inserted_id})
    print(inserted_user)
    return sign_jwt(user.email)

@router.get("/users/", response_model=List[UserView])
async def list_users():
    users = await router.mongodb["user"].find().to_list(1000)
    for user in users:
        user=user.pop('password')
    return users
    
@router.get("/users/{id}/", response_model=UserView)
async def get_users(id, response=Response):
    user = await router.mongodb["user"].find_one({'_id': ObjectId(id)})
    return user

@router.put("/user/{id}/", response_model=UserView, status_code=status.HTTP_201_CREATED)
async def update_user(id, user: UserProfileUpdate):
    user_dict = {
        k: v for k, v in user.model_dump(by_alias=True).items() if v is not None
    }
    user_update = await router.mongodb["user"].find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": user_dict},
            return_document=ReturnDocument.AFTER,
        )       
    if user_update is not None:
        return user_update
    else:
        raise HTTPException(status_code=404, detail=f"user with id: {id}, was not found.")