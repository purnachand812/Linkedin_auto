#!/usr/bin/env python3
"""
detect.py - Quality & Humanizer Detection Panel for Purna's LinkedIn Assistant.
Scores draft across 5 checks: Burstiness, Specificity, Slop Density, Fingerprint, Voice & Tells.
"""

import sys
import os
import re
import json
import math
import argparse

def load_slop_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"forbidden_words": [], "forbidden_phrases": [], "forbidden_endings": []}

def calc_burstiness(text):
    # Sentence length variance
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if len(s.strip()) > 0]
    if len(sentences) <= 1:
        return 50.0 # Insufficient data
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    
    # Higher std dev relative to mean indicates better burstiness (varied rhythm)
    cv = std_dev / mean if mean > 0 else 0
    # Map cv (typical human writing cv is 0.4 - 1.0)
    score = min(100.0, cv * 120.0)
    return round(score, 1)

def calc_specificity(text):
    # Counts numbers, technical tokens, prices, URLs, specific metrics, file extensions, and licenses
    tokens = text.split()
    if not tokens:
        return 0.0
    
    specific_patterns = [
        r'\d+(\.\d+)?k?',             # Numbers (1.5k, 100, 21, 11)
        r'\$\d+|\€\d+',               # Currency ($0, €20)
        r'\b(v\d+\.\d+|python|docker|gpu|vram|ram|api|mit|apache|llm|ollama|vllm|swe-bench|lmsys|github|claude|gemini|openai|anthropic)\b', # Tech keywords
        r'\b[a-zA-Z0-9_-]+\.(py|json|md|txt|ts|js)\b', # File names / extensions
        r'https?://',                 # URLs
        r'%',                          # Percentages
        r'\b(tested|untested|benchmark|repo|commit|license|heuristic|heuristics|script|scripts|plugin|workflow)\b'
    ]
    
    matches = 0
    for pattern in specific_patterns:
        matches += len(re.findall(pattern, text, re.IGNORECASE))
    
    density = matches / len(tokens)
    # 15% density of specific technical tokens yields 100 score
    score = min(100.0, density * 650.0)
    return round(score, 1)

def calc_slop_density(text, slop_config):
    words = text.split()
    if not words:
        return 100.0, 0
    
    forbidden_words = slop_config.get("forbidden_words", [])
    forbidden_phrases = slop_config.get("forbidden_phrases", [])
    
    slop_count = 0
    for phrase in forbidden_phrases:
        slop_count += len(re.findall(re.escape(phrase), text, re.IGNORECASE)) * 2
        
    for word in forbidden_words:
        slop_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE))
        
    per_100 = (slop_count / len(words)) * 100.0
    score = max(0.0, 100.0 - (per_100 * 25.0))
    return round(score, 1), slop_count

def calc_fingerprint(text):
    penalties = 0
    # Check invisible characters
    invisibles = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']
    for char in invisibles:
        if char in text:
            penalties += 25
            
    # Check em-dashes
    if '—' in text:
        penalties += 30 * text.count('—')
        
    # Check curly quotes
    curly = ['“', '”', '‘', '’']
    for c in curly:
        if c in text:
            penalties += 10 * text.count(c)
            
    score = max(0.0, 100.0 - penalties)
    return round(score, 1)

def calc_voice_and_tells(text, slop_config):
    score = 100.0
    issues = []
    
    # Check engagement bait at the end
    forbidden_endings = slop_config.get("forbidden_endings", ["thoughts?", "agree?", "what do you think?"])
    lower_text = text.strip().lower()
    for ending in forbidden_endings:
        if lower_text.endswith(ending):
            score -= 35.0
            issues.append(f"Contains generic engagement bait ending: '{ending}'")
            
    # Check agent security warning if agent/code tool mentioned
    agent_keywords = ["agent", "terminal", "code execution", "browser automation", "execute commands", "repo", "scripts"]
    has_agent_ref = any(k in lower_text for k in agent_keywords)
    if has_agent_ref:
        security_terms = ["sandbox", "credentials", "security", "production", "inspect"]
        has_security_warn = any(s in lower_text for s in security_terms)
        if not has_security_warn:
            score -= 25.0
            issues.append("Discusses agent/execution capabilities but missing sandboxing security warning!")
            
    # Check explicit tested vs untested declaration if reviewing a tool
    tool_keywords = ["repo", "tool", "model", "release", "framework", "python"]
    has_tool_ref = any(k in lower_text for k in tool_keywords)
    if has_tool_ref:
        test_terms = ["tested", "haven't run", "based on", "documentation", "inspection"]
        has_test_decl = any(t in lower_text for t in test_terms)
        if not has_test_decl:
            score -= 20.0
            issues.append("Discusses a tool/model but lacks explicit tested vs untested declaration!")

    return max(0.0, round(score, 1)), issues

def evaluate_draft(text, slop_config):
    burstiness = calc_burstiness(text)
    specificity = calc_specificity(text)
    slop_score, slop_count = calc_slop_density(text, slop_config)
    fingerprint = calc_fingerprint(text)
    voice_score, voice_issues = calc_voice_and_tells(text, slop_config)
    
    # Final overall score: Weighted mean (60%) + Minimum check (40%)
    checks = [burstiness, specificity, slop_score, fingerprint, voice_score]
    mean_score = sum(checks) / len(checks)
    min_score = min(checks)
    
    final_score = (mean_score * 0.6) + (min_score * 0.4)
    final_score = round(final_score, 1)
    
    return {
        "final_score": final_score,
        "burstiness": burstiness,
        "specificity": specificity,
        "slop_score": slop_score,
        "slop_count": slop_count,
        "fingerprint": fingerprint,
        "voice_score": voice_score,
        "voice_issues": voice_issues
    }

def print_bar(label, score):
    bars = int(score / 4)
    bar_str = '#' * bars + '.' * (25 - bars)
    print(f"{label:<16} [{bar_str}] {score:>5.1f}")

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Score LinkedIn post draft against Purna's 5-check panel.")
    parser.add_argument("input_file", help="Path to input text file")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    slop_config = load_slop_config(os.path.join(script_dir, "slop.json"))

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read()

    res = evaluate_draft(text, slop_config)

    print("=== PURNA'S LINKEDIN QUALITY DETECTION PANEL ===")
    print_bar("BURSTINESS", res["burstiness"])
    print_bar("SPECIFICITY", res["specificity"])
    print_bar("SLOP DENSITY", res["slop_score"])
    print_bar("FINGERPRINT", res["fingerprint"])
    print_bar("VOICE & TELLS", res["voice_score"])
    print("-" * 52)
    
    verdict = "PASS (Ready to post)" if res["final_score"] >= 80.0 else "REVIEW NEEDED (Fix flags)"
    print(f"HUMAN QUALITY SCORE: {res['final_score']} / 100.0  --> {verdict}")

    if res["voice_issues"]:
        print("\nVoice & Guideline Flags:")
        for issue in res["voice_issues"]:
            print(f" ! {issue}")

if __name__ == "__main__":
    main()
