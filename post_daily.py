import os
import requests
import random
from PIL import Image, ImageDraw

BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
ORGANIZATION_ID = os.getenv("BUFFER_ORG_ID")  
CHANNEL_ID = os.getenv("BUFFER_CHANNEL_ID")    

# Expanding pool of professional tech insights
TECH_POSTS = [
    {
        "text": (
            "💡 Software Architecture Tip:\n\n"
            "Decoupling your UI layer from core business logic ensures maximum "
            "maintainability and smooth state management. Keep your code modular!\n\n"
            "#SoftwareEngineering #CleanCode #MobileDev #Programming"
        ),
        "title": "CLEAN ARCHITECTURE",
        "subtitle": "Decouple UI from Business Logic"
    },
    {
        "text": (
            "⚙️ Systems & Performance:\n\n"
            "Low-level memory management and efficient compilation pipelines play "
            "a massive role in optimizing performance-critical applications.\n\n"
            "#SystemsProgramming #Performance #Coding #Tech"
        ),
        "title": "SYSTEMS ENGINEERING",
        "subtitle": "Optimize Before You Scale"
    },
    {
        "text": (
            "🚀 Developer Workflow Insight:\n\n"
            "Automating your CI/CD build pipelines with GitHub Actions saves countless "
            "hours and catches bugs before they hit production.\n\n"
            "#DevOps #Automation #GitHubActions #Developer"
        ),
        "title": "CI/CD PIPELINES",
        "subtitle": "Automate Build & Deployment"
    },
    {
        "text": (
            "📱 Modern UI/UX Engineering:\n\n"
            "An intuitive user interface relies on fluid responsiveness, precise vector "
            "rendering, and predictable state transitions across every screen size.\n\n"
            "#UIUX #CrossPlatform #AppDevelopment #Flutter"
        ),
        "title": "UI/UX ENGINEERING",
        "subtitle": "Fluid Cross-Platform Design"
    }
]

def generate_tech_image(title, subtitle):
    """Programmatically generates a clean, dark-mode tech graphic card."""
    img = Image.new("RGB", (1080, 1080), color="#0F172A") 
    draw = ImageDraw.Draw(img)
    
    # Draw a stylish accent border frame
    draw.rectangle([40, 40, 1040, 1040], outline="#3B82F6", width=4)
    
    # Render text layout onto the graphic card
    draw.text((80, 200), "EXPERT TECH INSIGHTS", fill="#94A3B8")
    draw.text((80, 300), title, fill="#FFFFFF")
    draw.text((80, 420), subtitle, fill="#38BDF8")
    
    image_path = "tech_post_image.png"
    img.save(image_path)
    return image_path

def push_to_buffer():
    selected_post = random.choice(TECH_POSTS)
    generate_tech_image(selected_post["title"], selected_post["subtitle"])
    
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
            ... on Post {
                id
                text
                status
            }
        }
    }
    """
    
    payload = {
        "query": mutation,
        "variables": {
            "input": {
                "organizationId": ORGANIZATION_ID,
                "channelId": CHANNEL_ID,
                "text": selected_post["text"],
                "mode": "addToQueue"
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {BUFFER_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(BUFFER_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if "errors" not in result:
            print("Successfully queued daily tech post in Buffer!")
        else:
            print(f"GraphQL Error: {result['errors']}")
    else:
        print(f"Request Failed: {response.status_code}, {response.text}")

if __name__ == "__main__":
    push_to_buffer()
