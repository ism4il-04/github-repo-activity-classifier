"""
data_collection.py
==================
GitHub Repository Activity Dataset — Phase 1 Collection Script
ENSA Tétouan | ML Project 2025-2026

Target variable: is_inactive
    1 = abandoned (no push in last 180 days)
    0 = active    (pushed within last 180 days)

Usage:
    python data_collection.py --token YOUR_TOKEN --rows 12000 --out ../data/dataset.csv

Requirements:
    pip install requests pandas tqdm
"""

import argparse
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://api.github.com"
INACTIVITY_THRESHOLD_DAYS = 180   # repos with no push in 180 days → inactive
RATE_LIMIT_BUFFER = 50            # stop requesting if fewer than this many calls remain
INACTIVE_RATIO = 0.15             # target 15% inactive class (within 5–25% requirement)
RAW_CACHE_FILE = Path("../data/raw_cache.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def make_session(token: str) -> requests.Session:
    """Create an authenticated session with default headers."""
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return s


def check_rate_limit(session: requests.Session) -> dict | None:
    """Return current rate limit info from GitHub. Returns None on auth failure."""
    try:
        r = session.get(f"{BASE_URL}/rate_limit", timeout=15)
        if r.status_code == 401:
            log.error(
                "401 Unauthorized when checking rate limit — your GitHub token has expired "
                "or been revoked. Generate a new token and re-run with --token NEW_TOKEN. "
                "Your progress is saved in the cache and will resume automatically."
            )
            raise SystemExit(1)
        r.raise_for_status()
        return r.json()["resources"]["core"]
    except requests.exceptions.RequestException as e:
        log.warning(f"Could not check rate limit: {e}. Proceeding anyway.")
        return None


def wait_for_rate_limit(session: requests.Session):
    """Block until rate limit resets if too low."""
    info = check_rate_limit(session)
    if info is None:
        return  # skip wait if rate limit check failed (network blip)
    remaining = info["remaining"]
    reset_ts = info["reset"]
    if remaining < RATE_LIMIT_BUFFER:
        wait_sec = max(reset_ts - time.time() + 5, 0)
        log.warning(
            f"Rate limit low ({remaining} remaining). Sleeping {wait_sec:.0f}s until reset..."
        )
        time.sleep(wait_sec)


def github_get(session: requests.Session, url: str, params: dict = None) -> dict | None:
    """GET request with rate-limit handling and retry on 5xx."""
    wait_for_rate_limit(session)
    for attempt in range(3):
        try:
            r = session.get(url, params=params, timeout=15)
            log.debug(f"GET {url} → {r.status_code}")
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 403:
                log.warning("403 – secondary rate limit hit. Sleeping 60s.")
                time.sleep(60)
            elif r.status_code == 422:
                log.warning(f"422 – invalid query for {url}. Skipping.")
                return None
            elif r.status_code >= 500:
                log.warning(f"Server error {r.status_code}. Retrying in 10s.")
                time.sleep(10)
            else:
                log.warning(f"Unexpected status {r.status_code} for {url}")
                return None
        except requests.exceptions.RequestException as e:
            log.error(f"Network error: {e}. Retrying in 10s.")
            time.sleep(10)
    log.error(f"Failed after 3 attempts: {url}")
    return None


# ---------------------------------------------------------------------------
# Data collection strategy
# ---------------------------------------------------------------------------
# We search repos by star range to get a diverse, non-biased sample.
# Stars are NOT used as a proxy for activity — they are just a search lever.
# This gives us repos across all activity levels, ensuring natural imbalance.

STAR_RANGES = [
    "0..5",
    "6..15",
    "16..50",
    "51..200",
    "201..1000",
    "1001..5000",
    "5001..50000",
]

# Languages to diversify the dataset
LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "Go",
    "Ruby", "Rust", "TypeScript", "PHP", "C",
]


def search_repos(session: requests.Session, stars: str, language: str, page: int,
                 inactive_only: bool = False) -> list[dict]:
    """
    Search GitHub repositories matching stars range and language.
    inactive_only=True  → adds pushed:<cutoff filter (guaranteed inactive repos)
    inactive_only=False → adds pushed:>cutoff filter (guaranteed active repos)
    Returns list of raw repo objects (up to 100 per page).
    """
    cutoff_date = (
        datetime.now(timezone.utc) - timedelta(days=INACTIVITY_THRESHOLD_DAYS)
    ).strftime("%Y-%m-%d")

    if inactive_only:
        q = f"stars:{stars} language:{language} pushed:<{cutoff_date}"
    else:
        q = f"stars:{stars} language:{language} pushed:>{cutoff_date}"

    params = {
        "q": q,
        "sort": "stars",   # sort by stars avoids recency bias
        "order": "desc",
        "per_page": 100,
        "page": page,
    }
    data = github_get(session, f"{BASE_URL}/search/repositories", params)
    if data is None:
        return []
    return data.get("items", [])


def get_contributor_count(session: requests.Session, full_name: str) -> int:
    """
    Fetch contributor count for a repo (capped at 100).
    Returns -1 on error.
    """
    url = f"{BASE_URL}/repos/{full_name}/contributors"
    data = github_get(session, url, params={"per_page": 100, "anon": "true"})
    if data is None or not isinstance(data, list):
        return -1
    return len(data)


def get_avg_issue_response_hours(session: requests.Session, full_name: str) -> float:
    """
    Approximate average issue response time (hours) using the last 20 closed issues.
    Returns -1.0 if unavailable.
    """
    url = f"{BASE_URL}/repos/{full_name}/issues"
    data = github_get(session, url, params={
        "state": "closed", "per_page": 20, "sort": "updated", "direction": "desc"
    })
    if not data or not isinstance(data, list):
        return -1.0
    deltas = []
    for issue in data:
        if "pull_request" in issue:
            continue  # skip PRs
        created = issue.get("created_at")
        closed = issue.get("closed_at")
        if created and closed:
            t0 = datetime.fromisoformat(created.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(closed.replace("Z", "+00:00"))
            deltas.append((t1 - t0).total_seconds() / 3600)
    return round(sum(deltas) / len(deltas), 2) if deltas else -1.0


def parse_repo(repo: dict, session: requests.Session) -> dict | None:
    """
    Extract and engineer features from a raw repo object.
    Returns a flat feature dict, or None if data is insufficient.
    """
    full_name = repo.get("full_name", "")
    pushed_at_str = repo.get("pushed_at")
    created_at_str = repo.get("created_at")

    if not pushed_at_str or not created_at_str:
        return None

    pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    # ---- Target variable ------------------------------------------------
    days_since_push = (now - pushed_at).days
    is_inactive = int(days_since_push > INACTIVITY_THRESHOLD_DAYS)

    # ---- Basic numeric features ----------------------------------------
    repo_age_days = (now - created_at).days
    if repo_age_days < 30:
        return None  # too new to classify meaningfully

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    open_issues = repo.get("open_issues_count", 0)
    watchers = repo.get("watchers_count", 0)
    size_kb = repo.get("size", 0)

    # ---- Derived / engineered features ---------------------------------
    has_description = int(bool(repo.get("description")))
    has_homepage = int(bool(repo.get("homepage")))
    has_wiki = int(repo.get("has_wiki", False))
    has_projects = int(repo.get("has_projects", False))
    is_fork = int(repo.get("fork", False))
    archived = int(repo.get("archived", False))

    license_name = (
        repo["license"]["name"] if repo.get("license") else "None"
    )

    # Commit frequency proxy: forks+stars per repo-age (rough engagement rate)
    engagement_rate = round((stars + forks) / max(repo_age_days, 1), 4)

    # Stars-to-forks ratio (popularity vs derivative use)
    stars_forks_ratio = round(stars / max(forks, 1), 2)

    # ---- Requires extra API calls (only for a sample to save quota) ----
    contributor_count = get_contributor_count(session, full_name)
    avg_issue_response_h = get_avg_issue_response_hours(session, full_name)

    return {
        # Identifiers (not used as features)
        "full_name": full_name,
        "collected_at": now.isoformat(),

        # Numeric features
        "stars": stars,
        "forks": forks,
        "open_issues": open_issues,
        "watchers": watchers,
        "size_kb": size_kb,
        "repo_age_days": repo_age_days,
        "days_since_last_push": days_since_push,
        "contributor_count": contributor_count,
        "avg_issue_response_hours": avg_issue_response_h,
        "engagement_rate": engagement_rate,
        "stars_forks_ratio": stars_forks_ratio,

        # Categorical features
        "language": repo.get("language") or "Unknown",
        "license": license_name,

        # Binary features
        "has_description": has_description,
        "has_homepage": has_homepage,
        "has_wiki": has_wiki,
        "has_projects": has_projects,
        "is_fork": is_fork,
        "archived": archived,

        # Target variable
        "is_inactive": is_inactive,
    }


# ---------------------------------------------------------------------------
# Main collection loop
# ---------------------------------------------------------------------------

def _collect_pass(session: requests.Session, target: int, inactive_only: bool,
                  seen: set, rows: list, pbar) -> list:
    """
    One collection pass: gather `target` repos of the requested class.
    Modifies `seen` and `rows` in-place, updates `pbar`.
    """
    label = "inactive" if inactive_only else "active"
    collected = 0

    for lang in LANGUAGES:
        for star_range in STAR_RANGES:
            for page in range(1, 11):
                if collected >= target:
                    break

                raw_items = search_repos(session, star_range, lang, page, inactive_only)
                if not raw_items:
                    break

                for repo in raw_items:
                    if collected >= target:
                        break
                    fn = repo.get("full_name", "")
                    if fn in seen:
                        continue
                    seen.add(fn)

                    parsed = parse_repo(repo, session)
                    if parsed is None:
                        continue

                    # Confirm the class matches (sanity check)
                    if parsed["is_inactive"] != int(inactive_only):
                        continue

                    rows.append(parsed)
                    collected += 1
                    pbar.update(1)

                    # Checkpoint every 500 rows total
                    if len(rows) % 500 == 0:
                        log.info(f"Checkpoint: {len(rows)} rows total ({label} pass).")
                        RAW_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                        with open(RAW_CACHE_FILE, "w") as f:
                            json.dump(rows, f)

                time.sleep(1)

            if collected >= target:
                break
        if collected >= target:
            break

    log.info(f"Pass '{label}' complete: collected {collected}/{target} rows.")
    return rows


def collect(token: str, target_rows: int, out_path: Path):
    session = make_session(token)

    # Verify authentication
    me = github_get(session, f"{BASE_URL}/user")
    if me is None:
        raise SystemExit("Authentication failed. Check your GitHub token.")
    log.info(f"Authenticated as: {me['login']}")

    # Targets: 15% inactive, 85% active
    inactive_target = round(target_rows * INACTIVE_RATIO)
    active_target = target_rows - inactive_target
    log.info(f"Targets — active: {active_target}, inactive: {inactive_target}")

    rows: list = []
    seen: set = set()

    # Load partial cache if exists and split by class
    if RAW_CACHE_FILE.exists():
        log.info(f"Loading partial cache from {RAW_CACHE_FILE}")
        with open(RAW_CACHE_FILE) as f:
            cached = json.load(f)
        rows = cached
        seen = {r["full_name"] for r in rows}
        n_active = sum(1 for r in rows if r["is_inactive"] == 0)
        n_inactive = sum(1 for r in rows if r["is_inactive"] == 1)
        log.info(f"Resuming from cache: {n_active} active, {n_inactive} inactive rows.")

    # --- Pass 1: collect inactive repos ---
    n_inactive_have = sum(1 for r in rows if r["is_inactive"] == 1)
    need_inactive = max(0, inactive_target - n_inactive_have)
    if need_inactive > 0:
        log.info(f"Pass 1 — collecting {need_inactive} inactive repos...")
        pbar = tqdm(total=need_inactive, initial=0, desc="Inactive repos")
        _collect_pass(session, need_inactive, inactive_only=True, seen=seen, rows=rows, pbar=pbar)
        pbar.close()
    else:
        log.info("Inactive target already met from cache.")

    # --- Pass 2: collect active repos ---
    n_active_have = sum(1 for r in rows if r["is_inactive"] == 0)
    need_active = max(0, active_target - n_active_have)
    if need_active > 0:
        log.info(f"Pass 2 — collecting {need_active} active repos...")
        pbar = tqdm(total=need_active, initial=0, desc="Active repos")
        _collect_pass(session, need_active, inactive_only=False, seen=seen, rows=rows, pbar=pbar)
        pbar.close()
    else:
        log.info("Active target already met from cache.")

    # Final checkpoint save
    RAW_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_CACHE_FILE, "w") as f:
        json.dump(rows, f)

    # Build DataFrame, shuffle, and save
    import random
    random.shuffle(rows)
    df = pd.DataFrame(rows[:target_rows])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info(f"Saved {len(df)} rows → {out_path}")

    # Class distribution
    counts = df["is_inactive"].value_counts()
    total = len(df)
    log.info("=== Class distribution ===")
    log.info(f"  Active   (0): {counts.get(0, 0):>6}  ({counts.get(0, 0)/total*100:.1f}%)")
    log.info(f"  Inactive (1): {counts.get(1, 0):>6}  ({counts.get(1, 0)/total*100:.1f}%)")

    minority_pct = counts.get(1, 0) / total * 100
    if 5 <= minority_pct <= 25:
        log.info(f"✅ Minority class ratio {minority_pct:.1f}% is VALID (5–25%)")
    else:
        log.warning(f"⚠️  Minority class ratio {minority_pct:.1f}% is OUT OF RANGE (5–25%)")

    # Save sample
    sample_path = out_path.parent / "sample.csv"
    df.sample(min(100, len(df)), random_state=42).to_csv(sample_path, index=False)
    log.info(f"Saved 100-row sample → {sample_path}")

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect GitHub repo dataset.")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--rows", type=int, default=12000, help="Target number of rows (default 12000)")
    parser.add_argument("--out", default="../data/dataset.csv", help="Output CSV path")
    args = parser.parse_args()

    collect(
        token=args.token,
        target_rows=args.rows,
        out_path=Path(args.out),
    )
