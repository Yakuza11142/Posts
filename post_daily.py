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

# High-tension, polarizing engineering horror stories & production failure topics
DOMAINS = [
    (
        "PROD INCIDENT POST-MORTEM", 
        "How a single unindexed SQL query took down our entire payment gateway", 
        "🔥 Production Outage",
        "incident_log.sql",
        ["SELECT * FROM transactions", "WHERE status = 'pending'", "ORDER BY created_at DESC;"],
        "#EF4444",
        "Missing an index on high-throughput status tables triggers sequential table scans that exhaust CPU and bring down production."
    ),
    (
        "DOCKER ANTI-PATTERNS", 
        "Why your Docker image is 1.2 Gigabytes—and how to fix it", 
        "🐳 Container Bloat",
        "Dockerfile",
        ["FROM node:alpine", "COPY . .", "RUN npm install", "CMD [\"npm\", \"start\"]"],
        "#F43F5E",
        "Copying your entire workspace before running dependency installation invalidates Docker layer caching and balloons image size."
    ),
    (
        "MICROSERVICES MYTHS", 
        "Why distributed microservices are complete overkill for 95% of startups", 
        "🌐 Architecture Trap",
        "gateway.go",
        ["// 14 network hops just to", "// fetch a single user profile", "err := client.Call(...)"],
        "#8B5CF6",
        "Premature microservice decomposition introduces massive network latency, distributed transaction complexity, and debugging nightmares."
    ),
    (
        "CI/CD PIPELINE TRAPS", 
        "The silent GitHub Actions security flaw most teams completely miss", 
        "🚀 DevOps Failure",
        "workflow.yml",
        ["permissions:", "  contents: read", "  pull-requests: write # ⚠️ Dangerous injection risk"],
        "#EC4899",
        "Overly permissive GITHUB_TOKEN permissions allow compromised PR scripts to exfiltrate repository secrets and write malicious code."
    ),
    (
        "DATABASE CONNECTION STORMS", 
        "Why your connection pool is exhausting under heavy traffic spikes", 
        "📈 Backend Crash",
        "pool.rs",
        ["let pool = PgPoolOptions::new()", "    .max_connections(5000) // 💥 DB is dead", "    .connect(&url).await;"],
        "#FACC15",
        "Setting database connection limits too high overwhelms the underlying Postgres process, causing cascading timeouts across all microservices."
    ),
    (
        "STATE MANAGEMENT WARS", 
        "Why your Flutter app's reactive state tree is lagging at 60 FPS", 
        "📱 Mobile Performance",
        "bloc_leak.dart",
        ["// Rebuilding entire widget tree", "// on every single state emission", "context.watch<AppState>();"],
        "#06B6D4",
        "Calling context.watch() at the root of a complex widget tree forces massive unoptimized redraws, causing dropped frames on mobile."
    )
]

HASHTAG_POOLS = [
    "#SoftwareEngineering #DevOps #ProductionIncident #Coding #TechShorts",
    "#BackendEngineering #SystemDesign #DeveloperLife #Code #Programming",
    "#Docker #Kubernetes #CleanCode #Debugging #SoftwareArchitecture"
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
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

    domain, hook_subtitle, prefix, filename, code_lines, accent_color, incident_lesson = domain_tuple
    save_history({"last_domain": domain, "last_part": current_part})

    tags = random.choice(HASHTAG_POOLS)
    part_title_suffix = " (Part 2: The Root Cause Breakdown)" if current_part == 2 else " (Part 1)"

    # Highly polarizing, debate-inducing CTAs to trigger comments
    if "PROD INCIDENT" in domain:
        cta_question = "Have you ever taken down production with a bad SQL query? Drop your horror story below!"
    elif "DOCKER" in domain:
        cta_question = "What is the largest Docker image size you have ever inherited? Let me know!"
    elif "MICROSERVICES" in domain:
        cta_question = "Microservices vs Monolith: Which side of the fence is your team on?"
    elif "CI/CD" in domain:
        cta_question = "GitHub Actions vs GitLab CI: Which one has burned your team harder?"
    elif "DATABASE" in domain:
        cta_question = "How many max connections do you actually allow on your production pool?"
    else:
        cta_question = "What is the worst architectural mistake you have seen a team make? Tell me below!"

    text_content = (
        f"🔥 {prefix}{part_title_suffix}\n\n"
        f"⚠️ {hook_subtitle}\n\n"
        f"👇 {cta_question}\n"
        f"🔔 Subscribe for daily production incident breakdowns!\n\n"
        f"{tags}"
    )

    return {
        "text": text_content,
        "title": f"{domain}{part_title_suffix}",
        "subtitle": hook_subtitle,
        "filename": filename,
        "code_lines": code_lines,
        "accent": accent_color,
        "lesson": incident_lesson,
        "part": current_part
    }

def get_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 46),
            ImageFont.truetype("arial.ttf", 52), 
            ImageFont.truetype("arial.ttf", 38), 
            ImageFont.truetype("DejaVuSansMono.ttf", 36), 
            ImageFont.truetype("arial.ttf", 34)
        )
    except IOError:
        return (ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default())

def generate_assets(title, subtitle, filename, code_lines, accent_color, lesson_text, part_num):
    font_header, font_title, font_sub, font_code, font_footer = get_fonts()

    # High-retention voiceover script targeting the 60-second runtime with a gripping narrative hook
    voice_script = (
        f"Let us talk about a brutal production failure: {subtitle}. "
        f"Junior and senior engineers alike fall into this exact trap, resulting in catastrophic downtime, frantic midnight paging, and angry users. "
        f"Look at the exact lines of code causing the failure on your screen right now. "
        f"Notice how deceptive it looks, yet under heavy production load, it completely shatters system stability. "
        f"Here is the hard lesson learned from this incident: {lesson_text} "
        f"Drop a comment with your own production horror story, and subscribe so you never miss a critical breakdown!"
    )

    tts = gTTS(text=voice_script, lang='en', slow=False)
    audio_path = "voice_track.mp3"
    tts.save(audio_path)

    frame_list = []
    W, H = 1080, 1920  # 9:16 Vertical Resolution for YouTube Shorts

    # -------------------------------------------------------------------------
    # FRAME GROUP 1: Hook & Incident Setup (Duration: ~6 seconds / 180 frames)
    # -------------------------------------------------------------------------
    img1 = Image.new("RGB", (W, H), color="#0B0F19")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((60, 100), f"🔥 PART {part_num} — PRODUCTION INCIDENT", fill="#EF4444", font=font_header)
    draw1.text((60, 180), title[:32], fill="#FFFFFF", font=font_title)
    draw1.text((60, 260), subtitle[:48], fill="#94A3B8", font=font_sub)

    draw1.rectangle([60, 400, 1020, 1400], fill="#1E293B", outline=accent_color, width=3)
    draw1.text((100, 460), "🚨 The Production Outage", fill="#38BDF8", font=font_title)
    draw1.multiline_text((100, 580), f"What went wrong:\n\n{lesson_text}", fill="#FFFFFF", font=font_sub, spacing=16)
    draw1.text((60, 1800), "@YakubuPeter-o7k2u | Subscribe for More", fill="#475569", font=font_footer)

    frame_list.extend([np.array(img1)] * 180)

    # -------------------------------------------------------------------------
    # FRAME GROUP 2: Buggy Code Walkthrough (Duration: ~32 seconds / 960 frames)
    # -------------------------------------------------------------------------
    current_text_lines = []
    frames_per_line = max(60, 960 // max(1, len(code_lines)))
    
    for line in code_lines:
        current_text_lines.append(line)
        partial_code = "\n".join(current_text_lines)

        img_code = Image.new("RGB", (W, H), color="#0B0F19")
        draw_code = ImageDraw.Draw(img_code)
        draw_code.text((60, 100), f"🔥 INCIDENT CODE (Part {part_num})", fill=accent_color, font=font_header)
        draw_code.text((60, 180), title[:32], fill="#FFFFFF", font=font_title)

        draw_code.rectangle([60, 280, 1020, 1550], fill="#111827", outline="#1F2937", width=3)
        draw_code.text((100, 310), f"workspace — {filename}", fill="#64748B", font=font_sub)
        draw_code.multiline_text((90, 400), partial_code, fill=accent_color, font=font_code, spacing=16)
        draw_code.text((60, 1800), "@YakubuPeter-o7k2u | Like & Subscribe", fill="#475569", font=font_footer)

        frame_list.extend([np.array(img_code)] * frames_per_line)

    # Hold final code state for deep analysis (~10 seconds / 300 frames)
    frame_list.extend([np.array(img_code)] * 300)

    # -------------------------------------------------------------------------
    # FRAME GROUP 3: Takeaway & Polarizing CTA (Duration: ~12 seconds / 360 frames)
    # -------------------------------------------------------------------------
    img3 = Image.new("RGB", (W, H), color="#0B0F19")
    draw3 = ImageDraw.Draw(img3)
    draw3.text((60, 100), "💡 POST-MORTEM TAKEAWAY", fill=accent_color, font=font_header)
    draw3.text((60, 180), title[:32], fill="#FFFFFF", font=font_title)

    draw3.rectangle([60, 320, 1020, 1500], fill="#1E293B", outline=accent_color, width=3)
    draw3.text((100, 400), "🛡️ How to Prevent This:", fill="#38BDF8", font=font_title)
    draw3.multiline_text((100, 520), lesson_text[:180], fill="#FFFFFF", font=font_sub, spacing=16)

    draw3.text((100, 1200), "👇 Drop a comment with your outage story & subscribe!", fill="#34D399", font=font_sub)
    draw3.text((60, 1800), "@YakubuPeter-o7k2u", fill="#475569", font=font_footer)

    frame_list.extend([np.array(img3)] * 360)

    # Total frames: 180 + 960 + 300 + 360 = 1800 frames = Exactly 60 seconds at 30 FPS.
    temp_video_path = "temp_tech_asset.mp4"
    final_video_path = "tech_asset.mp4"
    iio.imwrite(temp_video_path, frame_list, fps=30, plugin="FFMPEG")

    # Using -af "apad" pads the audio stream with silence to match the 60s video stream,
    # preventing FFmpeg from truncating the video early.
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-af", "apad", "-shortest", final_video_path
    ], check=True)

    return "tech_asset.png", final_video_path

def commit_and_push_assets():
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "tech_asset.png", "tech_asset.mp4", HISTORY_FILE], check=True)

    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return "", ""

    subprocess.run(["git", "commit", "-m", "chore: update production incident 60s masterclass assets [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)

    repo = os.getenv("GITHUB_REPOSITORY")
    return f"https://raw.githubusercontent.com/{repo}/main/tech_asset.png", f"https://raw.githubusercontent.com/{repo}/main/tech_asset.mp4"

def push_to_buffer():
    try:
        post = generate_generative_post()
        generate_assets(
            post["title"], post["subtitle"], post["filename"], 
            post["code_lines"], post["accent"], post["lesson"], post["part"]
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
