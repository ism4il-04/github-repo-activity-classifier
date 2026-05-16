# DATASET.md — GitHub Repository Activity Dataset

## a) Identification

| Field | Value |
|---|---|
| **Name** | GitHub Repository Activity Dataset |
| **Author(s)** | Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER |
| **Date of collection** | 2026-05-15 |
| **Version** | 1.0 |
| **File** | `data/dataset.csv` |

---

## b) Source

| Field | Value |
|---|---|
| **API** | GitHub REST API v2022-11-28 |
| **Base URL** | `https://api.github.com` |
| **Date of access** | 2026-05-15 |
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

A **two-pass stratified collection** was used to correct the structural bias of the GitHub Search API, which by default returns only recently active repositories (sorted by `updated desc`), making the inactive class invisible without an explicit `pushed:<cutoff` filter:
- **Pass 1 :** `pushed:<cutoff` — collects guaranteed inactive repos (2,250 rows)
- **Pass 2 :** `pushed:>cutoff` — collects guaranteed active repos (12,750 rows)

---

## c.1) Scope, Population, and Collection Bias

### Why the raw GitHub population is out of scope

GitHub hosts 420M+ repositories. Of these, studies consistently report 70–80% as inactive when measuring the **raw population** — but this population includes millions of student projects, empty forks, one-commit experiments, and personal scratchpads that are never used as dependencies. This statistic is **not relevant** to our use case.

### Target sub-population and the star filter

Our dataset targets a **qualified sub-population**: repositories with **at least 1 star and at least 30 days of existence**. This acts as a minimal visibility filter — a repo with at least one star has been noticed by at least one person outside the owner, making it a plausible candidate for use as a dependency or reference project.

This filter is applied implicitly through the `stars:0..5` minimum range (≥ 0 stars collected, but the collection script excludes repos younger than 30 days) and explicitly via the age filter `repo_age_days >= 30`.

### Class imbalance — empirical validation

On this qualified sub-population, the 15% inactive rate is **empirically validated by academic literature**:

| Source | Finding | Relevance |
|---|---|---|
| Avelino et al. (2019), MSR — *doi.org/10.1109/MSR.2019.00059* | ~16% of 1,932 popular GitHub projects classified as abandoned | Direct validation of our 15% target on a similar qualified population |
### Correcting the GitHub Search API structural bias

Without the two-pass strategy, querying GitHub's Search API with default sorting (`sort=updated, order=desc`) returns results overwhelmingly skewed toward recently active repositories. In practice, this produced **0% inactive repos** in early testing. The `pushed:<cutoff` filter in Pass 1 directly targets the inactive sub-population, ensuring the dataset reflects the true distribution of the qualified population rather than an artifact of the API's ranking algorithm.

---

## c) Description

### Problem statement

This dataset supports a **binary supervised classification** task: predicting whether a GitHub repository **used as a dependency** (≥ 1 star, ≥ 30 days old) will become **inactive** (no code push for 180+ days). This is framed as a present-state label — a repo is labeled inactive if it has not been pushed to in the last 180 days at the time of collection.

**Target population:** Public GitHub repositories with **at least 1 star and at least 30 days of existence** — a proxy for libraries and tools that are actually visible and potentially used as production dependencies. This deliberately excludes student projects, empty forks, test repos, and abandoned experiments that make up the majority of GitHub's 420M+ raw repository count but are out of scope for dependency risk assessment.

**Business value:** OSS dependency managers, developer tools, and security teams need to flag potentially abandoned libraries before they become risks in production software.

### Dataset dimensions

| Property | Value |
|---|---|
| Number of rows | 15,000 |
| Number of features | 19 (11 numeric, 2 categorical, 6 binary) |
| Target variable | `is_inactive` |
| Minority class (inactive) | ~15% (naturally imbalanced) |

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

> | Class | Count | % |
> |---|---|---|
> | 0 — active | 12,750 | 85.0% |
> | 1 — inactive | 2,250 | 15.0% |

*(See bar chart in `notebooks/01_discovery.ipynb` and `data/class_distribution.png`)*

---

## d) Known limitations

- `contributor_count` is capped at 100 by the script's single-page call; repos with more contributors will show 100.
- `avg_issue_response_hours` is `-1.0` for repos with no closed issues — treat as a missing value category.
- The 180-day threshold is a design choice; adjust in `data_collection.py` to change the definition of inactivity.
- GitHub's Search API does not expose commit frequency directly; `engagement_rate` is an approximation.
- Repos less than 30 days old are excluded to avoid labeling genuinely new repos as inactive.
