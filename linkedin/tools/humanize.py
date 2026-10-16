#!/usr/bin/env python3
"""
humanize.py - Clean LinkedIn post drafts for Purna's technical voice.
Strips invisible characters, em-dashes, curly quotes, and highlights AI slop.
"""

import sys
import os
import re
import json
import argparse

def load_slop_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"forbidden_words": [], "forbidden_phrases": [], "dry_replacements": {}}

def clean_text(text, slop_config):
    original = text
    changes = []

    # 1. Remove Invisible Characters
    invisible_chars = [
        ('\u200b', 'zero-width space'),
        ('\u200c', 'zero-width non-joiner'),
        ('\u200d', 'zero-width joiner'),
        ('\u2060', 'word joiner'),
        ('\ufeff', 'byte order mark'),
        ('\u00ad', 'soft hyphen')
    ]
    for char, desc in invisible_chars:
        if char in text:
            count = text.count(char)
            text = text.replace(char, '')
            changes.append(f"Removed {count} {desc}(s)")

    # Convert non-breaking space to regular space
    if '\u00a0' in text:
        count = text.count('\u00a0')
        text = text.replace('\u00a0', ' ')
        changes.append(f"Converted {count} non-breaking space(s)")

    # 2. Typography Fixes (Em-dashes to commas/hyphens, curly quotes to straight)
    if '—' in text:
        count = text.count('—')
        # Replace ' — ' with ', ' or '--'
        text = re.sub(r'\s*—\s*', ', ', text)
        changes.append(f"Replaced {count} em dash(es) with commas/full stops")

    if '–' in text: # en-dash
        text = text.replace('–', '-')
        changes.append("Converted en dash to hyphen")

    # Curly quotes
    quotes_map = [
        ('“', '"'), ('”', '"'),
        ('‘', "'"), ('’', "'"),
        ('…', '...')
    ]
    for src, dst in quotes_map:
        if src in text:
            count = text.count(src)
            text = text.replace(src, dst)
            changes.append(f"Standardized {count} instance(s) of '{src}'")

    # 3. Highlight/Replace Slop Words
    slop_found = []
    forbidden_words = slop_config.get("forbidden_words", [])
    forbidden_phrases = slop_config.get("forbidden_phrases", [])
    replacements = slop_config.get("dry_replacements", {})

    for phrase in forbidden_phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            slop_found.append(f"Forbidden phrase found: '{phrase}' ({len(matches)}x)")

    for word in forbidden_words:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            suggested = replacements.get(word.lower(), "remove/rewrite")
            slop_found.append(f"Slop word found: '{word}' ({len(matches)}x) -> Suggested replacement: '{suggested}'")
            # Automatically perform replacement if dry replacement exists
            if word.lower() in replacements:
                def replace_match(m):
                    orig = m.group(0)
                    rep = replacements[word.lower()]
                    return rep.capitalize() if orig[0].isupper() else rep
                text = pattern.sub(replace_match, text)
                changes.append(f"Replaced '{word}' with '{replacements[word.lower()]}'")

    return text, changes, slop_found

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Clean and humanize LinkedIn draft text.")
    parser.add_argument("input_file", help="Path to input text file")
    parser.add_argument("--out", help="Path to output cleaned text file", default=None)
    parser.add_argument("--report", action="store_true", help="Print detailed change report")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    slop_config = load_slop_config(os.path.join(script_dir, "slop.json"))

    with open(args.input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text, changes, slop_found = clean_text(raw_text, slop_config)

    print("=== HUMANIZE CLEANING SUMMARY ===")
    if changes:
        print("\nCleanings performed:")
        for c in changes:
            print(f" - {c}")
    else:
        print("\nNo typography or invisible character issues found.")

    if slop_found:
        print("\nSlop Warnings / Remaining Concerns:")
        for s in slop_found:
            print(f" ! {s}")
    else:
        print("No AI slop vocabulary detected!")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        print(f"\nSaved cleaned text to: {args.out}")
    elif not args.report:
        print("\n=== CLEANED TEXT OUTPUT ===")
        print(cleaned_text)

if __name__ == "__main__":
    main()
