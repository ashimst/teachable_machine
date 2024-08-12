from fastapi import APIRouter, Body, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app import oauth2, models,database,schemas
from ..utilities import hashing,email_utils

router = APIRouter(prefix='/auth',
    tags=['Authentication'])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(user: models.UserModel = Body(...)):  
    user_data = user.model_dump(by_alias=True, exclude=["id"])
    user_data["password"] = hashing.hash(user_data["password"])
    user_data["is_verified"]= False
    user_data["role"]=models.Role.user
    
    # Check if username or email already exists
    username_exist = await database.User.find_one({"username": user.username})
    email_exist = await database.User.find_one({"email": user.email})

    if username_exist:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Account with username '{user.username}' already exists"
        )
    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Account with email '{user.email}' already exists"
        )
 
    # Insert new user
    new_user = await database.User.insert_one(user_data)
    created_user = await database.User.find_one({"_id": new_user.inserted_id})

    # Serialize the user data for response
    response = models.user_serializer(created_user)
    return response


@router.post("/generate-otp")
async def generate_otp(current_user: models.UserModel = Depends(oauth2.get_current_user)):
    otp_code= email_utils.generate_otp()
    hashed= hashing.hash(otp_code)
    await database.User.update_one({"_id":current_user["_id"]},{"$set":{"otp":hashed}})
    email= models.user_serializer(await database.User.find_one({"_id":current_user["_id"]}))["email"]
    email_utils.send_otp_email(email,otp_code)
    return {"message":"OTP sent successfully"}

@router.post("/verify-otp",status_code= status.HTTP_202_ACCEPTED)
async def verify_otp(user_otp:str,current_user: models.UserModel = Depends(oauth2.get_current_user)):
    collection= await database.User.find_one({"_id":current_user["_id"]})
    vals=models.user_otp_serializer(collection)
    stored_otp= vals["otp"]
    if hashing.verify(user_otp,stored_otp):
        if vals["role"]=="user":
            await database.User.update_one({"_id":current_user["_id"]},{"$set":{"is_verified":True}})
        return {"message": "otp successfully verified"}
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="incorrect otp")
    


@router.post('/login', response_model=schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends()):

    user= await database.User.find_one({"email":user_credentials.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    user=models.user_serializer_auth(user)
    if not hashing.verify(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    access_token = oauth2.create_access_token(data={"user_id": user["id"],"role":user["role"]})

    return {"access_token": access_token, "token_type": "bearer","role":user["role"]}

@router.get("/check-verified")
async def verify(current_user:models.UserModel=Depends(oauth2.get_current_user)):
    user=models.user_serializer(current_user)
    return {"verified":user["is_verified"]}