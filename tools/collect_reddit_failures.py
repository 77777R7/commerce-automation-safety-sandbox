#!/usr/bin/env python3
"""Collect a small batch of public Reddit commerce automation failure signals.

This is a narrow v0.1 collector for Failure Intelligence. It intentionally avoids
user profile scraping, private communities, login flows, and large-scale crawling.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

from scrapling.fetchers import Fetcher


DEFAULT_SUBREDDITS = ["n8n"]
DEFAULT_KEYWORDS = [
    "shopify",
    "inventory",
    "fulfillment",
    "webhook",
    "idempotency",
    "tracking",
    "refund",
    "amazon",
]

FAILURE_TERMS = [
    "oversell",
    "oversold",
    "duplicate",
    "webhook",
    "idempotency",
    "retry",
    "timeout",
    "inventory",
    "fulfillment",
    "tracking",
    "refund",
    "reship",
    "cancel",
    "label",
    "warehouse",
    "mapping",
    "timezone",
    "null",
    "failed",
    "broke",
    "silent",
    "manual review",
]

LOW_VALUE_TERMS = [
    "automoderator",
    "great read",
    "thanks",
    "thank you",
]


@dataclass
class EvidenceItem:
    evidence_id: str
    captured_at: str
    source_type: str
    platform: str
    community: str
    source_url: str
    thread_title: str
    evidence_type: str
    author_hash: str
    raw_excerpt: str
    matched_terms: str
    relevance_score: int
    privacy_note: str


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def short_excerpt(value: str, limit: int = 650) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def mask_author(author: str) -> str:
    if not author:
        return "unknown"
    digest = hashlib.sha256(author.encode("utf-8")).hexdigest()[:10]
    return f"user_{digest}"


def score_text(text: str) -> tuple[int, list[str]]:
    lower = text.lower()
    matched = [term for term in FAILURE_TERMS if term in lower]
    score = len(matched)
    if "oversold" in lower or "oversell" in lower:
        score += 3
    if "idempotency" in lower or "webhook" in lower:
        score += 2
    if "manual review" in lower:
        score += 1
    if any(term in lower for term in LOW_VALUE_TERMS):
        score -= 3
    return score, matched


def absolutize(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return "https://old.reddit.com" + url
    return url


def search_urls(subreddits: Iterable[str], keywords: Iterable[str], per_keyword: int) -> list[str]:
    urls: list[str] = []
    for subreddit in subreddits:
        for keyword in keywords:
            q = quote_plus(keyword)
            urls.append(
                f"https://old.reddit.com/r/{subreddit}/search?q={q}&restrict_sr=on&sort=new&t=year"
            )
            if len(urls) >= per_keyword * len(list(subreddits)) * len(list(keywords)):
                break
    return urls


def extract_search_results(page, max_threads: int) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for item in page.css(".search-result"):
        title = normalize_text(item.css("a.search-title::text").get() or "")
        href = absolutize(item.css("a.search-title::attr(href)").get() or "")
        if title and href and "/comments/" in href:
            results.append((title, href))
        if len(results) >= max_threads:
            break
    return results


def extract_post_text(page) -> str:
    title = normalize_text(page.css("a.title::text").get() or page.css("title::text").get() or "")
    body = normalize_text(" ".join(t for t in page.css(".usertext-body .md ::text").getall() if t))
    return normalize_text(f"{title} {body}")


def extract_comments(page) -> list[tuple[str, str, str]]:
    comments: list[tuple[str, str, str]] = []
    for comment in page.css(".comment"):
        author = normalize_text(comment.css("a.author::text").get() or "")
        if author.lower() == "automoderator":
            continue
        comment_id = comment.attrib.get("data-fullname") or comment.attrib.get("id") or ""
        text = normalize_text(" ".join(t for t in comment.css(".md ::text").getall() if t))
        if text:
            comments.append((comment_id, author, text))
    return comments


def collect(args: argparse.Namespace) -> list[EvidenceItem]:
    captured_at = datetime.now(timezone.utc).isoformat()
    subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    output_items: list[EvidenceItem] = []
    seen_threads: set[str] = set()
    seen_texts: set[str] = set()

    headers = {
        "User-Agent": "CommerceSafetyFailureIntelligence/0.1 research collector",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for search_url in search_urls(subreddits, keywords, args.per_keyword):
        if len(output_items) >= args.limit:
            break
        search_page = Fetcher.get(search_url, headers=headers, timeout=args.timeout, impersonate="chrome")
        if getattr(search_page, "status", None) != 200:
            time.sleep(args.delay)
            continue

        for title, thread_url in extract_search_results(search_page, args.max_threads_per_search):
            if len(output_items) >= args.limit:
                break
            if thread_url in seen_threads:
                continue
            seen_threads.add(thread_url)
            time.sleep(args.delay)

            thread_page = Fetcher.get(thread_url, headers=headers, timeout=args.timeout, impersonate="chrome")
            if getattr(thread_page, "status", None) != 200:
                time.sleep(args.delay)
                continue

            post_text = extract_post_text(thread_page)
            post_score, post_terms = score_text(post_text)
            if post_score >= args.min_score:
                key = hashlib.sha256(post_text.lower().encode("utf-8")).hexdigest()
                if key not in seen_texts:
                    seen_texts.add(key)
                    output_items.append(
                        EvidenceItem(
                            evidence_id=f"SCR-{len(output_items)+1:03d}",
                            captured_at=captured_at,
                            source_type="public_forum_search",
                            platform="Reddit",
                            community=f"r/{thread_url.split('/r/')[1].split('/')[0]}" if "/r/" in thread_url else "Reddit",
                            source_url=thread_url,
                            thread_title=title,
                            evidence_type="post",
                            author_hash="not_collected",
                            raw_excerpt=short_excerpt(post_text),
                            matched_terms=", ".join(post_terms),
                            relevance_score=post_score,
                            privacy_note="No user profile scraping; post excerpt only.",
                        )
                    )

            for comment_id, author, text in extract_comments(thread_page):
                if len(output_items) >= args.limit:
                    break
                score, terms = score_text(text)
                if score < args.min_score:
                    continue
                key = hashlib.sha256(text.lower().encode("utf-8")).hexdigest()
                if key in seen_texts:
                    continue
                seen_texts.add(key)
                anchor = f"{thread_url}{comment_id}" if comment_id.startswith("#") else thread_url
                output_items.append(
                    EvidenceItem(
                        evidence_id=f"SCR-{len(output_items)+1:03d}",
                        captured_at=captured_at,
                        source_type="public_forum_search",
                        platform="Reddit",
                        community=f"r/{thread_url.split('/r/')[1].split('/')[0]}" if "/r/" in thread_url else "Reddit",
                        source_url=anchor,
                        thread_title=title,
                        evidence_type="comment",
                        author_hash=mask_author(author),
                        raw_excerpt=short_excerpt(text),
                        matched_terms=", ".join(terms),
                        relevance_score=score,
                        privacy_note="Author masked; no user profile scraping; excerpt only.",
                    )
                )
            time.sleep(args.delay)

    return output_items


def write_outputs(items: list[EvidenceItem], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "scrapling_reddit_test_raw_evidence.jsonl"
    csv_path = output_dir / "scrapling_reddit_test_raw_evidence.csv"
    summary_path = output_dir / "scrapling_reddit_test_summary.md"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(items[0]).keys()) if items else EvidenceItem.__dataclass_fields__.keys())
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Scrapling Reddit Test Summary\n\n")
        f.write(f"Items collected: {len(items)}\n\n")
        for item in items:
            f.write(f"## {item.evidence_id}: {item.thread_title}\n")
            f.write(f"- Source: {item.source_url}\n")
            f.write(f"- Type: {item.evidence_type}\n")
            f.write(f"- Score: {item.relevance_score}\n")
            f.write(f"- Matched terms: {item.matched_terms}\n")
            f.write(f"- Excerpt: {item.raw_excerpt}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect public Reddit failure-intelligence evidence with Scrapling.")
    parser.add_argument("--subreddits", default=",".join(DEFAULT_SUBREDDITS))
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per-keyword", type=int, default=1)
    parser.add_argument("--max-threads-per-search", type=int, default=3)
    parser.add_argument("--min-score", type=int, default=2)
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output-dir", default="outputs/failure_intelligence/scrapling_reddit_test")
    args = parser.parse_args()

    items = collect(args)
    write_outputs(items, Path(args.output_dir))
    print(json.dumps({"items": len(items), "output_dir": args.output_dir}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
