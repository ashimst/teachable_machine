import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app import models


# Database configuration
DATABASE_URL = "mongodb://localhost:27017"
DATABASE_NAME = "teachable"

# Connect to MongoDB
client = AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]

# Collections
User = db.get_collection("users")
Projects= db.get_collection("projects")

async def initialize_db():
    # Check if a user document exists, if not, insert one
    user = await User.find_one()
    if not user:
        user_document = {
            "_id": ObjectId(),
            "username": "superadmin",
            "email": "test",
            "password":"test",
            "first_name": "Super",
            "last_name": "Admin",
            "phone_number": "9818615071",
            "birth_date": "2000-01-01T00:00:00Z",
            "role":models.Role.superadmin,
            "is_verified": True
        }
        await User.insert_one(user_document)
    project=await Projects.find_one()
    if not project:
        project_document={
            "_id":ObjectId(),
            "creator":"test",
            "name":"default",
            "classes":[{"label_1":["embeddings"]}]
        }
        await Projects.insert_one(project_document)
    print("database initialized successfully")
        