# FastAPI is a class that inherits directly from Starlette.
from http.client import HTTPException
from fastapi import FastAPI, Response, status
from typing import List
from bson import ObjectId
from pymongo import ReturnDocument
from contextlib import asynccontextmanager
from models.PostModel import Post, UpdatePostModel
import motor.motor_asyncio
from fastapi import FastAPI, Depends, HTTPException, Body
from auth.auth_bearer import JWTBearer
from auth.auth_handler import sign_jwt
from models.UserModel import User, UserLogin, UserView, UserProfileUpdate
import bcrypt

# define a lifespan method for fastapi
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

async def startup_db_client(app):
    app.mongodb_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://admin_db:admin_db%40123@ac-zqjvwqm-shard-00-00.rwsx2kh.mongodb.net:27017,ac-zqjvwqm-shard-00-01.rwsx2kh.mongodb.net:27017,ac-zqjvwqm-shard-00-02.rwsx2kh.mongodb.net:27017/?replicaSet=atlas-k4qpqk-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=Cluster0")
    app.mongodb = app.mongodb_client.get_database("blog")
    print("MongoDB connected.")

async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")

app = FastAPI(lifespan=lifespan)

####### POST

@app.get("/") # decorator
async def root():
    return {"message": "Hello World"}


@app.get("/posts/", response_model=List[Post])
async def list_posts():
    posts = await app.mongodb["post"].find().to_list(1000)
    return posts


@app.get("/posts/latest/", response_model=List[Post])
async def get_latest_post():
    posts = await app.mongodb["post"].find().sort("created_at").to_list(1000)
    return posts


@app.get("/posts/{id}", response_model=Post)
async def get_post(id, response: Response):
    post = await app.mongodb["post"].find_one({"_id": ObjectId(id)})
    if post:
        return post
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"post_detail": f"post with id: {id}, was not found."}


@app.post("/create-posts/", status_code=status.HTTP_201_CREATED, response_model=Post, dependencies=[Depends(JWTBearer())], tags=["posts"])
async def create_posts(new_post: Post):
    result = await app.mongodb["post"].insert_one(new_post.dict())
    inserted_post = await app.mongodb["post"].find_one({"_id": result.inserted_id})
    return inserted_post


@app.put("/posts/{id}", response_model=Post, status_code=status.HTTP_201_CREATED)
async def update_post(id, post: UpdatePostModel):
    post_dict = {
        k: v for k, v in post.model_dump(by_alias=True).items() if v is not None
    }
    updated_post = await app.mongodb["post"].find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": post_dict},
            return_document=ReturnDocument.AFTER,
        )       
    if updated_post is not None:
        return updated_post
    else:
        raise HTTPException(status_code=404, detail=f"post with id: {id}, was not found.")
    if (existing_post := await post.find_one({"_id": id})) is not None:
        return existing_post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with id: {id}, was not found.")


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: str):
    delete_result = await app.mongodb["post"].delete_one({"_id": ObjectId(id)})
    if delete_result is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with id: {id}, was not found.")

###### USER

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
    result = await app.mongodb["user"].find_one({"email": email_address})
    if result is not None:
        hashed_password= result["password"]
        return verify_password(password, hashed_password)
    else: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"Invalid! email")
    

@app.post("/user/login/", tags=["user"])
async def login(user: UserLogin = Body(...)):
    if await check_user(user.email, user.password):
        return sign_jwt(user.email)
    return {
        "error": "Wrong login details!"
    }


@app.post("/user/signup/", tags=["user"])
async def signup(user: User = Body(...)):
    user.password = hash_password((user.password))
    result = await app.mongodb["user"].insert_one(user.dict())
    inserted_user = await app.mongodb["user"].find_one({"_id": result.inserted_id})
    print(inserted_user)
    return sign_jwt(user.email)

@app.get("/users/", response_model=List[UserView])
async def list_users():
    users = await app.mongodb["user"].find().to_list(1000)
    for user in users:
        user=user.pop('password')
    return users
    
@app.get("/users/{id}/", response_model=UserView)
async def get_users(id, response=Response):
    user = await app.mongodb["user"].find_one({'_id': ObjectId(id)})
    return user

@app.put("/user/{id}/", response_model=UserView, status_code=status.HTTP_201_CREATED)
async def update_user(id, user: UserProfileUpdate):
    user_dict = {
        k: v for k, v in user.model_dump(by_alias=True).items() if v is not None
    }
    user_update = await app.mongodb["user"].find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": user_dict},
            return_document=ReturnDocument.AFTER,
        )       
    if user_update is not None:
        return user_update
    else:
        raise HTTPException(status_code=404, detail=f"user with id: {id}, was not found.")

# Run with ``uvicorn main:app --reload``

# http://localhost:8000/redoc
# http://localhost:8000/docs/
