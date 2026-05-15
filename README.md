# GitHub Repository Activity Dataset — Phase 1

**ENSA Tétouan | Machine Learning 2025-2026**  
**Authors:** Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER  
**Professor:** Pr. Y. EL YOUNOUSSI

---

## Project Overview

Binary supervised classification task: **predict whether a GitHub repository will become inactive** (no push in 180+ days) based on publicly available metadata.

**Business value:** OSS dependency managers and security teams (Snyk, Dependabot, etc.) need to flag potentially abandoned libraries before they become risks in production software.

---

## Repository Structure

```
Project_Phase_1/
├── src/
│   └── data_collection.py     # Data collection script (GitHub REST API)
├── notebooks/
│   └── 01_discovery.ipynb     # Exploratory Data Analysis
├── data/
│   └── .gitkeep               # Folder placeholder (dataset not committed)
├── cadrage.md                 # Project framing document
├── DATASET.md                 # Dataset documentation
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Data Collection

Run the collection script to generate `data/dataset.csv` (~15,000 rows):

```bash
cd src
python data_collection.py --token YOUR_GITHUB_TOKEN --rows 15000 --out ../data/dataset.csv
```

> You need a GitHub Personal Access Token with `public_repo` scope.  
> Get one at: GitHub → Settings → Developer settings → Personal access tokens

**Collection strategy:**
- 7 star ranges × 10 programming languages = diverse, unbiased sample
- Pass 1: 2,250 inactive repos (`pushed:<cutoff`)
- Pass 2: 12,750 active repos (`pushed:>cutoff`)
- Automatically resumes from cache if interrupted

---

## Dataset

| Property | Value |
|---|---|
| Rows | 15,000 |
| Features | 19 (11 numeric, 2 categorical, 6 binary) |
| Target | `is_inactive` (binary: 0 = active, 1 = inactive) |
| Class ratio | ~85% active / ~15% inactive |

See [`DATASET.md`](DATASET.md) for full schema and documentation.

---

## Exploratory Analysis

Open and run all cells in `notebooks/01_discovery.ipynb` after collecting the dataset.

---

## Target Variable Definition

A repository is labeled **inactive (1)** if it has not been pushed to in the **last 180 days** at the time of collection.

> ⚠️ `days_since_last_push` and `archived` must be **dropped before modeling** to avoid data leakage.

