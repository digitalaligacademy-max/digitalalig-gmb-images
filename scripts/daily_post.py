#!/usr/bin/env python3
"""
Generates the next GMB poster in rotation for digitalalig.com and pushes it
to this repo. Run from the repo root: python3 scripts/daily_post.py

Prints two lines to stdout for the caller (a Claude scheduled task) to use:
  CAPTION: <text to post>
  IMAGE_URL: <raw.githubusercontent.com url to attach as media>

Does not call Metricool itself — the caller does that after checking
(via getScheduledPosts) that no GMB post is already scheduled for today.
"""
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "raw")
POSTS_DIR = os.path.join(REPO_ROOT, "posts")
STATE_FILE = os.path.join(REPO_ROOT, "state.json")
RAW_BASE_URL = "https://raw.githubusercontent.com/digitalaligacademy-max/digitalalig-gmb-images/main"

YELLOW = (247, 197, 0)
NAVY = (20, 22, 28)
WHITE = (255, 255, 255)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Fixed course facts — never invent numbers/claims beyond this list.
FACTS = {
    "price": "₹16,000",
    "batch_date": "10th of every month",
    "subjects": "Digital Marketing + AI",
    "job_assistance": True,
    "location": "Aligarh",
    "website": "digitalalig.com",
}

# Content rotation: (photo filename in raw/, headline, subline, badge)
VARIANTS = [
    ("classroom-teaching.jpg", "New Batch Starts 10th!",
     "Digital Marketing + AI course • ₹16,000 • Job assistance included", "₹16,000"),
    ("certificate-1on1-a.jpg", "Real Certificates. Real Careers.",
     "Our students complete live projects and get placement support after the course.", "JOB READY"),
    ("classroom-1.jpg", "Hands-On Digital Marketing + AI Training",
     "Live projects, not just slides. Classroom batches running now in Aligarh.", "ALIGARH"),
    ("certificate-group.jpg", "DigitalAlig Success Stories",
     "Students who completed our Digital Marketing + AI course. Next batch starts 10th.", "NEW BATCH"),
    ("classroom-2.jpg", "Seats Filling for the Next Batch",
     "Digital Marketing + AI • ₹16,000 • Starts 10th • Job assistance included", "₹16,000"),
    ("certificate-1on1-b.jpg", "From Student to Job-Ready",
     "Every DigitalAlig student gets placement support after course completion.", "JOB READY"),
    ("classroom-3.jpg", "Learn Digital Marketing + AI in Aligarh",
     "Classroom and practical training — new batch starts the 10th of every month.", "ALIGARH"),
    ("classroom-teaching.jpg", "Why DigitalAlig?",
     "Real campaigns, real tools, real placement support. ₹16,000 • Starts 10th.", "₹16,000"),
    ("classroom-4.jpg", "Digital Marketing + AI Course",
     "Next batch starts 10th in Aligarh. Limited seats, job assistance included.", "NEW BATCH"),
    ("classroom-room2.jpg", "Build a Career in Digital Marketing + AI",
     "Hands-on training every month in Aligarh — job assistance after course completion.", "JOB READY"),
]


def f(path, size):
    return ImageFont.truetype(path, size)


def wrapped(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_post(src_path, out_path, headline, subline, badge):
    img = Image.open(src_path).convert("RGB")
    target_w, target_h = 1080, 1350
    iw, ih = img.size
    target_ratio = target_w / target_h
    cur_ratio = iw / ih
    if cur_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        x0 = (iw - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        y0 = (ih - new_h) // 2
        img = img.crop((0, y0, iw, y0 + new_h))
    img = img.resize((target_w, target_h), Image.LANCZOS)

    overlay = Image.new("L", img.size, 0)
    od = ImageDraw.Draw(overlay)
    grad_h = 760
    for i in range(grad_h):
        y = target_h - grad_h + i
        alpha = int(235 * (i / grad_h) ** 1.4)
        od.line([(0, y), (target_w, y)], fill=alpha)
    black = Image.new("RGB", img.size, (0, 0, 0))
    base = Image.composite(black, img, overlay)

    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, target_w, 14], fill=YELLOW)
    pad = 56
    d.ellipse([pad, 40, pad + 34, 74], fill=YELLOW)
    d.text((pad + 48, 42), "DIGITALALIG", font=f(BOLD, 30), fill=WHITE)
    d.text((pad + 48, 78), "LEARN DIGITAL MARKETING AT ALIGARH", font=f(REG, 15), fill=(226, 226, 226))

    bf = f(BOLD, 24)
    tw = d.textlength(badge, font=bf)
    bx0, by0 = target_w - pad - tw - 36, 42
    bx1, by1 = target_w - pad, by0 + 46
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=23, fill=YELLOW)
    d.text((bx0 + 18, by0 + 10), badge, font=bf, fill=NAVY)

    hl_font = f(BOLD, 58)
    lines = wrapped(d, headline, hl_font, target_w - pad * 2)
    y = target_h - 70 - len(lines) * 66
    sub_font = f(REG, 30)
    sub_lines = wrapped(d, subline, sub_font, target_w - pad * 2)
    y -= (len(sub_lines) * 40 + 20)
    for line in lines:
        d.text((pad, y), line, font=hl_font, fill=WHITE)
        y += 66
    y += 14
    for line in sub_lines:
        d.text((pad, y), line, font=sub_font, fill=(225, 225, 225))
        y += 40

    d.rectangle([0, target_h - 56, target_w, target_h], fill=YELLOW)
    d.text((pad, target_h - 48), "New batch starts 10th every month  •  digitalalig.com",
            font=f(BOLD, 22), fill=NAVY)

    base.save(out_path, "JPEG", quality=88)


def main():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as fh:
            state = json.load(fh)
    else:
        state = {"next_index": 0}

    idx = state["next_index"] % len(VARIANTS)
    photo, headline, subline, badge = VARIANTS[idx]

    import datetime
    today = datetime.date.today().isoformat()
    out_name = f"post_{today}_{idx}.jpg"
    os.makedirs(POSTS_DIR, exist_ok=True)
    out_path = os.path.join(POSTS_DIR, out_name)

    make_post(os.path.join(RAW_DIR, photo), out_path, headline, subline, badge)

    caption = f"{headline} {subline}".strip()

    state["next_index"] = idx + 1
    with open(STATE_FILE, "w") as fh:
        json.dump(state, fh, indent=2)

    rel_path = f"posts/{out_name}"
    print(f"CAPTION: {caption}")
    print(f"IMAGE_URL: {RAW_BASE_URL}/{rel_path}")
    print(f"LOCAL_PATH: {out_path}")
    print(f"VARIANT_INDEX: {idx}")


if __name__ == "__main__":
    main()
