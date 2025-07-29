# be-a-good-friend

# 🎥 YouTube Engagement Automation

This project is a **YouTube engagement automation tool** designed to:
1. **Fetch transcripts** of a given YouTube video.
2. **Analyze transcripts** to find interesting snippets (especially for horror/emotional content).
3. **Generate context-aware comments** using a Hugging Face LLM (e.g., `microsoft/Phi-3-mini-4k-instruct`).
4. **Simulate watch behavior** with random pauses, scrolling, liking, and commenting using **Playwright**.
5. **Avoid duplicate comments** by maintaining a history of posted comments.

---

## **⚙️ Features**
- Extract video **ID and title** from a YouTube URL.
- Fetch and rank transcript snippets using **YouTubeTranscriptApi**.
- Generate a **natural, human-like comment** with an LLM pipeline.
- Use **Playwright** to:
  - Simulate watching the video (3–10 min).
  - Like the video.
  - Post a generated comment.
- Avoid posting duplicate comments using a `used_comments.json` file.

---

## **📦 Requirements**

### **Python Libraries**
Install dependencies:
```bash
pip install -r requirements.txt
```

### **Playwright Setup**
```bash
playwright install
playwright install-deps
```

---

## **🔑 Configuration**
The main config values are defined at the top of the script:
- `HUGGINGFACE_MODEL` – Hugging Face model to use for comment generation.
- `WATCH_TIME_MIN`, `WATCH_TIME_MAX` – Randomized watch duration (in seconds).
- `COMMENT_HISTORY_FILE` – Path to the JSON file storing posted comments.

To **simulate logged-in behavior**, ensure your **YouTube cookies** are saved as:
```bash
youtube_cookies.json
```
You can export cookies using browser extensions like **EditThisCookie** or **Get cookies.txt**.

---

## **▶️ Usage**

### **Basic Command**
```bash
python automation_script.py 'https://www.youtube.com/watch?v=C3VtQX8frao'
```

### **Arguments**
- **`<YouTube Video URL>`** – The YouTube video you want to engage with.

### **Example Output**
```
[INFO] Opening video: https://www.youtube.com/watch?v=C3VtQX8frao
[INFO] Watching before commenting...
[INFO] Liked the video.
[INFO] Comment posted: "Wow! The part at 03:15 gave me chills! 😱"
[INFO] Watching for another 234.5 seconds...
[INFO] Engagement complete.
```

---

## **🧠 How It Works**
1. **Extract Video Info:**  
   `get_video_id()` and `get_video_title()` fetch the video ID and title.

2. **Fetch Transcript:**  
   `get_transcript_snippets()` pulls transcript lines (Hindi/English) and ranks them by "interestingness" using horror/emotional keywords.

3. **Generate Comments:**  
   `generate_comment()` crafts a context-aware comment using the transcript and video title.

4. **Prevent Duplicates:**  
   `save_comment()` ensures new comments are unique.

5. **Simulate Watch + Engagement:**  
   `watch_and_comment()` opens Chrome (via Playwright), simulates watching, likes the video, and posts the comment.

---

## **🚀 Quick Start**
1. **Clone this repository:**
   ```bash
   git clone https://github.com/your-username/youtube-engagement-automation.git
   cd youtube-engagement-automation
   ```

2. **Set up dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Run the script:**
   ```bash
   python automation_script.py "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

---

## **🔒 Disclaimer**
This project is for **educational purposes only**.  
Automating interactions on YouTube may violate their [Terms of Service](https://www.youtube.com/t/terms).  
Use this script responsibly and **at your own risk**.

---

## **🚀 Future Enhancements**
- Add **multilingual comment generation**.
- Integrate **proxy rotation** to mimic real user behavior.
- Add **real-time sentiment analysis** of transcripts before commenting.

