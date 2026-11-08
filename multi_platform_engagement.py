import os
import json
import requests

HISTORY_FILE = "posted_history.json"

# Dynamic comment triggers tailored to the topic being published
DOMAIN_COMMENTS = {
    "MICROSERVICES MYTHS": {
        "yt": "I'll start: We once split a monolith into 14 microservices too early and latency exploded by 400%. Have you seen microservices fail at your company?",
        "tw": "gRPC vs REST for microservices: Which side of the fence is your team on right now?",
        "li": "Architectural debate: At what point in user growth should a startup actually migrate from a clean monolith to microservices?"
    },
    "PROD INCIDENT POST-MORTEM": {
        "yt": "Worst database outage I've debugged was a missing index on a 10M row table. What's your worst SQL horror story?",
        "tw": "What is the fastest way your team has accidentally taken down a production database?",
        "li": "Production post-mortem breakdown: How does your engineering team enforce database migration indexing in your CI/CD pipeline?"
    },
    "DOCKER ANTI-PATTERNS": {
        "yt": "The biggest offender is usually copying node_modules or build artifacts into the context. What's the largest Docker image size you've inherited?",
        "tw": "Multi-stage builds vs Docker slim images: Which one is your go-to for keeping image size under 100MB?",
        "li": "DevOps best practice: How strictly does your infrastructure team enforce multi-stage container builds?"
    },
    "CI/CD PIPELINE TRAPS": {
        "yt": "Giving GITHUB_TOKEN pull-request write access has burned so many repos. What's your top CI/CD security rule?",
        "tw": "GitHub Actions vs GitLab CI vs Jenkins: Which pipeline framework is least headache-inducing in production?",
        "li": "Security engineering review: How are you managing secret rotation and runner permissions in high-frequency CI pipelines?"
    },
    "DATABASE CONNECTION STORMS": {
        "yt": "Setting pool limits higher doesn't solve high latency—it just crashes Postgres faster. How do you tune your DB connection pools?",
        "tw": "PgBouncer vs built-in ORM connection pooling: What's your preferred stack for high concurrency?",
        "li": "Database scalability: How does your backend architecture handle sudden 10x traffic spikes without exhausting database connections?"
    },
    "STATE MANAGEMENT WARS": {
        "yt": "Calling context.watch() at the top of a tree will drop your frame rate fast. Which state pattern do you enforce on your mobile team?",
        "tw": "Bloc vs Riverpod vs Provider: Which Flutter state pattern actually scales long-term?",
        "li": "Mobile software architecture: How do you decouple business logic from UI streams in production mobile apps?"
    }
}

DEFAULT_COMMENTS = {
    "yt": "What's the worst engineering trap you've run into with this stack? Drop your story below!",
    "tw": "What tool or pattern does your team rely on for this in production?",
    "li": "What is your team's preferred approach to solving this architectural trade-off?"
}

def load_last_domain():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_domain")
        except Exception:
            pass
    return None

def get_contextual_comment(platform):
    last_domain = load_last_domain()
    if last_domain in DOMAIN_COMMENTS:
        return DOMAIN_COMMENTS[last_domain].get(platform, DEFAULT_COMMENTS[platform])
    return DEFAULT_COMMENTS.get(platform)

def post_youtube_comment(video_id):
    comment_text = get_contextual_comment("yt")
    print(f"📺 YouTube Comment (Video: {video_id}):\n   → \"{comment_text}\"")
    # Execute YouTube API commentThreads.insert call here

def post_twitter_reply(tweet_id):
    comment_text = get_contextual_comment("tw")
    print(f"🐦 Twitter Auto-Reply (Tweet: {tweet_id}):\n   → \"{comment_text}\"")
    # Execute Twitter API v2 reply call here

def post_linkedin_comment(post_urn):
    comment_text = get_contextual_comment("li")
    print(f"💼 LinkedIn Auto-Comment (Post: {post_urn}):\n   → \"{comment_text}\"")
    # Execute LinkedIn socialActions comment call here

if __name__ == "__main__":
    print("🚀 Triggering topic-specific engagement comments...")
    # This reads posted_history.json created by postdaily.py and drops matching comments
    yt_comment = get_contextual_comment("yt")
    print(f"Target Comment Payload: {yt_comment}")
