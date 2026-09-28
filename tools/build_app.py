import csv
import hashlib
import html as html_module
import json
import re
import sys
from pathlib import Path

import yaml

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent

sys.path.insert(0, str(TOOLS_DIR))
from wrong_scripts import WRONG_SCRIPTS

CSV_PATH = ROOT_DIR / "data" / "phonebook.csv"
SCRIPTS_PATH = ROOT_DIR / "data" / "call_scripts.yaml"
CLASSIFIEDS_PATH = ROOT_DIR / "printables" / "classifieds.html"
CONFIG_PATH = ROOT_DIR / "data" / "app_config.yaml"
TEMPLATE_PATH = ROOT_DIR / "app" / "template.html"
OUT_PATH = ROOT_DIR / "app" / "index.html"


def clean_html_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return html_module.unescape(s).strip()


def extract_decoy_ads(classifieds_path: str, exclude_numbers: set):
    """Auto-extract phone numbers printed in classifieds.html ads (other than
    the real special numbers) so dialing them in the app echoes back that
    same ad's own headline/body — these are pure flavor, not real clues."""
    with open(classifieds_path) as f:
        page = f.read()

    ad_blocks = re.findall(r'<div class="ad[^"]*">(.*?)</div>', page, re.S)
    decoys = []
    seen_phones = set()
    for block in ad_blocks:
        phone_m = re.search(r'<span class="phone">(.*?)</span>', block, re.S)
        if not phone_m:
            continue
        digits_m = re.search(r"(\d+)", clean_html_text(phone_m.group(1)))
        if not digits_m:
            continue
        phone = digits_m.group(1)
        if phone in exclude_numbers or phone in seen_phones:
            continue
        seen_phones.add(phone)

        headline_m = re.search(r'<span class="headline">(.*?)</span>', block, re.S)
        body_m = re.search(r'<span class="body">(.*?)</span>', block, re.S)
        headline = clean_html_text(headline_m.group(1)) if headline_m else ""
        body = clean_html_text(body_m.group(1)) if body_m else ""
        decoys.append({
            "phone": phone,
            "name": headline,
            "role": "decoy",
            "scriptIndex": 0,
            "script": body,
        })
    return decoys


def script_index_for(phone: str) -> int:
    # Stable across runs/machines (unlike Python's built-in hash()), so a
    # given phone number always maps to the same wrong-number script.
    digest = hashlib.md5(phone.encode("utf-8")).hexdigest()
    return int(digest, 16) % len(WRONG_SCRIPTS)


with open(CSV_PATH, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with open(SCRIPTS_PATH) as f:
    call_scripts = yaml.safe_load(f)

with open(CONFIG_PATH) as f:
    app_config = yaml.safe_load(f)

clue_script_by_phone = {c["phone"]: c["script"] for c in call_scripts["clues"]}
special_script_by_phone = {s["phone"]: s["script"] for s in call_scripts["special"]}

phonebook = []
for r in rows:
    entry = {
        "phone": r["phone"],
        "name": f"{r['first_name']} {r['last_name']}".strip(),
        "role": r["role"],
        "scriptIndex": script_index_for(r["phone"]),
    }
    if r["role"] == "clue":
        entry["script"] = clue_script_by_phone[r["phone"]]
    elif r["role"] == "special":
        entry["script"] = special_script_by_phone[r["phone"]]
    phonebook.append(entry)

target_rows = [r for r in phonebook if r["role"] == "target"]
assert len(target_rows) == 1, f"expected exactly 1 target, found {len(target_rows)}"
clue_rows = [r for r in phonebook if r["role"] == "clue"]
assert len(clue_rows) == 5, f"expected exactly 5 clue rows, found {len(clue_rows)}"
special_rows = [r for r in phonebook if r["role"] == "special"]
assert {r["phone"] for r in special_rows} == set(special_script_by_phone), "special rows in CSV don't match call_scripts.yaml"

# Decoy numbers printed in classifieds.html (not the real specials) just echo
# their own ad text back — auto-extracted so they stay in sync with the ads
# without hand-authoring a script per number. Not written to phonebook.csv;
# these aren't part of the elimination game, only the physical prop.
existing_phones = {r["phone"] for r in phonebook}
decoy_rows = extract_decoy_ads(CLASSIFIEDS_PATH, exclude_numbers=set(special_script_by_phone))
decoy_rows = [d for d in decoy_rows if d["phone"] not in existing_phones]
phonebook.extend(decoy_rows)

TARGET_SCRIPT = app_config["target_script"]

with open(TEMPLATE_PATH) as f:
    template = f.read()

html = (
    template
    .replace("__PHONEBOOK_JSON__", json.dumps(phonebook))
    .replace("__WRONG_SCRIPTS_JSON__", json.dumps(WRONG_SCRIPTS, ensure_ascii=False))
    .replace("__TARGET_SCRIPT_JSON__", json.dumps(TARGET_SCRIPT, ensure_ascii=False))
    .replace("__SPECIAL_NUMBERS_JSON__", json.dumps(sorted(special_script_by_phone)))
    .replace("__MAX_FREE_CALLS_JSON__", json.dumps(app_config["free_calls"]["max_per_device"]))
    .replace("__COOLDOWN_MINUTES_JSON__", json.dumps(app_config["free_calls"]["cooldown_minutes"]))
    .replace("__RING_MIN_SECONDS_JSON__", json.dumps(app_config["ring"]["min_seconds"]))
    .replace("__RING_MAX_SECONDS_JSON__", json.dumps(app_config["ring"]["max_seconds"]))
    .replace("__RESET_CODE_JSON__", json.dumps(str(app_config["reset_code"])))
)

with open(OUT_PATH, "w") as f:
    f.write(html)

print("Wrote", OUT_PATH, "- phonebook entries:", len(phonebook), "- wrong scripts:", len(WRONG_SCRIPTS))
print("Target number:", target_rows[0]["phone"])
print("Special numbers:", [r["phone"] for r in special_rows])
print("Clue numbers:", [r["phone"] for r in clue_rows])
print("Decoy ad numbers auto-extracted from classifieds.html:", [d["phone"] for d in decoy_rows])
