import os
import requests
import random
from PIL import Image, ImageDraw

BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
ORGANIZATION_ID = os.getenv("BUFFER_ORG_ID")  
CHANNEL_ID = os.getenv("BUFFER_CHANNEL_ID")    

# Generative building blocks to create endless unique developer posts
DOMAINS = [
    ("SOFTWARE ARCHITECTURE", "Decouple UI from Business Logic", "💡 Software Architecture Insight"),
    ("SYSTEMS ENGINEERING", "Optimize Memory Before You Scale", "⚙️ Systems & Performance"),
    ("CI/CD PIPELINES", "Automate Builds to Ship Faster", "🚀 DevOps Workflow"),
    ("UI/UX & STATE DIFFS", "Ensure Fluid Visual Transitions", "📱 Modern Frontend Design"),
    ("CLOUD INFRASTRUCTURE", "Design for High Availability & Fault Tolerance", "☁️️ Cloud Architecture"),
    ("DATABASE OPTIMIZATION", "Index Queries to Minimize Latency", "🗄️ Backend Performance"),
    ("STATE MANAGEMENT", "Keep Data Flow Predictable & Traceable", "🔄 Application Architecture"),
    ("SECURITY ENGINEERING", "Sanitize Inputs & Validate Every Payload", "🔒 Core Security Practice")
]

TIPS = [
    "Modular codebases reduce technical debt and make cross-platform scaling seamless.",
    "Low-level resource handling prevents memory leaks in performance-critical loops.",
    "Automated testing pipelines catch regression bugs before they ever reach production environments.",
    "Clean state transitions and reactive UI updates drastically improve user retention.",
    "Decentralized micro-services require strict contract testing and robust error boundaries."
]

HASHTAG_POOLS = [
    "#SoftwareEngineering #CleanCode #MobileDev #Programming",
    "#SystemsProgramming #Performance #Coding #TechStack",
    "#DevOps #Automation #GitHubActions #DeveloperLife",
    "#UIUX #CrossPlatform #AppDevelopment #Flutter",
    "#CloudComputing #Backend #Scalability #Architecture"
]

def generate_generative_post():
    domain, subtitle, prefix = random.choice(DOMAINS)
    tip = random.choice(TIPS)
    tags = random.choice(HASHTAG_POOLS)
    
    text_content = (
        f"{prefix}:\n\n"
        f"{tip}\n\n"
        f"Key Focus: {subtitle}\n\n"
        f"{tags}"
    )
    
    return {
        "text": text_content,
        "title": domain,
        "subtitle": subtitle
    }

def generate_tech_image(title, subtitle):
    img = Image.new("RGB", (1080, 1080), color="#0F172A") 
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([40, 40, 1040, 1040], outline="#3B82F6", width=4)
    
    draw.text((80, 200), "GENERATIVE TECH INSIGHTS", fill="#94A3B8")
    draw.text((80, 300), title[:25], fill="#FFFFFF")
    draw.text((80, 420), subtitle[:35], fill="#38BDF8")
    
    image_path = "tech_post_image.png"
    img.save(image_path)
    return image_path

def push_to_buffer():
    post = generate_generative_post()
    generate_tech_image(post["title"], post["subtitle"])
    
    # Updated mutation with correct Buffer schema error fragments
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
            __typename
            ... on PostActionPayload {
                post {
                    id
                }
            }
            ... on MutationError {
                message
            }
            ... on InvalidInputError {
                message
            }
            ... on LimitReachedError {
                message
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
                "text": post["text"],
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
            print("Successfully queued generative tech post in Buffer!")
            print(result)
        else:
            print(f"GraphQL Error: {result['errors']}")
    else:
        print(f"Request Failed: {response.status_code}, {response.text}")

if __name__ == "__main__":
    push_to_buffer()
