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

BUFFER_API_URL = "https://api.buffer.com"
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")

channel_ids_env = [
    os.getenv("BUFFER_YT_CHANNEL_ID"),
    os.getenv("BUFFER_TWITTER_CHANNEL_ID"),
    os.getenv("BUFFER_LINKEDIN_CHANNEL_ID")
]
CHANNEL_IDS = [cid for cid in channel_ids_env if cid]
if not CHANNEL_IDS and os.getenv("BUFFER_CHANNEL_ID"):
    CHANNEL_IDS = [os.getenv("BUFFER_CHANNEL_ID")]

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
    "#SoftwareEngineering #CleanCode #MobileDev #Programming #TechShorts",
    "#SystemsProgramming #Performance #Coding #TechStack #Developer",
    "#DevOps #Automation #GitHubActions #DeveloperLife #Code"
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"last_domain": None, "last_part": 1}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def generate_generative_post():
    history = load_history()
    last_domain = history.get("last_domain")
    last_part = history.get("last_part", 1)

    if last_domain and last_part == 1:
        domain_tuple = next((d for d in DOMAINS if d[0] == last_domain), random.choice(DOMAINS))
        current_part = 2
    else:
        domain_tuple = random.choice(DOMAINS)
        current_part = 1

    domain, subtitle, prefix, filename, code_lines, accent_color, coach_tip = domain_tuple
    save_history({"last_domain": domain, "last_part": current_part})

    tip = random.choice(TIPS)
    tags = random.choice(HASHTAG_POOLS)

    part_title_suffix = " (Part 2: Advanced Deep Dive)" if current_part == 2 else " (Part 1)"
    
    text_content = (
        f"⚡ {prefix}{part_title_suffix}\n\n"
        f"💡 {tip}\n\n"
        f"👇 Drop a comment with your thoughts!\n"
        f"🔔 Subscribe so you never miss the next part!\n\n"
        f"{tags}"
    )

    return {
        "text": text_content,
        "title": f"{domain}{part_title_suffix}",
        "subtitle": subtitle,
        "filename": filename,
        "code_lines": code_lines,
        "accent": accent_color,
        "tip": tip,
        "coach": coach_tip,
        "part": current_part
    }

def get_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 46),
            ImageFont.truetype("arial.ttf", 54), 
            ImageFont.truetype("arial.ttf", 40), 
            ImageFont.truetype("DejaVuSansMono.ttf", 36), 
            ImageFont.truetype("arial.ttf", 36)
        )
    except IOError:
        return (ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default())

def generate_assets(title, subtitle, filename, code_lines, accent_color, tip_text, coach_tip, part_num):
    font_header, font_title, font_sub, font_code, font_footer = get_fonts()

    if part_num == 1:
        voice_script = f"Most developers fail at {title}. Watch till the end to see the fix, and subscribe for part two."
    else:
        voice_script = f"Here is the advanced breakdown for {title}. {coach_tip} Hit subscribe for daily architecture breakdowns."

    tts = gTTS(text=voice_script, lang='en', slow=False)
    audio_path = "voice_track.mp3"
    tts.save(audio_path)

    # Frame 1: High-Retention Hook
    img1 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((60, 60), f"⚡ PART {part_num} — MASTERCLASS", fill="#EF4444" if part_num == 1 else "#34D399", font=font_header)
    draw1.text((60, 130), title[:28], fill="#FFFFFF", font=font_title)
    draw1.text((60, 210), subtitle[:40], fill="#94A3B8", font=font_sub)

    draw1.rectangle([60, 340, 1020, 780], fill="#1E293B", outline=accent_color, width=3)
    draw1.text((100, 380), "🚨 Watch to the end for the secret", fill="#38BDF8", font=font_title)
    draw1.multiline_text((100, 480), coach_tip, fill="#FFFFFF", font=font_sub, spacing=12)
    draw1.text((60, 930), "@YakubuPeter-o7k2u | Subscribe for More", fill="#475569", font=font_footer)

    frame_list = [np.array(img1)] * 60

    # Terminal Typing Frames
    current_text_lines = []
    for line in code_lines:
        current_text_lines.append(line)
        partial_code = "\n".join(current_text_lines)

        img_code = Image.new("RGB", (1080, 1080), color="#0B0F19")
        draw_code = ImageDraw.Draw(img_code)
        draw_code.text((60, 60), f"⚡ CODE ARCHITECTURE (Part {part_num})", fill=accent_color, font=font_header)
        draw_code.text((60, 130), title[:28], fill="#FFFFFF", font=font_title)

        draw_code.rectangle([60, 220, 1020, 840], fill="#111827", outline="#1F2937", width=3)
        draw_code.text((195, 238), f"workspace — {filename}", fill="#64748B", font=font_sub)
        draw_code.multiline_text((90, 310), partial_code, fill=accent_color, font=font_code, spacing=12)
        draw_code.text((60, 930), "@YakubuPeter-o7k2u | Like & Subscribe", fill="#475569", font=font_footer)

        frame_list.extend([np.array(img_code)] * 35)

    # Final CTA Frame
    img3 = Image.new("RGB", (1080, 1080), color="#0B0F19")
    draw3 = ImageDraw.Draw(img3)
    draw3.text((60, 60), "⚡ ENGINEERING TAKEAWAY", fill=accent_color, font=font_header)
    draw3.text((60, 130), title[:28], fill="#FFFFFF", font=font_title)

    draw3.rectangle([60, 280, 1020, 780], fill="#1E293B", outline=accent_color, width=3)
    draw3.text((100, 330), "💡 Core Rule:", fill="#38BDF8", font=font_title)
    draw3.multiline_text((100, 430), tip_text[:120], fill="#FFFFFF", font=font_sub, spacing=12)
    
    cta_text = "👇 Part 2 is live on the channel — Subscribe!" if part_num == 1 else "👇 Drop a comment with your tech stack!"
    draw3.text((100, 650), cta_text, fill="#34D399", font=font_sub)
    draw3.text((60, 930), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    frame_list.extend([np.array(img3)] * 75)

    temp_video_path = "temp_tech_asset.mp4"
    final_video_path = "tech_asset.mp4"
    iio.imwrite(temp_video_path, frame_list, fps=30, plugin="FFMPEG")

    subprocess.run([
        "ffmpeg", "-y", "-i", temp_video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest", final_video_path
    ], check=True)

    return "tech_asset.png", final_video_path

def commit_and_push_assets():
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "tech_asset.png", "tech_asset.mp4", HISTORY_FILE], check=True)

    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return "", ""

    subprocess.run(["git", "commit", "-m", "chore: update part sequence assets [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)

    repo = os.getenv("GITHUB_REPOSITORY")
    return f"https://raw.githubusercontent.com/{repo}/main/tech_asset.png", f"https://raw.githubusercontent.com/{repo}/main/tech_asset.mp4"

def push_to_buffer():
    try:
        post = generate_generative_post()
        generate_assets(
            post["title"], post["subtitle"], post["filename"], 
            post["code_lines"], post["accent"], post["tip"], post["coach"], post["part"]
        )
        image_url, video_url = commit_and_push_assets()
        if not video_url:
            return

        time.sleep(10)
        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
            createPost(input: $input) {
                __typename
                ... on PostActionSuccess { __typename }
                ... on MutationError { message }
                ... on InvalidInputError { message }
                ... on LimitReachedError { message }
            }
        }
        """
        headers = {"Authorization": f"Bearer {BUFFER_API_KEY}", "Content-Type": "application/json"}

        for channel_id in CHANNEL_IDS:
            payload = {
                "query": mutation,
                "variables": {
                    "input": {
                        "channelId": channel_id,
                        "text": post["text"],
                        "mode": "shareNow",
                        "schedulingType": "automatic",
                        "assets": [{"video": {"url": video_url}}]
                    }
                }
            }
            if channel_id == os.getenv("BUFFER_YT_CHANNEL_ID"):
                payload["variables"]["input"]["metadata"] = {
                    "youtube": {"title": f"{post['title']} #Shorts", "categoryId": "28"}
                }

            requests.post(BUFFER_API_URL, json=payload, headers=headers)
    finally:
        for f in ["voice_track.mp3", "temp_tech_asset.mp4"]:
            if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    push_to_buffer()
