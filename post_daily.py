import os
import requests
import random
from PIL import Image, ImageDraw

# API Configuration and Environment Endpoints
BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")

# Collect all three channel IDs from your GitHub Secrets into a list for looping
channel_ids_env = [
    os.getenv("BUFFER_YT_CHANNEL_ID"),
    os.getenv("BUFFER_TWITTER_CHANNEL_ID"),
    os.getenv("BUFFER_LINKEDIN_CHANNEL_ID")
]
# Filter out any empty values
CHANNEL_IDS = [cid for cid in channel_ids_env if cid]

# Fallback check if individual channel secrets weren't used, check for single BUFFER_CHANNEL_ID
if not CHANNEL_IDS:
    single_channel = os.getenv("BUFFER_CHANNEL_ID")
    if single_channel:
        CHANNEL_IDS = [single_channel]

# Fail-safe validation check: Stops execution immediately if core credentials are missing
if not BUFFER_API_KEY or not CHANNEL_IDS:
    raise ValueError("❌ Missing GitHub Secrets! Ensure BUFFER_API_KEY and Channel IDs are properly configured.")

# Generative text blocks to create unique developer content every run
DOMAINS = [
    ("SOFTWARE ARCHITECTURE", "Decouple UI from Business Logic", "💡 Software Architecture Insight"),
    ("SYSTEMS ENGINEERING", "Optimize Memory Before You Scale", "⚙️ Systems & Performance"),
    ("CI/CD PIPELINES", "Automate Builds to Ship Faster", "🚀 DevOps Workflow"),
    ("UI/UX & STATE DIFFS", "Ensure Fluid Visual Transitions", "📱 Modern Frontend Design"),
    ("CLOUD INFRASTRUCTURE", "Design for High Availability & Fault Tolerance", "☁️ Cloud Architecture"),
    ("DATABASE OPTIMIZATION", "Index Queries to Minimize Latency", "🗄 Backend Performance"),
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
    """Randomly selects and pieces together a unique tech post combination."""
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
    """Draws a clean, dark-mode 1080x1080 graphic card with Pillow for social media rendering."""
    img = Image.new("RGB", (1080, 1080), color="#0F172A") # Deep Slate background
    draw = ImageDraw.Draw(img)
    
    # Draw accent border frame
    draw.rectangle([40, 40, 1040, 1040], outline="#3B82F6", width=4)
    
    # Render typography fields
    draw.text((80, 200), "GENERATIVE TECH INSIGHTS", fill="#94A3B8")
    draw.text((80, 300), title[:25], fill="#FFFFFF")
    draw.text((80, 420), subtitle[:35], fill="#38BDF8")
    
    image_path = "tech_post_image.png"
    img.save(image_path)
    return image_path

def push_to_buffer():
    """Builds the post, generates the image asset, and broadcasts via GraphQL mutation to all channels."""
    post = generate_generative_post()
    generate_tech_image(post["title"], post["subtitle"])
    
    # Updated mutation schema matching Buffer's expected CreatePostInput fields
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
            __typename
            ... on PostActionSuccess {
                __typename
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
    
    headers = {
        "Authorization": f"Bearer {BUFFER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Loop through each platform's channel ID and queue the post independently
    for channel_id in CHANNEL_IDS:
        payload = {
            "query": mutation,
            "variables": {
                "input": {
                    "channelId": channel_id,
                    "text": post["text"],
                    "mode": "addToQueue",
                    "schedulingType": "automatic"
                }
            }
        }

        response = requests.post(BUFFER_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if "errors" not in result:
                print(f"Successfully queued post for Channel ID: {channel_id}")
            else:
                print(f"GraphQL Error for {channel_id}: {result['errors']}")
        else:
            print(f"Request Failed for {channel_id}: {response.status_code}, {response.text}")

if __name__ == "__main__":
    push_to_buffer()
