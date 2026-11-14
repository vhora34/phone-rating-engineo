#!/usr/bin/env python3
"""Offline India smartphone recommendation engine (Python 3.9+, no dependencies).

Run: python phone_compare.py
Input examples:
  Samsung Galaxy S25 12GB 256GB Rs 60000
  OnePlus 13s 16/512 Rs 62000, Galaxy S25 12/256 Rs 60000
  list
  help
  q

Scores and descriptive notes are *editorial estimates*, not lab results.
Prices are illustrative defaults; enter the actual purchase price for useful value ratings.
Only variants in the database or explicitly supplied by the user are evaluated.
"""
from __future__ import annotations
import difflib
import math
import re
from dataclasses import dataclass

CATEGORIES = ("build", "camera", "design", "battery", "longevity", "basic", "value")
LABELS = {"build": "Build quality", "camera": "Camera", "design": "Design & comfort",
          "battery": "Battery & charging", "longevity": "Long-term ownership",
          "basic": "Everyday performance", "value": "Value for money"}

# Weights are intentionally explicit and sum to 1.0. Change to reflect your audience.
PROFILES = {
    "Compact flagship buyer": {"design": .30, "build": .20, "camera": .15, "longevity": .15, "basic": .10, "battery": .05, "value": .05},
    "Photography & family events": {"camera": .40, "build": .10, "design": .10, "battery": .10, "longevity": .10, "basic": .10, "value": .10},
    "Long-term keeper (5+ years)": {"longevity": .35, "build": .20, "basic": .20, "battery": .10, "camera": .05, "value": .10},
    "All-day battery user": {"battery": .45, "basic": .20, "longevity": .15, "value": .10, "build": .05, "camera": .05},
    "Premium design lover": {"design": .35, "build": .30, "camera": .10, "longevity": .10, "basic": .10, "value": .05},
    "Budget-conscious buyer": {"value": .45, "basic": .20, "battery": .15, "longevity": .10, "camera": .05, "build": .05},
    "Everyday social-media user": {"basic": .35, "battery": .20, "camera": .15, "longevity": .15, "value": .10, "build": .05},
}
assert all(abs(sum(w.values()) - 1) < 1e-9 for w in PROFILES.values())

@dataclass(frozen=True)
class Phone:
    name: str
    ram: int
    storage: int
    reference_price: int
    scores: dict
    facts: tuple
    strengths: tuple
    weaknesses: tuple
    aliases: tuple = ()
    note: str = ""

# Reference prices are editable illustrative INR prices, NOT live market quotes.
# Scores are deliberately editorial, and should be reviewed as market data evolves.
PHONES = [
    Phone("Samsung Galaxy S25", 12, 256, 60000,
          dict(build=9.3, camera=9.1, design=9.4, battery=7.3, longevity=9.5, basic=9.6),
          ("6.2-inch compact AMOLED", "Snapdragon 8 Elite", "4,000mAh battery; 25W wired charging",
           "50MP main + ultrawide + 3x telephoto", "IP68 water/dust resistance",
           "Seven generations of OS upgrades promised from launch"),
          ("Lightweight compact design", "Versatile camera system for photos and video",
           "Flagship performance and long update commitment", "IP68 protection"),
          ("Smaller battery than many rivals", "25W charging is comparatively slow",
           "Premium repair costs", "No microSD expansion"),
          ("s25", "galaxy s25", "samsung s25")),
    Phone("OnePlus 13s", 12, 256, 55000,
          dict(build=8.8, camera=8.5, design=9.1, battery=9.4, longevity=8.5, basic=9.6),
          ("6.32-inch compact AMOLED", "Snapdragon 8 Elite", "5,850mAh battery; 80W wired charging",
           "50MP main + 2x telephoto; no ultrawide", "IP65 water/dust resistance"),
          ("Excellent battery capacity for a compact phone", "Fast charging and flagship speed",
           "Comfortable narrow body", "Strong multitasking capability"),
          ("No ultrawide camera", "IP65 is less protective against immersion than IP68",
           "Heavier than Galaxy S25", "Software support horizon is shorter than S25"),
          ("op 13s", "oneplus13s")),
    Phone("Samsung Galaxy A56", 8, 128, 32000,
          dict(build=8.5, camera=8.2, design=8.0, battery=8.2, longevity=8.8, basic=8.2),
          ("Exynos 1580", "50MP main camera with OIS", "5,000mAh battery",
           "Six generations of OS upgrades promised from launch"),
          ("Balanced family-event photography", "Long software support",
           "Good everyday display and battery"),
          ("Less powerful than flagship phones", "128GB base variant may fill over time",
           "Larger body than compact flagships"),
          ("a56", "galaxy a56")),
    Phone("Samsung Galaxy A36", 8, 256, 27000,
          dict(build=8.0, camera=7.7, design=7.8, battery=8.1, longevity=8.0, basic=7.5),
          ("Snapdragon 6 Gen 3", "50MP main camera with OIS", "5,000mAh battery",
           "Six generations of OS upgrades promised from launch"),
          ("256GB option offers useful storage headroom", "Long update commitment",
           "Reliable everyday feature set"),
          ("Processor has limited long-term performance headroom", "Not compact",
           "Cameras less versatile than flagship models"),
          ("a36", "galaxy a36")),
    Phone("Samsung Galaxy S25 FE", 8, 128, 40000,
          dict(build=8.8, camera=8.8, design=8.2, battery=8.1, longevity=9.0, basic=9.0),
          ("Exynos 2400", "50MP main + ultrawide + 3x telephoto", "4,900mAh battery",
           "IP68 water/dust resistance"),
          ("Versatile camera system", "Strong everyday performance", "Long software support"),
          ("Large body", "Used units require battery and repair-history inspection",
           "Condition matters more than scores when buying second-hand"),
          ("s25 fe", "galaxy s25 fe"), "Used-phone prices are NOT directly comparable to new-phone prices without condition checks."),
    Phone("vivo T5x", 8, 128, 28500,
          dict(build=7.7, camera=7.1, design=7.5, battery=9.4, longevity=7.3, basic=8.2),
          ("Dimensity 7400-series chipset", "Large battery", "LCD display"),
          ("Strong battery-focused everyday option", "Capable social-media performance"),
          ("Camera versatility is limited", "Shorter software-support outlook than Samsung A-series",
           "128GB storage may be restrictive over many years"),
          ("t5x", "vivo t5x 5g")),
    Phone("realme P4s", 8, 128, 30000,
          dict(build=7.7, camera=7.3, design=7.8, battery=9.4, longevity=7.5, basic=8.3),
          ("Dimensity 7400-series chipset", "Battery-oriented design", "AMOLED display"),
          ("Excellent battery emphasis", "Smooth everyday performance"),
          ("Less versatile cameras than flagships", "Check current price against alternatives"),
          ("p4s", "realme p4s 5g")),
]


def money(amount):
    s = str(round(amount))
    return "₹" + (s[:-3] and re.sub(r"\B(?=(\d{2})+(?!\d))", ",", s[:-3]) + "," or "") + s[-3:]


def clamp(v):
    return max(1.0, min(10.0, v))


def normalize(s):
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def parse_input(raw):
    text = raw.strip()
    price = None
    # Price requires an explicit currency marker to avoid confusing it with RAM/storage.
    pm = re.search(r"(?:₹|\b(?:rs\.?|inr)\s*)\s*([\d,]+)", text, re.I)
    if pm:
        price = int(pm.group(1).replace(",", ""))
        text = text[:pm.start()] + " " + text[pm.end():]
    ram = storage = None
    pair = re.search(r"(?<!\d)(\d{1,2})\s*(?:gb)?\s*/\s*(\d{2,4})\s*(?:gb)?(?!\d)", text, re.I)
    if pair:
        ram, storage = int(pair.group(1)), int(pair.group(2))
        text = text[:pair.start()] + " " + text[pair.end():]
    else:
        ram_match = re.search(r"\b(\d{1,2})\s*gb\s*ram\b|\bram\s*(\d{1,2})\s*gb\b", text, re.I)
        sto_match = re.search(r"\bstorage\s*(\d{2,4})\s*(gb|tb)\b", text, re.I)
        if ram_match:
            ram = int(ram_match.group(1) or ram_match.group(2))
            text = text.replace(ram_match.group(0), " ")
        if sto_match:
            storage = int(sto_match.group(1)) * (1024 if sto_match.group(2).lower() == "tb" else 1)
            text = text.replace(sto_match.group(0), " ")
        # Handle common '12GB 256GB' format.
        matches = list(re.finditer(r"\b(\d+)\s*(gb|tb)\b", text, re.I))
        values = [int(m.group(1)) * (1024 if m.group(2).lower() == "tb" else 1) for m in matches]
        if len(values) >= 2:
            if ram is None:
                ram = min(values[0], values[1])
            if storage is None:
                storage = max(values[0], values[1])
            text = re.sub(r"\b\d+\s*(?:gb|tb)\b", " ", text, flags=re.I)
        elif len(values) == 1:
            if values[0] <= 24 and ram is None:
                ram = values[0]
            elif values[0] > 24 and storage is None:
                storage = values[0]
            text = re.sub(r"\b\d+\s*(?:gb|tb)\b", " ", text, flags=re.I)
    return " ".join(text.split()), ram, storage, price


def find_phone(query):
    q = normalize(query)
    aliases = {}
    for p in PHONES:
        for alias in (p.name, *p.aliases):
            aliases[normalize(alias)] = p
    if q in aliases:
        return aliases[q], []
    # Never auto-substitute another model, e.g. S25 FE for S25.
    suggestions = difflib.get_close_matches(q, list(aliases), n=4, cutoff=.52)
    unique = []
    for a in suggestions:
        if aliases[a].name not in unique:
            unique.append(aliases[a].name)
    return None, unique[:3]


def scores_for(p, ram, storage, price):
    ram = p.ram if ram is None else ram
    storage = p.storage if storage is None else storage
    if ram < 2 or ram > 32 or storage < 32 or storage > 2048:
        raise ValueError("RAM/storage appears invalid; please check the entered variant.")
    price = p.reference_price if price is None else price
    if price <= 0:
        raise ValueError("Price must be greater than zero.")
    scores = dict(p.scores)
    # RAM/storage modestly affect practical longevity; they do not improve the camera or build.
    ram_delta = ram - p.ram
    storage_delta = math.log2(storage / p.storage)
    scores["longevity"] = clamp(scores["longevity"] + .10 * ram_delta + .22 * storage_delta)
    scores["basic"] = clamp(scores["basic"] + .06 * ram_delta + .12 * storage_delta)
    # Price-sensitive, India-oriented relative value score: compare actual price with reference
    # and baseline capability. +/- Rs 10k changes value by 1 point (bounded).
    hardware = sum(scores.values()) / len(scores)
    scores["value"] = clamp(hardware - (price - 30000) / 10000 * .70)
    overall = sum(scores[c] for c in CATEGORIES) / len(CATEGORIES)
    fits = sorted(((name, sum(scores.get(cat, 0) * weight for cat, weight in weights.items()))
                   for name, weights in PROFILES.items()), key=lambda x: x[1], reverse=True)
    return scores, overall, fits, ram, storage, price


def bar(score):
    filled = max(0, min(10, round(score)))
    return "█" * filled + "░" * (10 - filled)


def rating_word(score):
    if score >= 9: return "Outstanding"
    if score >= 8.3: return "Excellent"
    if score >= 7.5: return "Very good"
    if score >= 6.5: return "Good"
    return "Mixed"


def report(query):
    name, ram, storage, price = parse_input(query)
    p, suggestions = find_phone(name)
    if p is None:
        print(f"\nPhone not found: {name!r}. No substitute was scored.")
        if suggestions:
            print("Did you mean: " + ", ".join(suggestions) + "?")
        print("Type 'list' to see supported models; add new models in PHONES.\n")
        return None
    try:
        s, overall, fits, ram, storage, price = scores_for(p, ram, storage, price)
    except ValueError as exc:
        print("Input error:", exc)
        return None
    print("\n" + "=" * 70)
    print(f"{p.name} | {ram}GB RAM / {storage}GB storage | {money(price)}")
    print("=" * 70)
    print(f"OVERALL: {overall:.1f}/10 — {rating_word(overall)}")
    print("\nCATEGORY RATINGS (editorial, not benchmark measurements)")
    for cat in CATEGORIES:
        print(f"  {LABELS[cat]:<23} {bar(s[cat])} {s[cat]:4.1f}/10")
    print("\nKEY SPECIFICATIONS")
    for fact in p.facts: print("  • " + fact)
    print("\nBEST SUITED FOR")
    for idx, (label, score) in enumerate(fits[:3], 1):
        print(f"  {idx}. {label} — {score:.1f}/10 match")
    print("\nLESS SUITED FOR")
    for label, score in fits[-2:]:
        print(f"  • {label} — {score:.1f}/10 match")
    print("\nSTRENGTHS")
    for point in p.strengths: print("  + " + point)
    print("\nWEAKNESSES / TRADE-OFFS")
    for point in p.weaknesses: print("  - " + point)
    print("\nBUYER VERDICT")
    print(f"  {p.name} is particularly suitable for {fits[0][0].lower()}s.")
    print(f"  Its strongest rated category is {LABELS[max(s, key=s.get)].lower()} "
          f"({max(s.values()):.1f}/10); its weakest is "
          f"{LABELS[min(s, key=s.get)].lower()} ({min(s.values()):.1f}/10).")
    if price != p.reference_price:
        print(f"  Your entered price: {money(price)}; database reference: {money(p.reference_price)}.")
    else:
        print("  Value uses an editable reference price, NOT a live store quote.")
    if p.note: print("  NOTE: " + p.note)
    print("  Reminder: scores are subjective; actual battery life, cameras, and reliability vary.\n")
    return p, s, overall, fits, price


def compare(queries):
    rows = [r for q in queries if (r := report(q)) is not None]
    if len(rows) < 2:
        return
    print("\n" + "=" * 70)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 70)
    print(f"{'Category':<24}" + "".join(f"{str(i+1):>11}" for i in range(len(rows))))
    for cat in CATEGORIES:
        print(f"{LABELS[cat]:<24}" + "".join(f"{r[1][cat]:>11.1f}" for r in rows))
    print(f"{'OVERALL':<24}" + "".join(f"{r[2]:>11.1f}" for r in rows))
    print("\nPHONES")
    for i, r in enumerate(rows, 1):
        print(f"  {i}. {r[0].name} — {money(r[4])} — best for {r[3][0][0]}")
    winner = max(rows, key=lambda r: r[2])
    print(f"\nHighest overall editorial rating: {winner[0].name} ({winner[2]:.1f}/10)")
    print("Compare scores against your own priorities; the highest overall is not always your best fit.\n")


# PROGRAMIZ: Enter the phone in the Input (stdin) panel, then click Run.
# Example input: Samsung Galaxy S25 12GB 256GB Rs 60000
# Compare: OnePlus 13s 16/512 Rs 62000, Galaxy S25 12/256 Rs 60000


def main():
    print("PHONE RECOMMENDATION ENGINE — INDIA")
    print("Enter phone model, RAM, storage, and optional price.")
    print("For comparison, separate phones with commas.\n")
    try:
        query = input("Phone(s): ").strip()
    except EOFError:
        query = ""
    if not query:
        print("No input received. In Programiz, open the Input (stdin) section,")
        print("type e.g. Samsung Galaxy S25 12GB 256GB Rs 60000, and click Run.")
        return
    parts = [x.strip() for x in re.split(r",\s*(?=[A-Za-z])", query) if x.strip()]
    if len(parts) > 1:
        compare(parts)
    else:
        report(parts[0])


if __name__ == "__main__":
    main()
