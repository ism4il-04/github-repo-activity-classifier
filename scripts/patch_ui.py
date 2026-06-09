import os
import re

ui_path = r'app/ui.py'
with open(ui_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update English translations
en_translations = '''        "upload_csv_label": "Drop CSV here",
        "github_token": "GitHub Token (Optional)",
        "github_url_label": "GitHub Repository URL",
        "btn_fetch": "Fetch from GitHub",
        "fetch_success": "Successfully fetched {repo}!",
        "fetch_error": "Could not fetch {repo}: {err}",'''
content = content.replace('        "upload_csv_label": "Drop CSV here",', en_translations)

# 2. Update French translations
fr_translations = '''        "upload_csv_label": "Déposer un CSV ici",
        "github_token": "Token GitHub (Optionnel)",
        "github_url_label": "URL du dépôt GitHub",
        "btn_fetch": "Importer depuis GitHub",
        "fetch_success": "Importation réussie pour {repo} !",
        "fetch_error": "Impossible d'importer {repo} : {err}",'''
content = content.replace('        "upload_csv_label": "Déposer un CSV ici",', fr_translations)

# 3. Add fetch_github_repo function
fetch_func = '''
import datetime

def fetch_github_repo(url: str, token: str):
    import re
    match = re.search(r"github\\.com/([^/]+)/([^/]+)", url)
    if not match:
        return "Invalid GitHub URL format."
    owner, repo_name = match.groups()
    repo_name = repo_name.removesuffix(".git")
    full_name = f"{owner}/{repo_name}"

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        r = httpx.get(f"https://api.github.com/repos/{full_name}", headers=headers, timeout=10.0)
        if r.status_code == 404:
            return "Repository not found or private."
        elif r.status_code == 403:
            return "API Rate limit exceeded. Please provide a GitHub token."
        r.raise_for_status()
        repo = r.json()

        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        open_issues = repo.get("open_issues_count", 0)
        size_kb = float(repo.get("size", 0))

        created_at_str = repo.get("created_at")
        if not created_at_str:
            return "Missing created_at field."
        created_at = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        repo_age_days = max((now - created_at).days, 30)

        engagement_rate = round((stars + forks) / max(repo_age_days, 1), 4)
        stars_forks_ratio = round(stars / max(forks, 1), 2)

        language = repo.get("language") or "Other"
        from app.ui import PROG_LANGUAGES, LICENSES # hacky scope resolution if needed
        if language not in PROG_LANGUAGES:
            language = "Other"
            
        license_name = repo["license"]["name"] if repo.get("license") else "Other"
        found_license = "Other"
        for lic in LICENSES:
            if lic in license_name or license_name in lic:
                found_license = lic
                break
        
        has_description = bool(repo.get("description"))
        has_homepage = bool(repo.get("homepage"))
        has_wiki = bool(repo.get("has_wiki", False))
        has_projects = bool(repo.get("has_projects", False))
        is_fork = bool(repo.get("fork", False))

        contributor_count = -1
        try:
            r_c = httpx.get(f"https://api.github.com/repos/{full_name}/contributors?per_page=100&anon=true", headers=headers, timeout=5.0)
            if r_c.status_code == 200:
                contributor_count = len(r_c.json())
        except Exception:
            pass

        avg_issue_response_hours = -1.0
        try:
            r_i = httpx.get(f"https://api.github.com/repos/{full_name}/issues?state=closed&per_page=20", headers=headers, timeout=5.0)
            if r_i.status_code == 200:
                data = r_i.json()
                deltas = []
                for issue in data:
                    if "pull_request" in issue:
                        continue
                    c_at = issue.get("created_at")
                    cl_at = issue.get("closed_at")
                    if c_at and cl_at:
                        t0 = datetime.datetime.fromisoformat(c_at.replace("Z", "+00:00"))
                        t1 = datetime.datetime.fromisoformat(cl_at.replace("Z", "+00:00"))
                        deltas.append((t1 - t0).total_seconds() / 3600)
                if deltas:
                    avg_issue_response_hours = round(sum(deltas) / len(deltas), 2)
        except Exception:
            pass

        return {
            "stars": stars, "forks": forks, "watchers": watchers, "open_issues": open_issues,
            "size_kb": size_kb, "repo_age_days": repo_age_days, "engagement_rate": engagement_rate,
            "stars_forks_ratio": stars_forks_ratio, "language": language, "license_name": found_license,
            "has_description": has_description, "has_homepage": has_homepage, "has_wiki": has_wiki,
            "has_projects": has_projects, "is_fork": is_fork, "contributor_count": contributor_count,
            "avg_issue_response_hours": avg_issue_response_hours
        }

    except Exception as e:
        return str(e)

def mock_predict_single'''

content = content.replace("def mock_predict_single", fetch_func)

# 4. Add token to sidebar
sidebar_ext = '''
    st.divider()
    gh_token = st.text_input(t("github_token"), type="password")
    st.session_state["gh_token"] = gh_token
    st.caption(t("footer_caption"))'''
content = content.replace('    st.divider()\n    st.caption(t("footer_caption"))', sidebar_ext)

# 5. Add fetch form to tab_single
fetch_form = '''
        st.markdown(f'<p class="section-label">{t("section_input")}</p>', unsafe_allow_html=True)
        with st.container(border=False):
            with st.form("github_fetch_form", border=False):
                gh_url = st.text_input(t("github_url_label"), placeholder="https://github.com/owner/repo")
                fetch_btn = st.form_submit_button(t("btn_fetch"), type="secondary")
            if fetch_btn and gh_url:
                with st.spinner("Fetching..."):
                    res = fetch_github_repo(gh_url, st.session_state.get("gh_token", ""))
                    if isinstance(res, dict):
                        st.session_state.update(res)
                        st.success(t("fetch_success", repo=gh_url))
                    else:
                        st.error(t("fetch_error", repo=gh_url, err=res))
            
            st.markdown(
                f'<div class="glass-card" style="margin-bottom:0">'
'''
content = content.replace('        st.markdown(f\'<p class="section-label">{t("section_input")}</p>\', unsafe_allow_html=True)\n        with st.container(border=False):\n            st.markdown(\n                f\'<div class="glass-card" style="margin-bottom:0">\'', fetch_form)

# 6. Replace form fields with default values from session_state
content = content.replace('value=8, step=1)', 'value=int(st.session_state.get("stars", 8)), step=1)')
content = content.replace('value=2, step=1)', 'value=int(st.session_state.get("forks", 2)), step=1)')
content = content.replace('value=8, step=1)', 'value=int(st.session_state.get("watchers", 8)), step=1)')
content = content.replace('value=1, step=1)', 'value=int(st.session_state.get("open_issues", 1)), step=1)')
content = content.replace('value=3, step=1,', 'value=int(st.session_state.get("contributor_count", 3)), step=1,')
content = content.replace('value=1500.0, step=100.0)', 'value=float(st.session_state.get("size_kb", 1500.0)), step=100.0)')
content = content.replace('value=600, step=10)', 'value=int(st.session_state.get("repo_age_days", 600)), step=10)')
content = content.replace('value=0.016, format="%.5f",', 'value=float(st.session_state.get("engagement_rate", 0.016)), format="%.5f",')
content = content.replace('value=4.0, format="%.2f",', 'value=float(st.session_state.get("stars_forks_ratio", 4.0)), format="%.2f",')
content = content.replace('value=24.0, step=1.0,', 'value=float(st.session_state.get("avg_issue_response_hours", 24.0)), step=1.0,')

content = content.replace('language = st.selectbox(t("field_primary_language"), PROG_LANGUAGES)',
                          'idx_lang = PROG_LANGUAGES.index(st.session_state.get("language", "Python")) if st.session_state.get("language", "Python") in PROG_LANGUAGES else 0\n                    language = st.selectbox(t("field_primary_language"), PROG_LANGUAGES, index=idx_lang)')
content = content.replace('license_name = st.selectbox(t("field_license"), LICENSES)',
                          'idx_lic = LICENSES.index(st.session_state.get("license_name", "MIT License")) if st.session_state.get("license_name", "MIT License") in LICENSES else 0\n                    license_name = st.selectbox(t("field_license"), LICENSES, index=idx_lic)')

content = content.replace('value=True)', 'value=bool(st.session_state.get("has_description", True)))')
content = content.replace('has_wiki = st.checkbox(t("flag_wiki"), value=True)', 'has_wiki = st.checkbox(t("flag_wiki"), value=bool(st.session_state.get("has_wiki", True)))')
content = content.replace('value=False)', 'value=bool(st.session_state.get("is_fork", False)))')
content = content.replace('has_homepage = st.checkbox(t("flag_homepage"), value=False)', 'has_homepage = st.checkbox(t("flag_homepage"), value=bool(st.session_state.get("has_homepage", False)))')
content = content.replace('has_projects = st.checkbox(t("flag_projects"), value=False)', 'has_projects = st.checkbox(t("flag_projects"), value=bool(st.session_state.get("has_projects", False)))')

# Note: has_description uses `value=bool(...)` above so we need to be careful with the exact replacements. Let's do regex replacements for checkboxes instead to be safe, but they are all unique. Wait, has_description is just 'value=True)', let's rollback and replace properly.
content = content.replace('value=bool(st.session_state.get("has_description", True)))', 'value=True)') # revert
content = content.replace('value=bool(st.session_state.get("is_fork", False)))', 'value=False)') # revert

content = content.replace('has_description = st.checkbox(t("flag_description"), value=True)', 'has_description = st.checkbox(t("flag_description"), value=bool(st.session_state.get("has_description", True)))')
content = content.replace('is_fork = st.checkbox(t("flag_fork"), value=False)', 'is_fork = st.checkbox(t("flag_fork"), value=bool(st.session_state.get("is_fork", False)))')
content = content.replace('has_homepage = st.checkbox(t("flag_homepage"), value=False)', 'has_homepage = st.checkbox(t("flag_homepage"), value=bool(st.session_state.get("has_homepage", False)))')
content = content.replace('has_projects = st.checkbox(t("flag_projects"), value=False)', 'has_projects = st.checkbox(t("flag_projects"), value=bool(st.session_state.get("has_projects", False)))')

with open(ui_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied.")
