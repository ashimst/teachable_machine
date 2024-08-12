from typing import List
from uuid import uuid4
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, File, Form, UploadFile, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
import joblib
import pydantic
import os 
from app import oauth2, models,database,schemas
from ..utilities import hashing,email_utils,random_generator,utils
from sklearn.neighbors import KNeighborsClassifier
import numpy as np


router=APIRouter(prefix='/projects',
                 tags=['Project'])



@router.post("/create-project")
async def create_project(project_name: str, current_user: models.UserModel = Depends(oauth2.get_verified_user)):
    user = models.user_serializer(current_user)
    
    # Create the initial project data
    project_data = {
        "_id": ObjectId(),  # Generate a new ObjectId
        "project_id": random_generator.generate_event_url(user["username"]),
        "creator": user['username'],
        "name": project_name,
        "classes": [],
        "model": None
    }
    
    # Create a ProjectModel instance for validation
    try:
        project_model = models.ProjectModel(**project_data)  # Unpack the dictionary
    except pydantic.ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    
    # Insert the new project into the database
    try:
        result = await database.Projects.insert_one(project_model.model_dump(by_alias=True))  # Await the async operation
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    if result.inserted_id:
        # Convert the ObjectId to a string before returning
        project_data['_id'] = str(project_data['_id'])
        return {"message": "Project created successfully", "project": project_data}
    else:
        raise HTTPException(status_code=500, detail="Failed to create project")

@router.get("/user-projects")
async def get_user_projects(current_user: models.UserModel = Depends(oauth2.get_verified_user)):
    user = models.user_serializer(current_user)
    
    try:
        # Query the database for all projects created by the current user
        projects_cursor = database.Projects.find({"creator": user['username']})
        projects = await projects_cursor.to_list(length=None)  # Convert the cursor to a list
        
        # Convert ObjectId to string for all projects
        for project in projects:
            project['_id'] = str(project['_id'])
        
        return {"projects": projects}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")

UPLOAD_DIRECTORY = "./uploaded_images/"

@router.post("/class")
async def upload_images(
    project_id: str = Form(...),
    label: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: models.UserModel = Depends(oauth2.get_verified_user)
):
    user = models.user_serializer(current_user)

    # Ensure the upload directory exists
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    # Extract embeddings for each uploaded file
    embeddings = []
    for file in files:
        try:
            # Save the uploaded file to the upload directory
            file_id = str(uuid4())
            file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}_{file.filename}")
            
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())

            # Extract the image embedding
            embedding = np.array(utils.extract_image_embedding(file_path))
            embeddings.append(embedding)

        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error processing file {file.filename}: {str(e)}")

        finally:
            # Optionally remove the file after processing to save space
            if os.path.exists(file_path):
                os.remove(file_path)

    try:
        # Find the project in the database
        project_doc = await database.Projects.find_one({"project_id": project_id})
        
        if project_doc is None:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_doc = models.project_serializer(project_doc)
        
        # Check if the current user is the creator of the project
        if project_doc["creator"] == user["username"]:
            
            # Create a new class entry with the label and embeddings
            new_class = {"label": label, "embeddings": embeddings}

            # If the classes list is None, initialize it to an empty list
            if project_doc.get("classes") is None:
                project_doc["classes"] = []

            # Append the new class to the classes list using $push
            result = await database.Projects.update_one(
                {"project_id": project_id},
                {"$push": {"classes": new_class}}
            )

            if result.modified_count == 1:
                return {"message": "Class successfully uploaded"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update project with new class")

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account is unauthorized to perform that action"
            )

    except Exception as e:
        # Log the exception details for debugging
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



# Define the directory where models will be saved
MODEL_DIRECTORY = "./models/"

@router.post("/train")
async def train_knn(
    project_id: str,
    current_user: models.UserModel = Depends(oauth2.get_verified_user)
):
    try:
        # Fetch project document from the database
        project_doc = await database.Projects.find_one({"project_id": project_id})

        if project_doc is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Ensure the current user is the creator of the project
        user = models.user_serializer(current_user)
        if project_doc["creator"] != user["username"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account is unauthorized to perform that action"
            )

        # Extract labels and embeddings
        classes = project_doc.get("classes", [])
        if not classes:
            raise HTTPException(status_code=400, detail="No classes available for training")

        labels = [cls["label"] for cls in classes]
        embeddings = [embedding for cls in classes for embedding in cls["embeddings"]]

        if not embeddings or not labels:
            raise HTTPException(status_code=400, detail="No embeddings or labels available for training")

        # Prepare data for KNN
        X_train = embeddings
        y_train = labels

        # Train KNN model
        knn = KNeighborsClassifier(n_neighbors=3)  # Adjust parameters as needed
        knn.fit(X_train, y_train)

        # Save the model
        model_filename = f"{project_id}_knn_model.joblib"
        model_path = os.path.join(MODEL_DIRECTORY, model_filename)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(knn, model_path)

        # Update the project document with the model path
        result = await database.Projects.update_one(
            {"project_id": project_id},
            {"$set": {"model_path": model_path}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update project with model path")

        return {"message": "Model trained and saved successfully", "model_path": model_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

@router.post("/classify")
async def classify_image(
    project_id: str,
    file: UploadFile = File(...),
    current_user: models.UserModel = Depends(oauth2.get_verified_user)
):
    try:
        # Fetch project document from the database
        project_doc = await database.Projects.find_one({"project_id": project_id})

        if project_doc is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Ensure the current user is the creator of the project
        user = models.user_serializer(current_user)
        if project_doc["creator"] != user["username"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account is unauthorized to perform that action"
            )

        # Retrieve the model path
        model_path = project_doc.get("model_path")
        if model_path is None or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Model not found")

        # Load the model
        knn = joblib.load(model_path)

        # Save the uploaded image
        file_id = str(uuid4())
        file_path = os.path.join("temp", f"{file_id}_{file.filename}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # Extract the image embedding
        embedding = utils.extract_image_embedding(file_path)

        # Perform classification
        prediction = knn.predict([embedding])
        predicted_label = prediction[0]

        # Clean up the temporary file
        os.remove(file_path)

        return {"predicted_label": predicted_label}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")