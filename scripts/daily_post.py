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
# headline/subline/badge are baked into the poster image overlay.
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

# Social-post captions, written separately from the image overlay text so the
# GMB post doesn't just repeat the poster headline/subline verbatim. Each one
# is a distinct, human-sounding update tied to that variant's photo. Keep
# these grounded in FACTS above — vary the wording and the keyword phrasing
# (best digital marketing course / institute / training in Aligarh), don't
# use the same opening line or the same keyword phrase two days running.
CAPTIONS = [
    # 0 classroom-teaching.jpg — new batch announcement
    "New batch of our Digital Marketing + AI course kicks off on the 10th. If you've been putting off learning digital marketing properly — ads, SEO, content, and now AI tools — this is a good month to start. Classroom training in Aligarh, ₹16,000, job assistance included once you finish. Seats are limited, so reach out early if you want in. digitalalig.com",
    # 1 certificate-1on1-a.jpg — one student receiving certificate
    "Handed over another certificate today — always a good feeling. This student put in the work through our Digital Marketing + AI course and came out the other side job-ready, not just certificate-ready. That's the part we care about most: what happens after the course, not just during it. Placement support included for everyone who completes the program. Aligarh batches, ₹16,000.",
    # 2 classroom-1.jpg — hands-on training in progress
    "This is what a regular class looks like at DigitalAlig — no long lecture slides, just live projects and real campaigns students actually run. It's why people tell us we run one of the best digital marketing courses in Aligarh: you learn by doing, not by memorizing. Digital Marketing + AI, ₹16,000, job assistance after. New batch starts the 10th.",
    # 3 certificate-group.jpg — group of graduates with certificates
    "Another batch, another set of success stories. These are students who just finished our Digital Marketing + AI course here in Aligarh — certificates in hand, ready to put it to work. Looking for the best digital marketing course or institute in Aligarh? Here's what finishing one actually looks like: hands-on campaigns, real tools, and genuine job assistance once you're done — not just a certificate for the wall. New batches start on the 10th of every month, ₹16,000 all inclusive. digitalalig.com",
    # 4 classroom-2.jpg — seats filling up
    "A few seats left for next month's Digital Marketing + AI batch. We keep our classroom sizes small on purpose — easier to actually teach people instead of just talking at a room. ₹16,000, starts the 10th, job assistance included when you're done. If you're in Aligarh and comparing digital marketing institutes, come sit in on a class before you decide.",
    # 5 certificate-1on1-b.jpg — another student, placement story
    "From sitting in our classroom to holding a completion certificate — that's the whole point of the course. Every student who finishes our Digital Marketing + AI program gets placement support, because a certificate on its own doesn't pay rent. If that's the kind of course you're after, we're in Aligarh and happy to talk you through what it actually covers.",
    # 6 classroom-3.jpg — practical training
    "A lot of people ask what makes a digital marketing course worth the money. Our answer: you should be running real ad accounts and real content calendars before you graduate, not just watching someone else do it. That's how we teach Digital Marketing + AI at DigitalAlig in Aligarh. ₹16,000, new batch every month starting the 10th, job assistance included.",
    # 7 classroom-teaching.jpg — why choose us
    "Thinking about which digital marketing institute to join in Aligarh? Here's the honest pitch: real campaigns instead of theory, AI tools folded into the course (not bolted on), and job assistance after you finish — not just a diploma. ₹16,000 for the full Digital Marketing + AI course, next batch starts the 10th. Happy to answer questions before you commit.",
    # 8 classroom-4.jpg — course overview, limited seats
    "Digital marketing without AI skills is half a toolkit these days — our course covers both together, not as an afterthought. Next batch starts the 10th in Aligarh, ₹16,000, job assistance included, and seats are limited so we can actually give people attention. If you've been comparing digital marketing courses nearby, come ask us anything first.",
    # 9 classroom-room2.jpg — career building
    "Watched a few more students build the start of a digital marketing career this month — that's really what the course is for. Hands-on Digital Marketing + AI training in Aligarh, ₹16,000, job assistance once you complete it, new batch every 10th. If you're serious about switching into this field, we'd rather you visit and ask questions than just read an ad.",
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

    caption = CAPTIONS[idx]

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
