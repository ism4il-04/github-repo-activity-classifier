# DATASET.md — GitHub Repository Activity Dataset

## a) Identification

| Field | Value |
|---|---|
| **Name** | GitHub Repository Activity Dataset |
| **Author(s)** | Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER |
| **Date of collection** | 2026-05-05 |
| **Version** | 1.0 |
| **File** | `data/dataset.csv` |

---

## b) Source

| Field | Value |
|---|---|
| **API** | GitHub REST API v2022-11-28 |
| **Base URL** | `https://api.github.com` |
| **Date of access** | 2026-05-05 |
| **Authentication** | Personal Access Token (read-only, public repos) |

### Endpoints used

| Endpoint | Purpose |
|---|---|
| `GET /search/repositories` | Main search — returns repo metadata |
| `GET /repos/{owner}/{repo}/contributors` | Contributor count per repo |
| `GET /repos/{owner}/{repo}/issues` | Last 20 closed issues for response time |
| `GET /rate_limit` | Rate limit monitoring |

### Sampling strategy

Repositories were sampled across 7 star ranges (0–5, 6–15, 16–50, 51–200, 201–1000, 1001–5000, 5001–50000) and 10 programming languages (Python, JavaScript, Java, C++, Go, Ruby, Rust, TypeScript, PHP, C). This cross-stratified approach ensures diversity in repo size and activity level, preventing selection bias toward popular or recently active repositories.

---

## c) Description

### Problem statement

This dataset supports a **binary supervised classification** task: predicting whether a GitHub repository will become **inactive** (no code push for 180+ days). This is framed as a present-state label — a repo is labeled inactive if it has not been pushed to in the last 180 days at the time of collection.

**Business value:** OSS dependency managers, developer tools, and security teams need to flag potentially abandoned libraries before they become risks in production software.

### Dataset dimensions

| Property | Value |
|---|---|
| Number of rows | ≥ 10,000 |
| Number of features | 19 (11 numeric, 2 categorical, 6 binary) |
| Target variable | `is_inactive` |
| Minority class (inactive) | ~10–20% (naturally imbalanced) |

---

### Feature schema

| Feature | Type | Description | Range / Values |
|---|---|---|---|
| `stars` | numeric (int) | Total GitHub stars | 0 – 500,000+ |
| `forks` | numeric (int) | Total forks | 0 – 100,000+ |
| `open_issues` | numeric (int) | Open issues + PRs at collection time | 0 – 10,000+ |
| `watchers` | numeric (int) | Watchers count | 0 – 500,000+ |
| `size_kb` | numeric (int) | Repository size in kilobytes | 0 – 500,000+ |
| `repo_age_days` | numeric (int) | Days since repo creation | 30 – 5,000+ |
| `days_since_last_push` | numeric (int) | Days since last git push | 0 – 3,000+ |
| `contributor_count` | numeric (int) | Number of distinct contributors (capped at 100 in script) | 1 – 100+ |
| `avg_issue_response_hours` | numeric (float) | Mean time to close last 20 issues (hours); -1.0 if no issues | -1.0 – 10,000+ |
| `engagement_rate` | numeric (float) | (stars + forks) / repo_age_days — proxy for sustained interest | 0.0 – 50.0+ |
| `stars_forks_ratio` | numeric (float) | stars / max(forks, 1) | 0.1 – 1,000+ |
| `language` | categorical | Primary programming language | Python, JavaScript, Java, … Unknown |
| `license` | categorical | License name | MIT, Apache-2.0, GPL-3.0, None, … |
| `has_description` | binary (0/1) | Whether the repo has a non-empty description | 0, 1 |
| `has_homepage` | binary (0/1) | Whether a homepage URL is set | 0, 1 |
| `has_wiki` | binary (0/1) | Whether the GitHub Wiki feature is enabled | 0, 1 |
| `has_projects` | binary (0/1) | Whether GitHub Projects is enabled | 0, 1 |
| `is_fork` | binary (0/1) | Whether this repo is a fork | 0, 1 |
| `archived` | binary (0/1) | Whether the repo is officially archived | 0, 1 |

### Target variable

| Variable | Type | Description |
|---|---|---|
| `is_inactive` | binary (0/1) | **1** = no push in last 180 days (inactive / potentially abandoned); **0** = pushed within last 180 days (active) |

> **Note:** `days_since_last_push` and `archived` are strongly correlated with the target. They should be **dropped before modeling** to avoid data leakage — they are included in the dataset for documentation and EDA purposes only. The `full_name` and `collected_at` identifier columns should also be excluded from the feature matrix.

### Class distribution

> Fill in after collection. Expected distribution:
>
> | Class | Count | % |
> |---|---|---|
> | 0 — active | ~9,000–10,500 | ~85–90% |
> | 1 — inactive | ~1,000–2,000 | ~10–15% |

*(Add a bar chart from `notebooks/01_discovery.ipynb` here)*

---

## d) Known limitations

- `contributor_count` is capped at 100 by the script's single-page call; repos with more contributors will show 100.
- `avg_issue_response_hours` is `-1.0` for repos with no closed issues — treat as a missing value category.
- The 180-day threshold is a design choice; adjust in `data_collection.py` to change the definition of inactivity.
- GitHub's Search API does not expose commit frequency directly; `engagement_rate` is an approximation.
- Repos less than 30 days old are excluded to avoid labeling genuinely new repos as inactive.
