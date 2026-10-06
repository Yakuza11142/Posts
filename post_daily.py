import os
import json
import requests
import random
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont
import imageio.v3 as iio
import numpy as np
from gtts import gTTS

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
        "MICROSERVICES & NETWORKING", 
        "Ensure low-latency service-to-service communication", 
        "🌐 Distributed Systems",
        "service.proto",
        ["syntax = \"proto3\";", "service UserService {", "  rpc GetUser (UserRequest) returns (UserResponse);", "}"],
        "#8B5CF6",
        "Protocol buffers serialize data faster than JSON for microservices."
    ),
    (
        "DATABASE SCALING & SHARDING", 
        "Distribute high-volume traffic across read replicas", 
        "📈 Database Performance",
        "pool.sql",
        ["ALTER SYSTEM SET max_connections = 500;", "CREATE TABLE shards.users_partition OF users", "FOR VALUES FROM (1) TO (100000);"],
        "#EC4899",
        "Connection pooling prevents database crashes under heavy loads."
    ),
    (
        "MOBILE STATE PATTERNS", 
        "Manage reactive UI data streams efficiently", 
        "📱 Clean Mobile Architecture",
        "bloc_state.dart",
        ["class UserBloc extends Bloc<UserEvent, UserState> {", "  UserBloc() : super(UserInitial()) {", "    on<FetchUserEvent>(_onFetch);", "  }", "}"],
        "#06B6D4",
        "Predictable state patterns make debugging complex mobile apps easier."
    ),
    (
        "CI/CD PIPELINES", 
        "Automate your builds to ship faster and safer", 
        "🚀 DevOps Workflow",
        "workflow.yml",
        ["name: Production CI", "on: [push]", "jobs:", "  deploy:", "    runs-on: ubuntu-latest"],
        "#F43F5E",
        "Automation tests your code automatically every time you save!"
    ),
    (
        "SECURITY ENGINEERING", 
        "Sanitize inputs and validate every payload", 
        "🔒 Core Security Practice",
        "security.rs",
        ["let clean_input = html_escape(input);", "assert!(token.verify_sig(), \"Unauthorized\");"],
        "#FACC15",
        "Always clean user inputs to protect your app from hackers!"
    ),
    (
        "KUBERNETES DEPLOYMENTS", 
        "Orchestrate containers for maximum uptime", 
        "⚙️ Cloud Orchestration",
        "deployment.yaml",
        ["apiVersion: apps/v1", "kind: Deployment", "metadata:", "  name: core-service"],
        "#38BDF8",
        "Kubernetes automatically restarts crashed application containers!"
    ),
    (
        "API RATE LIMITING", 
        "Protect backend servers from traffic spikes", 
        "🛡️ Backend Protection",
        "ratelimit.go",
        ["limiter := rate.NewLimiter(10, 30);", "if !limiter.Allow() {", "  return 429", "}"],
        "#34D399",
        "Rate limits prevent malicious actors from spamming your API."
    ),
    (
        "DOCKER CONTAINERIZATION", 
        "Package dependencies for uniform execution", 
        "🐳 Infrastructure Consistency",
        "Dockerfile",
        ["FROM dart:stable AS build", "WORKDIR /app", "COPY . .", "RUN dart compile exe"],
        "#4ADE80",
        "Containers ensure your code runs the exact same everywhere."
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

    domain, subtitle, prefix, filename, code_lines, accent_color, coach_tip = random.choice(available_domains)
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
        "code_lines": code_lines,
        "accent": accent_color,
        "tip": tip,
        "coach": coach_tip
    }

def get_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 46),
            ImageFont.truetype("arial.ttf", 62), # Giant headers
            ImageFont.truetype("arial.ttf", 44), # Big subtitles
            ImageFont.truetype("DejaVuSansMono.ttf", 36), # Huge code text
            ImageFont.truetype("arial.ttf", 36)
        )
    except IOError:
        try:
            return (
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.truetype("Courier", 36),
                ImageFont.load_default()
            )
        except IOError:
            return (
                ImageFont.load_default(), ImageFont.load_default(), 
                ImageFont.load_default(), ImageFont.load_default(), 
                ImageFont.load_default()
            )

def generate_assets(title, subtitle, filename, code_lines, accent_color, tip_text, coach_tip):
    """Generates an animated sequence with progressive typing and embeds a clear AI voiceover using gTTS and ffmpeg."""
    font_header, font_title, font_sub, font_code, font_footer = get_fonts()

    # --- GENERATE THE VOICE-OVER AUDIO (TTS) ---
    voice_script = f"Attention developers. Let's master {title}. {coach_tip}"
    tts = gTTS(text=voice_script, lang='en', slow=False)
    audio_path = "voice_track.mp3"
    tts.save(audio_path)

    # --- FRAME 1: The Hook & Coach Intro ---
    img1 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((60, 60), "⚡ TECH & CODE COACH", fill=accent_color, font=font_header)
    draw1.text((60, 130), title[:26], fill="#FFFFFF", font=font_title)
    draw1.text((60, 210), subtitle[:40], fill="#94A3B8", font=font_sub)

    draw1.rectangle([60, 340, 1020, 780], fill="#1E293B", outline=accent_color, width=3)
    draw1.text((100, 380), "🧑‍💻 Let's Learn Together!", fill="#38BDF8", font=font_title)
    draw1.multiline_text((100, 480), coach_tip, fill="#FFFFFF", font=font_sub, spacing=12)
    draw1.text((60, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    frame_list = []
    frame_list.extend([np.array(img1)] * 60) # ~2 seconds hook

    # --- FRAMES 2X: Progressive Line-by-Line Terminal Typing Effect ---
    current_text_lines = []
    for line in code_lines:
        current_text_lines.append(line)
        partial_code_snippet = "\n".join(current_text_lines)

        img_code = Image.new("RGB", (1080, 1080), color="#0B0F19")
        draw_code = ImageDraw.Draw(img_code)
        draw_code.text((60, 60), "⚡ TECH & CODE COACH", fill=accent_color, font=font_header)
        draw_code.text((60, 130), title[:26], fill="#FFFFFF", font=font_title)

        draw_code.rectangle([60, 220, 1020, 840], fill="#111827", outline="#1F2937", width=3)
        draw_code.ellipse([90, 245, 110, 265], fill="#EF4444")
        draw_code.ellipse([120, 245, 140, 265], fill="#F59E0B")
        draw_code.ellipse([150, 245, 170, 265], fill="#10B981")
        draw_code.text((195, 238), f"workspace — {filename}", fill="#64748B", font=font_sub)
        draw_code.multiline_text((90, 310), partial_code_snippet, fill=accent_color, font=font_code, spacing=12)
        draw_code.text((60, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

        img_code.save("tech_asset.png")
        frame_list.extend([np.array(img_code)] * 35)

    # --- FRAME 3: The Core Tip / Takeaway ---
    img3 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw3 = ImageDraw.Draw(img3)
    draw3.text((60, 60), "⚡ TECH & CODE COACH", fill=accent_color, font=font_header)
    draw3.text((60, 130), title[:26], fill="#FFFFFF", font=font_title)

    draw3.rectangle([60, 280, 1020, 780], fill="#1E293B", outline=accent_color, width=3)
    draw3.text((100, 330), "💡 Engineering Takeaway:", fill="#38BDF8", font=font_title)
    draw3.multiline_text((100, 430), tip_text[:120], fill="#FFFFFF", font=font_sub, spacing=12)
    draw3.text((60, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    frame_list.extend([np.array(img3)] * 75) # ~2.5 seconds takeaway

    temp_video_path = "temp_tech_asset.mp4"
    final_video_path = "tech_asset.mp4"
    iio.imwrite(temp_video_path, frame_list, fps=30, plugin="FFMPEG")

    merge_cmd = [
        "ffmpeg", "-y",
        "-i", temp_video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        final_video_path
    ]
    subprocess.run(merge_cmd, check=True)

    return "tech_asset.png", final_video_path

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

    subprocess.run(["git", "commit", "-m", "chore: update assets with voice narration [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)

    return image_url, video_url

def cleanup_temp_files():
    temp_files = ["voice_track.mp3", "temp_tech_asset.mp4"]
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"🧹 Cleaned up temporary file: {file}")
            except Exception as e:
                print(f"⚠️ Could not remove {file}: {e}")

def push_to_buffer():
    try:
        post = generate_generative_post()
        generate_assets(
            post["title"], post["subtitle"], post["filename"], 
            post["code_lines"], post["accent"], post["tip"], post["coach"]
        )
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
            
            # YouTube, LinkedIn, and X will all receive the high-engagement video asset!
            is_video_channel = channel_id in [
                os.getenv("BUFFER_YT_CHANNEL_ID"), 
                os.getenv("BUFFER_LINKEDIN_CHANNEL_ID"),
                os.getenv("BUFFER_TWITTER_CHANNEL_ID")
            ]
            
            asset_type = "video" if is_video_channel else "image"
            asset_url = video_url if is_video_channel else image_url

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
                    print(f"Successfully published post for Channel ID: {channel_id} (Format: {asset_type})")
                else:
                    print(f"GraphQL Error for {channel_id}: {result['errors']}")
            else:
                print(f"Request Failed for {channel_id}: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"❌ Critical error in publishing pipeline: {e}")
        raise e
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    push_to_buffer()
