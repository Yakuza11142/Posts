import os
import requests
import random
import subprocess
import time
from PIL import Image, ImageDraw
import imageio.v3 as iio

# API Configuration and Environment Endpoints
BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")

# Collect all three channel IDs from your GitHub Secrets into a list for looping
channel_ids_env = [
    os.getenv("BUFFER_YT_CHANNEL_ID"),
    os.getenv("BUFFER_TWITTER_CHANNEL_ID"),
    os.getenv("BUFFER_LINKEDIN_CHANNEL_ID")
]
CHANNEL_IDS = [cid for cid in channel_ids_env if cid]

if not CHANNEL_IDS:
    single_channel = os.getenv("BUFFER_CHANNEL_ID")
    if single_channel:
        CHANNEL_IDS = [single_channel]

if not BUFFER_API_KEY or not CHANNEL_IDS:
    raise ValueError("❌ Missing GitHub Secrets! Ensure BUFFER_API_KEY and Channel IDs are properly configured.")

DOMAINS = [
    ("SOFTWARE ARCHITECTURE", "Decouple UI from Business Logic", "💡 Software Architecture Insight"),
    ("SYSTEMS ENGINEERING", "Optimize Memory Before You Scale", "⚙️ Systems & Performance"),
    ("CI/CD PIPELINES", "Automate Builds to Ship Faster", "🚀 DevOps Workflow"),
    ("UI/UX & STATE DIFFS", "Ensure Fluid Visual Transitions", "📱 Modern Frontend Design"),
    ("CLOUD INFRASTRUCTURE", "Design for High Availability & Fault Tolerance", "☁️ Cloud Architecture"),
    ("DATABASE OPTIMIZATION", "Index Queries to Minimize Latency", "🄲 Backend Performance"),
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

def generate_assets(title, subtitle):
    """Generates a clean text card (without bounding boxes) and a 3-second MP4 video."""
    # 1. Generate Image Card cleanly without outer borders
    img = Image.new("RGB", (1080, 1080), color="#0F172A")
    draw = ImageDraw.Draw(img)
    
    draw.text((80, 220), "GENERATIVE TECH INSIGHTS", fill="#94A3B8")
    draw.text((80, 320), title[:25], fill="#FFFFFF")
    draw.text((80, 460), subtitle[:35], fill="#38BDF8")

    image_path = "tech_asset.png"
    img.save(image_path)

    # 2. Convert Image to a 3-second MP4 video for YouTube Shorts using FFMPEG plugin
    video_path = "tech_asset.mp4"
    frame = iio.imread(image_path)
    # Write 90 frames (3 seconds at 30fps)
    iio.imwrite(video_path, [frame] * 90, fps=30, plugin="FFMPEG")

    return image_path, video_path

def commit_and_push_assets():
    """Commits and pushes generated assets to GitHub to get permanent public raw URLs."""
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "tech_asset.png", "tech_asset.mp4"], check=True)
    subprocess.run(["git", "commit", "-m", "chore: update automated post assets [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)

    repo = os.getenv("GITHUB_REPOSITORY")
    image_url = f"https://raw.githubusercontent.com/{repo}/main/tech_asset.png"
    video_url = f"https://raw.githubusercontent.com/{repo}/main/tech_asset.mp4"
    return image_url, video_url

def push_to_buffer():
    post = generate_generative_post()
    generate_assets(post["title"], post["subtitle"])
    image_url, video_url = commit_and_push_assets()

    # Wait 10 seconds for GitHub's raw CDN to index the new files globally
    print("Waiting for assets to propagate on GitHub CDN...")
    time.sleep(10)

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

    for channel_id in CHANNEL_IDS:
        is_youtube = channel_id == os.getenv("BUFFER_YT_CHANNEL_ID")
        asset_type = "video" if is_youtube else "image"
        asset_url = video_url if is_youtube else image_url

        post_input = {
            "channelId": channel_id,
            "text": post["text"],
            "mode": "shareNow",
            "schedulingType": "automatic",
            "assets": [{
                asset_type: {
                    "url": asset_url
                }
            }]
        }

        # Inject YouTube-specific metadata required by Buffer's API for video uploads
        if is_youtube:
            post_input["metadata"] = {
                "youtube": {
                    "title": post["title"][:100],
                    "categoryId": "28"
                }
            }

        payload = {
            "query": mutation,
            "variables": {
                "input": post_input
            }
        }

        response = requests.post(BUFFER_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if "errors" not in result:
                print(f"Successfully published post for Channel ID: {channel_id}")
            else:
                print(f"GraphQL Error for {channel_id}: {result['errors']}")
        else:
            print(f"Request Failed for {channel_id}: {response.status_code}, {response.text}")

if __name__ == "__main__":
    push_to_buffer()
