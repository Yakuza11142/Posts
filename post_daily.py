import os
import json
import requests
import random
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont
import imageio.v3 as iio
import numpy as np

# API Configuration and Environment Endpoints
BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")

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

HISTORY_FILE = "posted_history.json"

DOMAINS = [
    (
        "SOFTWARE ARCHITECTURE", 
        "Are you decoupling UI from Business Logic correctly?", 
        "💡 Architecture Insight",
        "repository.dart",
        "// Clean separation of concerns\nclass UserRepository {\n  Future<User> fetchUser() async {\n    return await _apiClient.get();\n  }\n}",
        "#38BDF8",
        "🤖 Coach Tip: Keep your display code separate from your data fetching!"
    ),
    (
        "SYSTEMS ENGINEERING", 
        "Are you optimizing memory before you scale?", 
        "⚙️ Performance & Memory",
        "memory.rs",
        "unsafe {\n  let ptr = alloc::alloc(layout);\n  ptr::write(ptr, data);\n}",
        "#4ADE80",
        "🤖 Coach Tip: Low-level pointers let us manage computer memory directly."
    ),
    (
        "CI/CD PIPELINES", 
        "Automate your builds to ship faster and safer", 
        "🚀 DevOps Workflow",
        "workflow.yml",
        "name: Production CI\non: [push]\njobs:\n  deploy:\n    runs-on: ubuntu-latest",
        "#F43F5E",
        "🤖 Coach Tip: Automation tests your code automatically every time you save!"
    ),
    (
        "UI/UX & STATE DIFFS", 
        "Ensure fluid visual transitions across devices", 
        "📱 Modern Frontend Design",
        "anim_builder.dart",
        "AnimatedBuilder(\n  animation: _controller,\n  builder: (context, child) => FadeTransition()\n)",
        "#A855F7",
        "🤖 Coach Tip: Smooth animations make apps feel alive and fun to use!"
    ),
    (
        "CLOUD INFRASTRUCTURE", 
        "Design for high availability and fault tolerance", 
        "☁️ Cloud Architecture",
        "main.tf",
        "resource \"aws_lb\" \"ingress\" {\n  internal = false\n  load_balancer_type = \"application\"\n}",
        "#FB923C",
        "🤖 Coach Tip: Cloud servers keep apps running even if one computer crashes."
    ),
    (
        "DATABASE OPTIMIZATION", 
        "Index your queries to minimize latency", 
        "🄲 Backend Performance",
        "query.sql",
        "CREATE INDEX idx_user_metrics \nON accounts(email) \nWHERE status = 'active';",
        "#34D399",
        "🤖 Coach Tip: Indexes act like a book table of contents to find data instantly."
    ),
    (
        "STATE MANAGEMENT", 
        "Keep data flow predictable and traceable", 
        "🔄 Application Architecture",
        "notifier.dart",
        "final userStateProvider = StateProvider<User?>(\n  (ref) => null\n);",
        "#38BDF8",
        "🤖 Coach Tip: State providers help track what information your app currently holds."
    ),
    (
        "SECURITY ENGINEERING", 
        "Sanitize inputs and validate every payload", 
        "🔒 Core Security Practice",
        "security.rs",
        "let clean_input = html_escape(input);\nassert!(token.verify_sig(), \"Unauthorized\");",
        "#FACC15",
        "🤖 Coach Tip: Always clean user inputs to protect your app from hackers!"
    )
]

TIPS = [
    "Modular codebases reduce technical debt and make cross-platform scaling seamless.",
    "Low-level resource handling prevents memory leaks in performance-critical loops.",
    "Automated testing pipelines catch regression bugs before they ever reach production.",
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

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def generate_generative_post():
    history = load_history()
    available_domains = [d for d in DOMAINS if d[0] not in history[-5:]]
    if not available_domains:
        available_domains = DOMAINS

    domain, subtitle, prefix, filename, code_snippet, accent_color, coach_tip = random.choice(available_domains)
    tip = random.choice(TIPS)
    tags = random.choice(HASHTAG_POOLS)

    history.append(domain)
    save_history(history)

    text_content = (
        f"{prefix}:\n\n"
        f"{tip}\n\n"
        f"Key Focus: {subtitle}\n\n"
        f"{tags}"
    )

    return {
        "text": text_content,
        "title": domain,
        "subtitle": subtitle,
        "filename": filename,
        "code": code_snippet,
        "accent": accent_color,
        "tip": tip,
        "coach": coach_tip
    }

def get_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 40),
            ImageFont.truetype("arial.ttf", 48),
            ImageFont.truetype("arial.ttf", 34),
            ImageFont.truetype("DejaVuSansMono.ttf", 28),
            ImageFont.truetype("arial.ttf", 30)
        )
    except IOError:
        try:
            return (
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.truetype("Courier", 28),
                ImageFont.load_default()
            )
        except IOError:
            return (
                ImageFont.load_default(), ImageFont.load_default(), 
                ImageFont.load_default(), ImageFont.load_default(), 
                ImageFont.load_default()
            )

def generate_assets(title, subtitle, filename, code_snippet, accent_color, tip_text, coach_tip):
    """Generates an 11-second multi-step animated video sequence featuring Code Coach guidance."""
    font_header, font_title, font_sub, font_code, font_footer = get_fonts()

    # --- FRAME 1: The Hook & Coach Intro ---
    img1 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((80, 80), "⚡ GENERATIVE TECH & CODE COACH", fill=accent_color, font=font_header)
    draw1.text((80, 160), title[:30], fill="#FFFFFF", font=font_title)
    draw1.text((80, 240), subtitle[:45], fill="#94A3B8", font=font_sub)
    
    draw1.rectangle([80, 380, 1000, 750], fill="#1E293B", outline=accent_color, width=2)
    draw1.text((120, 420), "🧑‍💻 Let's Learn Together!", fill="#38BDF8", font=font_title)
    draw1.multiline_text((120, 520), coach_tip, fill="#FFFFFF", font=font_sub, spacing=10)
    draw1.text((80, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    # --- FRAME 2: The Terminal Code Solution ---
    img2 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw2 = ImageDraw.Draw(img2)
    draw2.text((80, 80), "⚡ GENERATIVE TECH & CODE COACH", fill=accent_color, font=font_header)
    draw2.text((80, 160), title[:30], fill="#FFFFFF", font=font_title)
    
    draw2.rectangle([80, 240, 1000, 820], fill="#111827", outline="#1F2937", width=2)
    draw2.ellipse([110, 265, 128, 283], fill="#EF4444")
    draw2.ellipse([140, 265, 158, 283], fill="#F59E0B")
    draw2.ellipse([170, 265, 188, 283], fill="#10B981")
    draw2.text((215, 260), f"workspace — {filename}", fill="#64748B", font=font_sub)
    draw2.multiline_text((110, 330), code_snippet, fill=accent_color, font=font_code, spacing=10)
    draw2.text((80, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    # --- FRAME 3: The Core Tip / Takeaway ---
    img3 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw3 = ImageDraw.Draw(img3)
    draw3.text((80, 80), "⚡ GENERATIVE TECH & CODE COACH", fill=accent_color, font=font_header)
    draw3.text((80, 160), title[:30], fill="#FFFFFF", font=font_title)
    
    draw3.rectangle([80, 300, 1000, 720], fill="#1E293B", outline=accent_color, width=2)
    draw3.text((120, 350), "💡 Engineering Takeaway:", fill="#38BDF8", font=font_title)
    draw3.multiline_text((120, 450), tip_text[:120], fill="#FFFFFF", font=font_sub, spacing=10)
    draw3.text((80, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    image_path = "tech_asset.png"
    img2.save(image_path)

    f_data1 = np.array(img1)
    f_data2 = np.array(img2)
    f_data3 = np.array(img3)

    frame_list = []
    frame_list.extend([f_data1] * 90)   # Step 1: ~3.0 seconds (Coach Intro)
    frame_list.extend([f_data2] * 150)  # Step 2: ~5.0 seconds (Code IDE Reading Time)
    frame_list.extend([f_data3] * 90)   # Step 3: ~3.0 seconds (Takeaway Summary)

    video_path = "tech_asset.mp4"
    iio.imwrite(video_path, frame_list, fps=30, plugin="FFMPEG")

    return image_path, video_path

def commit_and_push_assets():
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "tech_asset.png", "tech_asset.mp4", HISTORY_FILE], check=True)
    
    diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    
    repo = os.getenv("GITHUB_REPOSITORY")
    image_url = f"https://raw.githubusercontent.com/{repo}/main/tech_asset.png"
    video_url = f"https://raw.githubusercontent.com/{repo}/main/tech_asset.mp4"

    if diff_result.returncode == 0:
        print("ℹ No asset changes detected. Skipping commit and push.")
        return image_url, video_url

    subprocess.run(["git", "commit", "-m", "chore: update coach-guided multi-step assets [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)
    
    return image_url, video_url

def push_to_buffer():
    post = generate_generative_post()
    generate_assets(post["title"], post["subtitle"], post["filename"], post["code"], post["accent"], post["tip"], post["coach"])
    image_url, video_url = commit_and_push_assets()

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
                print(f"Successfully published coach-guided post for Channel ID: {channel_id}")
            else:
                print(f"GraphQL Error for {channel_id}: {result['errors']}")
        else:
            print(f"Request Failed for {channel_id}: {response.status_code}, {response.text}")

if __name__ == "__main__":
    push_to_buffer()
