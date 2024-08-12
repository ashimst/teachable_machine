import torch
from torchvision import models, transforms
from PIL import Image

# Load pre-trained ResNet-50 model
model = models.resnet50(pretrained=True)
model.eval()

# Define the preprocessing transformations
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_image_embedding(image_path: str):
    # Load image
    image = Image.open(image_path).convert('RGB')

    # Preprocess image
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Create mini-batch as expected by the model

    # Check if GPU is available and if not, use CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    input_batch = input_batch.to(device)

    # Extract features
    with torch.no_grad():
        output = model(input_batch)
    
    # Get the feature vector (before the final classification layer)
    feature_vector = output.squeeze().cpu().numpy()
    
    return feature_vector
