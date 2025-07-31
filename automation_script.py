import os
import random
import time
import json
import sys
import requests
from datetime import datetime, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

# ================
# CONFIG
# ================
HUGGINGFACE_MODEL = "microsoft/Phi-3-mini-4k-instruct"  # Hugging Face text generation model, you can use other models as well
WATCH_TIME_MIN = 180  # 3 min
WATCH_TIME_MAX = 600  # 10 min
COMMENT_HISTORY_FILE = "used_comments.json"


os.environ["TOKENIZERS_PARALLELISM"] = ("false")  ## to ensure hugging face model don't get into deadlock


# Single pipeline for all tasks
llm_pipeline = pipeline(
    "text-generation",
    model=HUGGINGFACE_MODEL,
    device_map="auto",
    torch_dtype="auto",
    max_new_tokens=25,
    do_sample=True,  # To enable temperature control
    temperature=0.7  # Optional, but now recognized
)

def inject_youtube_cookies(page, cookie_file="youtube_cookies.json"):
    with open(cookie_file, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        page.context.add_cookies([cookie])

# ================
# STEP 1.1: EXTRACT VIDEO ID
# ================
def get_video_id(video_url):
    parsed_url = urlparse(video_url)
    return parse_qs(parsed_url.query).get("v", [None])[0]

# ================
# STEP 1.2: EXTRACT VIDEO TITLE
# ================
def get_video_title(video_id):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("title")
    except Exception as e:
        print(f"[ERROR] Failed to fetch video title: {e}")
        return "Friend's Horror Video"

# ================
# STEP 2: FETCH TRANSCRIPT SNIPPETS
# ================
# Some Hindi emotional keywords (can be extended - you can use your own or use an llm to figure this out)
INTERESTING_WORDS = [
    # Fear / Horror
    'डर', 'डरावना', 'भय', 'भयानक', 'सिहरन', 'चौंक', 'चीख', 'हड्डी', 'खून',
    'खूनखराबा', 'खूनी', 'काँप', 'दहशत', 'भूतिया', 'भयानकता',
    
    # Supernatural / Paranormal
    'भूत', 'प्रेत', 'आत्मा', 'चुड़ैल', 'डायन', 'शैतान', 'पिशाच',
    'राक्षस', 'प्रेतात्मा', 'जिन्न', 'अलौकिक', 'कब्र', 'कब्रिस्तान',
    'काल', 'काला जादू', 'टोना', 'वूडू', 'अजीब', 'रहस्यमय', 'रहस्य',

    # Suspense / Thriller
    'खतरा', 'खतरनाक', 'साजिश', 'शक', 'गायब', 'गुम', 'रहस्यमय', 
    'भटक', 'अनजान', 'चुपके', 'साया', 'सन्नाटा', 'अंधेरा', 'गुप्त',
    'गुप्तचर', 'सपना', 'दुःस्वप्न', 'दुःखद', 'घातक', 'घात', 'अनहोनी',
    
    # Emotional / Impactful
    'रोमांच', 'रोमांचक', 'चौंकाने', 'हैरान', 'आश्चर्य', 'अविश्वसनीय',
    'जोरदार', 'खौफनाक', 'खौफ', 'बेहोश', 'सन्न', 'झटका', 'गुस्सा',
    'खामोशी', 'तन्हाई', 'घबराहट', 'परेशान', 'खतरनाक', 'भ्रम',
    
    # Sound / Action words often used in horror
    'ठक', 'धमाका', 'चीख', 'चिल्लाहट', 'आहट', 'आवाज़', 'धमक', 'फुसफुसाहट',
    'कराह', 'सिसकी', 'फुफकार', 'भड़भड़ाहट', 'गूंज', 'बज', 'ठोकर',
    
    # Dark / Visual imagery
    'खून', 'लाश', 'मौत', 'मृत', 'कंकाल', 'कब्र', 'मृत्यु', 'अंधकार', 
    'खोपड़ी', 'सड़न', 'काला', 'धुंध', 'साया', 'अदृश्य', 'परछाई'
]

def score_snippet(snippet):
    """
    Score snippet based on interestingness:
    - Longer text gets higher score
    - Contains emotional words or punctuation
    """
    text = snippet.text
    score = len(text)  # Base score = length
    if any(word in text for word in INTERESTING_WORDS):
        score += 10
    if '!' in text or '?' in text:
        score += 5
    return score

def get_transcript_snippets(video_id, top_n=2):
    try:
        yt_api = YouTubeTranscriptApi()
        transcript_obj = yt_api.fetch(video_id=video_id, languages=['hi', 'en'])
        snippets_list = transcript_obj.snippets

        if not snippets_list:
            return []

        # Sort by interestingness score (descending)
        ranked_snippets = sorted(snippets_list, key=score_snippet, reverse=True)

        # Pick top N snippets randomly from the top 30% most interesting ones
        cutoff = max(1, int(len(ranked_snippets) * 0.3))
        top_candidates = ranked_snippets[:cutoff]
        selected_snippets = random.sample(top_candidates, min(top_n, len(top_candidates)))

        return [(s.text, s.start) for s in selected_snippets if s.text.strip()]

    except Exception as e:
        print(f"[ERROR] Unable to fetch transcript: {e}")
        return []


# ================
# STEP 3: GENERATE CONTEXT-AWARE COMMENT
# ================
def generate_comment(video_title, transcript_snippets):
    context = ""
    for text, ts in transcript_snippets:
        timestamp = str(datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%M:%S'))
        context += f"At {timestamp}, they said: '{text}'. "

    prompt = f"""
    Write a short, casual, positive YouTube comment (no explanation, no extra text) for a horror video titled '{video_title}'.
    Mention something specific from this context if possible: {context}.
    Use natural tone and emojis.
    Comment: 
    """
    comment = llm_pipeline(prompt, return_full_text=False)[0]['generated_text']
    return comment.strip()


# ================
# STEP 4: AVOID DUPLICATES
# ================
def save_comment(comment):
    if not os.path.exists(COMMENT_HISTORY_FILE):
        with open(COMMENT_HISTORY_FILE, 'w', encoding="utf-8") as f:
            json.dump([], f)
    with open(COMMENT_HISTORY_FILE, 'r') as f:
        history = json.load(f)

    if comment not in history:
        history.append(comment)
        with open(COMMENT_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    else:
        print("[INFO] Generated comment already used. Generating again...")
        return False
    return True


# ================
# STEP 5: SIMULATE WATCH + COMMENT
# ================
def watch_and_comment(video_url, comment):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)

        page = browser.new_page()

        # Inject cookies to simulate logged-in session
        inject_youtube_cookies(page)

        print(f"[INFO] Opening video: {video_url}")
        page.goto(video_url)
        page.wait_for_timeout(5000)

        # Watch for 60–90 seconds before commenting
        print("[INFO] Watching before commenting...")
        time.sleep(random.uniform(60, 90))

        # Like video
        try:
            page.click('button[aria-label="Like this video"]', timeout=5000)
            print("[INFO] Liked the video.")
        except:
            print("[WARNING] Like button not found or already liked.")

        # Scroll to comment box
        for _ in range(random.randint(2, 4)):
            page.mouse.wheel(0, random.randint(300, 600))
            time.sleep(random.uniform(1, 2))

        # Comment
        try:
            page.click('ytd-comment-simplebox-renderer')
            page.type('ytd-comment-simplebox-renderer #contenteditable-root', comment, delay=random.uniform(50, 120))
            time.sleep(random.uniform(1, 2))
            page.click('ytd-comment-simplebox-renderer #submit-button')
            print(f"[INFO] Comment posted: {comment}")
        except:
            print("[WARNING] Failed to post comment.")

        # Continue watching with random behavior
        watch_time = random.uniform(WATCH_TIME_MIN, WATCH_TIME_MAX)
        print(f"[INFO] Watching for another {watch_time:.1f} seconds...")
        start_time = time.time()
        while time.time() - start_time < watch_time:
            if random.random() < 0.2:
                page.keyboard.press('k')  # Pause/Play
                time.sleep(random.uniform(2, 5))
                page.keyboard.press('k')
            if random.random() < 0.1:
                page.keyboard.press('arrowright')  # Seek forward
            time.sleep(random.uniform(5, 10))

        browser.close()
        print("[INFO] Engagement complete.")


# ================
# MAIN
# ================
def main(video_url):
    video_id = get_video_id(video_url)
    video_title = get_video_title(video_id)
    if not video_id:
        print("[ERROR] Invalid YouTube URL.")
        return

    transcript_snippets = get_transcript_snippets(video_id)
    while True:
        comment = generate_comment(video_title, transcript_snippets)
        print("comment: {}".format(comment))
        if save_comment(comment):
            break
    # watch_and_comment(video_url, comment)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engage.py <YouTube Video URL>")
    else:
        main(sys.argv[1])

# python automation_scripy.py 'https://www.youtube.com/watch?v=C3VtQX8frao'
