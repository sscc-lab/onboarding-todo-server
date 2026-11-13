#!/usr/bin/env python3
"""3회차 실습 채점 — onboarding-todo-server · onboarding-todo-web 두 Repository를 함께 본다.

준비: gh CLI 로그인(gh auth login), 이 Repository의 solution-advanced Branch에서 pip install -r requirements-dev.txt

사용법 (한 줄 = 한 사람)
    python grading/collect.py alice pages=https://alice-todo-web.pages.dev
    python grading/collect.py --list people.txt --format json > ../evidence.json

people.txt
    alice  pages=https://alice-todo-web.pages.dev
    bob    pages=https://bob-web.pages.dev  server=bob/todo-server  web=bob/todo-web

    아이디   두 Repository의 주인. 기본 이름은 아이디/onboarding-todo-server · 아이디/onboarding-todo-web
    pages=   Cloudflare Pages 주소 (없으면 web Repository의 Website 칸 · Deployments에서 찾는다)
    api=     Render 주소 (없으면 web의 js/config.js에 적힌 API_BASE)
    server= · web=  Repository 이름이 기본과 다를 때
    저장소@브랜치  예: server=sscc-lab/onboarding-todo-server@solution-advanced

주의
- T1은 학생 코드를 이 컴퓨터에서 실행한다. 테스트는 학생의 tests/가 아니라 이 Branch의 tests/(정본)를 쓴다.
  실행하지 않으려면 --no-run.
- 배포한 서비스에는 GET · OPTIONS만 보낸다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CANON_TESTS = os.path.join(os.path.dirname(HERE), "tests")
TYPES = "feat|fix|docs|refactor|chore|init"
RE_BRANCH = re.compile(r"^(feat|fix|docs|refactor|chore)/#(\d+)-\S+$")
RE_COMMIT = re.compile(rf"^#(\d+) ({TYPES}): \S")
RE_PR_TITLE = re.compile(r"^\[#(\d+)\] \S")
RE_PR_TITLE_TYPED = re.compile(rf"^\[#\d+\] ({TYPES})\s*:")
RE_DB_SECRET = re.compile(r"postgres(?:ql)?(?:\+\w+)?://([^\s:/'\"]+):([^\s@'\"]+)@([^\s/'\":]+)")
RE_HOOK = re.compile(r"api\.render\.com/deploy/(srv-[\w-]+)\?key=([\w-]+)")
RE_API_BASE = re.compile(r"""^\s*export\s+const\s+API_BASE\s*=\s*["'`]([^"'`]+)["'`]""", re.M)

ITEMS = [
    ("W1", "기초 · Layer로 옮기기 PR 흐름", 15),
    ("W2", "기초 · Commit 규칙", 5),
    ("W3", "기초 · Review 받기", 10),
    ("T1", "기초 · API 동작 (정본 테스트)", 15),
    ("T2", "기초 · Layer 규칙", 10),
    ("F1", "기초 · 화면 api.js", 5),
    ("C1", "심화 · CI 켜기", 5),
    ("C2", "심화 · Pipeline 배포 성공", 10),
    ("C3", "심화 · 배포된 서버가 최신 Commit", 10),
    ("C4", "심화 · Pages 화면 · CORS", 5),
    ("X1", "심화 · 장애 기록", 10),
]
POINTS = {k: p for k, _, p in ITEMS}
TITLES = {k: t for k, t, _ in ITEMS}
PENALTY = 10
PASS_SCORE = 70

LAYER_RULES = {  # 파일 → 들어 있으면 안 되는 것
    "app/routers/todo.py": ["session.add", "session.commit", "session.delete", "select("],
    "app/services/todo_service.py": ["HTTPException", "from fastapi", "status_code", "session."],
    "app/repositories/todo_repository.py": ["HTTPException", "from fastapi", "status_code"],
}
FUNCS = {
    "createTodo": ["fetch(", "POST", "JSON.stringify", "content-type"],
    "updateTitle": ["fetch(", "PATCH", "JSON.stringify", "content-type", "title"],
    "setCompleted": ["fetch(", "PATCH", "JSON.stringify", "content-type", "completed"],
    "deleteTodo": ["fetch(", "DELETE"],
}

QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner name homepageUrl
    owner { login }
    deployments(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) { nodes { latestStatus { environmentUrl } } }
    defaultBranchRef { target { ... on Commit {
      oid
      history(first: 100) { nodes {
        oid messageHeadline
        author { name user { login } }
        associatedPullRequests(first: 3) { nodes { number } }
      } }
    } } }
    issues(first: 100, orderBy: {field: CREATED_AT, direction: ASC}) { nodes {
      number title body state author { login }
      closedByPullRequestsReferences(first: 5, includeClosedPrs: true) { nodes { number } }
    } }
    pullRequests(first: 100, orderBy: {field: CREATED_AT, direction: ASC}) { nodes {
      number title state merged mergedAt headRefName
      author { login }
      mergeCommit { messageHeadline parents(first: 3) { totalCount } }
      closingIssuesReferences(first: 5) { nodes { number } }
      files(first: 50) { nodes { path } }
      commits(first: 100) { nodes { commit { messageHeadline parents(first: 3) { totalCount } author { name user { login } } } } }
      reviews(first: 50) { nodes { state submittedAt author { login } } }
    } }
  }
}
"""


# ───────────────────────── 수집 ─────────────────────────

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def split_ref(spec):
    name, _, ref = spec.partition("@")
    return name, (ref or None)


def gh_repo(full):
    owner, name = full.split("/", 1)
    res = run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={name}"])
    if res.returncode != 0:
        return None, res.stderr.strip()
    data = json.loads(res.stdout)
    repo = (data.get("data") or {}).get("repository")
    return (repo, None) if repo else (None, str(data.get("errors")))


def gh_rest(path):
    res = run(["gh", "api", path])
    return json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else None


def clone(full, ref, dest):
    args = ["git", "clone", "--quiet", "--no-single-branch"] + (["--branch", ref] if ref else []) + [f"https://github.com/{full}.git", dest]
    res = run(args)
    if res.returncode != 0:
        raise SystemExit(f"[{full}] clone 실패: {res.stderr.strip()}")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def scan_secrets(dest):
    """모든 Branch 이력에서 DB 비밀번호 · Render Deploy Hook을 찾는다. 값은 가린다."""
    log = run(["git", "log", "--all", "-p", "--no-color", "--format=commit %H"], cwd=dest).stdout
    found, sha, path = [], None, None
    for line in log.splitlines():
        if line.startswith("commit "):
            sha = line[7:14]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            for m in RE_DB_SECRET.finditer(line):
                if m.group(2) in ("[YOUR-PASSWORD]", "password", "PASSWORD", "…", "..."):
                    continue
                found.append(f"{sha} `{path}` — postgresql://{m.group(1)}:****@{m.group(3)}")
            for m in RE_HOOK.finditer(line):
                found.append(f"{sha} `{path}` — Render Deploy Hook {m.group(1)}?key=****")
    return sorted(set(found))


def run_canon_tests(dest):
    """학생의 app/에 정본 tests/를 붙여 pytest를 돌린다."""
    work = tempfile.mkdtemp(prefix="todo3-test-")
    try:
        shutil.copytree(os.path.join(dest, "app"), os.path.join(work, "app"))
        shutil.copytree(CANON_TESTS, os.path.join(work, "tests"), ignore=shutil.ignore_patterns("__pycache__"))
        xml = os.path.join(work, "result.xml")
        env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "REQUIRE_DATABASE_URL", "ALLOWED_ORIGINS")}
        try:
            res = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", "tests"], cwd=work, env=env, timeout=180)
        except subprocess.TimeoutExpired:
            return {"error": "180초 안에 끝나지 않았다", "cases": []}
        if not os.path.exists(xml):
            return {"error": (res.stdout + res.stderr)[-600:], "cases": []}
        cases = []
        for tc in ET.parse(xml).getroot().iter("testcase"):
            bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
            msg = (bad.get("message") or "")[:200] if bad is not None else ""
            cases.append({"name": tc.get("name"), "ok": bad is None and tc.find("skipped") is None, "detail": msg})
        return {"error": None if cases else (res.stdout + res.stderr)[-600:], "cases": cases}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def http(url, method="GET", headers=None, timeout=30):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "onboarding-todo-grader", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": r.status, "headers": {k.lower(): v for k, v in r.headers.items()}, "body": r.read(200_000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "headers": {k.lower(): v for k, v in e.headers.items()}, "body": ""}
    except Exception as e:
        return {"status": None, "error": f"{type(e).__name__}: {e}"[:200], "headers": {}, "body": ""}


def origin_of(url):
    m = re.match(r"^(https?://[^/]+)", url or "")
    return m.group(1) if m else None


def actions(full):
    """main Push 실행 · PR 실행 · 최근 main 실행의 Job 결과."""
    owner_repo = full
    pr = gh_rest(f"repos/{owner_repo}/actions/runs?event=pull_request&per_page=5") or {}
    main = gh_rest(f"repos/{owner_repo}/actions/runs?branch=main&event=push&per_page=10") or {}
    runs = [{"id": r["id"], "sha": r["head_sha"], "status": r["status"], "conclusion": r["conclusion"], "url": r["html_url"]}
            for r in main.get("workflow_runs") or []]
    jobs = {}
    done = [r for r in runs if r["status"] == "completed"]
    if done:
        j = gh_rest(f"repos/{owner_repo}/actions/runs/{done[0]['id']}/jobs") or {}
        jobs = {x["name"]: x["conclusion"] for x in j.get("jobs") or []}
    return {"pr_runs": pr.get("total_count", 0), "main_runs": runs, "latest_jobs": jobs}


def collect(spec, run_tests=True):
    login = spec["login"]
    s_name, s_ref = split_ref(spec.get("server") or f"{login}/onboarding-todo-server")
    w_name, w_ref = split_ref(spec.get("web") or f"{login}/onboarding-todo-web")
    server, err = gh_repo(s_name)
    if server is None:
        raise SystemExit(f"[{s_name}] GitHub에서 읽지 못했습니다: {err}")
    web, _ = gh_repo(w_name)

    out = {"spec": spec, "server": server, "web": web, "local": {}, "live": {}, "actions": actions(s_name)}
    tmp = tempfile.mkdtemp(prefix="todo3-")
    try:
        sd = os.path.join(tmp, "server")
        clone(s_name, s_ref, sd)
        out["local"]["layers"] = {f: read(os.path.join(sd, f)) for f in LAYER_RULES}
        wf = os.path.join(sd, ".github", "workflows")
        out["local"]["workflows"] = sorted(os.listdir(wf)) if os.path.isdir(wf) else []
        out["local"]["secrets"] = scan_secrets(sd)
        app_src = "".join(out["local"]["layers"].get(f) or "" for f in LAYER_RULES)
        if RE_DB_SECRET.search(app_src):
            out["local"]["tests"] = {"error": "app/에 DB 주소가 적혀 있어 실행하지 않았다", "cases": [], "human": True}
        elif run_tests:
            out["local"]["tests"] = run_canon_tests(sd)
        if web:
            wd = os.path.join(tmp, "web")
            clone(w_name, w_ref, wd)
            out["local"]["api_js"] = read(os.path.join(wd, "js", "api.js")) or ""
            out["local"]["config_js"] = read(os.path.join(wd, "js", "config.js")) or ""
            out["local"]["secrets"] += scan_secrets(wd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    m = RE_API_BASE.search(out["local"].get("config_js") or "")
    base = (spec.get("api") or (m.group(1) if m else "")).rstrip("/")
    pages = spec.get("pages") or ((web or {}).get("homepageUrl") or "")
    if not pages:
        for d in ((web or {}).get("deployments") or {}).get("nodes") or []:
            u = ((d or {}).get("latestStatus") or {}).get("environmentUrl") or ""
            if "pages.dev" in u:
                pages = u
                break
    live = {"api_base": base, "pages": pages}
    if spec.get("api") or (base.startswith("http") and not re.search(r"//(localhost|127\.0\.0\.1)", base)):
        live["root"] = http(base + "/", timeout=90)  # Render 무료 인스턴스는 깨어나는 데 1분 가까이 걸린다
        live["todos"] = http(base + "/todos")
        if pages:
            o = origin_of(pages)
            live["cors_get"] = http(base + "/todos", headers={"Origin": o})
            live["cors_pre"] = http(base + "/todos", method="OPTIONS", headers={"Origin": o, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    if pages:
        live["pages_get"] = http(pages)
    for k in ("root", "todos", "cors_get", "cors_pre"):
        if k in live:
            try:
                live[k]["json"] = json.loads(live[k]["body"])
            except ValueError:
                live[k]["json"] = None
            live[k]["body"] = live[k]["body"][:300]
    if "pages_get" in live:
        b = live["pages_get"]["body"]
        live["pages_get"]["is_todo"] = 'id="new-form"' in b
        live["pages_get"]["body"] = ""
    out["live"] = live
    return out


# ───────────────────────── 판정 도우미 ─────────────────────────

def nodes(obj, key):
    return ((obj or {}).get(key) or {}).get("nodes") or []


def login_of(a):
    return (a or {}).get("login")


def commit_login(c):
    return login_of((c.get("author") or {}).get("user"))


def result(key, status, evidence, ai=False, score=None):
    full = POINTS[key]
    if score is None:
        score = {"pass": full, "partial": (full + 1) // 2, "fail": 0, "human": 0}[status]
    return {"id": key, "title": TITLES[key], "points": full, "status": status, "score": score, "ai_check": ai, "evidence": evidence}


def linked_issue(pr):
    refs = [n["number"] for n in nodes(pr, "closingIssuesReferences")]
    if refs:
        return refs[0]
    for text in (pr["title"], pr["headRefName"]):
        m = re.search(r"#(\d+)", text or "")
        if m:
            return int(m.group(1))
    return None


def layer_prs(gh, owner):
    return [pr for pr in nodes(gh, "pullRequests") if login_of(pr["author"]) == owner
            and any(f["path"] in LAYER_RULES for f in nodes(pr, "files"))]


def pr_problems(pr, issues):
    n, bad = linked_issue(pr), []
    b = RE_BRANCH.match(pr["headRefName"])
    if not b or int(b.group(2)) != (n or -1):
        bad.append(f"Branch `{pr['headRefName']}`")
    if not RE_PR_TITLE.match(pr["title"]) or RE_PR_TITLE_TYPED.match(pr["title"]):
        bad.append("제목 형식")
    issue = issues.get(n)
    if not nodes(pr, "closingIssuesReferences"):
        bad.append("`Closes #번호` 없음")
    elif pr["merged"] and not (issue and pr["number"] in [x["number"] for x in nodes(issue, "closedByPullRequestsReferences")]):
        bad.append(f"Issue #{n}이 이 PR로 닫히지 않음")
    mc = pr.get("mergeCommit") or {}
    if not pr["merged"]:
        bad.append("아직 합치지 않음")
    elif not (mc.get("parents", {}).get("totalCount") == 1 and (mc.get("messageHeadline") or "").endswith(f"(#{pr['number']})")):
        bad.append("Squash and merge 아님")
    return bad


def short(text, n=200):
    text = (text or "").strip().replace("\r", "")
    return text if len(text) <= n else text[:n] + "…"


def extract_function(src, name):
    m = re.search(rf"function\s+{name}\s*\(", src)
    if not m:
        return None
    i, depth = src.find("{", m.end()), 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0 and src[j] == "}":
            return src[m.start(): j + 1]
    return None


# ───────────────────────── 항목별 판정 ─────────────────────────

def check_flow(gh, prs):
    issues = {i["number"]: i for i in nodes(gh, "issues")}
    merged = [p for p in prs if p["merged"]]
    if not merged:
        return result("W1", "fail", ["Layer 파일을 고친 PR이 합쳐진 것이 없다"])
    ev, good = [f"합쳐진 Layer PR {len(merged)}개"], 0
    for pr in prs:
        bad = pr_problems(pr, issues)
        good += not bad
        ev.append(f"#{pr['number']} «{pr['title']}» " + ("— 규칙대로" if not bad else "— " + " · ".join(bad)))
    if len(merged) >= 3 and good == len(prs):
        return result("W1", "pass", ev)
    return result("W1", "partial", ev + (["PR이 세 개보다 적다 (기능마다 PR 하나)"] if len(merged) < 3 else []))


def check_commits(prs, owner):
    commits = [(pr, n["commit"]) for pr in prs for n in nodes(pr, "commits")
               if n["commit"]["parents"]["totalCount"] < 2 and commit_login(n["commit"]) in (owner, None)]
    if not commits:
        return result("W2", "fail", ["Layer PR에 본인 Commit이 없다"])
    bad = [f"PR #{pr['number']}: `{c['messageHeadline']}`" for pr, c in commits
           if not (RE_COMMIT.match(c["messageHeadline"]) and int(RE_COMMIT.match(c["messageHeadline"]).group(1)) == (linked_issue(pr) or -1))]
    status = "pass" if not bad else "partial" if len(bad) <= len(commits) / 2 else "fail"
    return result("W2", status, [f"본인 Commit {len(commits)}개 중 규칙 위반 {len(bad)}개"] + bad)


def check_reviews(prs, owner):
    if not prs:
        return result("W3", "fail", ["Layer PR이 없다"])
    ok, ev = 0, []
    for pr in prs:
        appr = [r for r in nodes(pr, "reviews") if r["state"] == "APPROVED" and login_of(r["author"]) != owner
                and (not pr["mergedAt"] or r["submittedAt"] <= pr["mergedAt"])]
        ok += bool(appr)
        ev.append(f"#{pr['number']}: " + (f"Approve by @{login_of(appr[0]['author'])}" if appr else "합치기 전 Pair의 Approve 없음"))
    return result("W3", "pass" if ok == len(prs) else "partial" if ok else "fail", ev)


def check_tests(local):
    t = local.get("tests")
    if t is None:
        return result("T1", "human", ["--no-run으로 실행하지 않았다"])
    if t.get("human"):
        return result("T1", "human", [t["error"] + " — 사람 확인 (비밀 값 감점은 따로)"])
    cases = t["cases"]
    if not cases:
        return result("T1", "fail", ["테스트를 돌리지 못했다: " + short(t.get("error"), 500)])
    passed = sum(c["ok"] for c in cases)
    ev = [f"{passed} / {len(cases)} 통과 (정본 tests/)"] + [f"✗ {c['name']} — {c['detail']}" for c in cases if not c["ok"]][:8]
    status = "pass" if passed == len(cases) else "fail" if passed == 0 else "partial"
    return result("T1", status, ev, score=round(POINTS["T1"] * passed / len(cases)))


def check_layers(local):
    ok, ev = 0, []
    for f, banned in LAYER_RULES.items():
        src = local["layers"].get(f)
        if src is None:
            ev.append(f"✗ `{f}` 파일이 없다")
            continue
        code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
        code = re.sub(r'"""[\s\S]*?"""', "", code)  # 설명 문자열은 빼고 본다
        hit = [b for b in banned if b in code]
        if "NotImplementedError" in code or "아직 구현하지 않았습니다" in code:
            ev.append(f"✗ `{f}` — 아직 비운 함수가 있다")
        elif hit:
            ev.append(f"✗ `{f}` — 이 층에 있으면 안 되는 것: {', '.join(hit)}")
        else:
            ok += 1
            ev.append(f"✓ `{f}`")
    status = "pass" if ok == 3 else "fail" if ok == 0 else "partial"
    return result("T2", status, [f"{ok} / 3 파일"] + ev, ai=True, score=round(POINTS["T2"] * ok / 3))


def check_api_js(local):
    src = local.get("api_js")
    if src is None:
        return result("F1", "fail", ["onboarding-todo-web Repository를 찾지 못했다"])
    ok, ev = 0, []
    for name, needs in FUNCS.items():
        body = extract_function(src, name)
        if body is None or "아직 옮기지 않았습니다" in body:
            ev.append(f"✗ {name} — 비어 있다")
            continue
        miss = [n for n in needs if n.lower() not in body.lower()]
        if miss:
            ev.append(f"✗ {name} — 빠진 것: {', '.join(miss)}")
            continue
        ok += 1
    ev.insert(0, f"{ok} / 4 함수")
    status = "pass" if ok == 4 else "fail" if ok == 0 else "partial"
    return result("F1", status, ev, score=round(POINTS["F1"] * ok / 4))


def check_ci(local, act):
    wf = local.get("workflows") or []
    if not wf:
        return result("C1", "fail", ["main에 .github/workflows/ 파일이 없다 — CI를 켜지 않았다"])
    ev = [f"Workflow: {', '.join(wf)}", f"PR에서 돈 실행 {act['pr_runs']}번"]
    return result("C1", "pass" if act["pr_runs"] else "partial", ev + ([] if act["pr_runs"] else ["PR에서 CI가 돈 기록이 없다"]))


def check_pipeline(act, repo):
    runs = act["main_runs"]
    if not runs:
        return result("C2", "fail", ["main에 Push(Merge)로 돈 Pipeline이 없다"])
    done = [r for r in runs if r["status"] == "completed"]
    if not done:
        return result("C2", "human", ["main Pipeline이 아직 도는 중이다 — 끝난 뒤 다시 채점"])
    last, jobs = done[0], act["latest_jobs"]
    ev = [f"최근 main 실행: {last['conclusion']} {last['url']}", "Job: " + ", ".join(f"{k}={v}" for k, v in jobs.items())]
    if last["conclusion"] == "success" and jobs.get("deploy") == "success":
        return result("C2", "pass", ev)
    if any(r["conclusion"] == "success" for r in done):
        return result("C2", "partial", ev + ["예전에는 성공했지만 최근 실행이 실패했다 — 장애 주입 중이면 되돌렸는지 확인"])
    return result("C2", "fail", ev)


def check_live(live, head):
    base = live["api_base"]
    if "root" not in live:
        return result("C3", "fail", [f"web의 API_BASE가 `{base or '없음'}` — 새 Render 주소로 바꾸지 않았다"])
    r = live["root"]
    ver = (r.get("json") or {}).get("version") if isinstance(r.get("json"), dict) else None
    ev = [f"GET {base}/ → {r['status'] or r.get('error')} · version `{ver}`", f"main 최신 Commit `{(head or '')[:7]}`"]
    todos_ok = live.get("todos", {}).get("status") == 200 and isinstance(live["todos"].get("json"), list)
    if r["status"] != 200:
        return result("C3", "fail", ev + ["서버가 응답하지 않는다 — Render Events · Logs"])
    if ver == head and todos_ok:
        return result("C3", "pass", ev)
    if ver == "dev":
        ev.append("version이 dev — CI가 만든 Image가 아니라 다른 방법으로 배포했다")
    elif ver != head:
        ev.append("최신 Commit이 아직 배포되지 않았다 (배포 중이거나 deploy 실패)")
    if not todos_ok:
        ev.append("GET /todos가 TODO 배열을 돌려주지 않는다")
    return result("C3", "partial", ev)


def check_pages(live):
    if not live["pages"]:
        return result("C4", "human", ["Pages 주소를 찾지 못했다 — 목록에 pages=주소를 적는다"])
    p = live.get("pages_get") or {}
    ev = [f"GET {live['pages']} → {p.get('status') or p.get('error')}"]
    page_ok = p.get("status") == 200 and p.get("is_todo")
    cors_ok = False
    if "cors_get" in live:
        o = origin_of(live["pages"])
        a1 = live["cors_get"]["headers"].get("access-control-allow-origin")
        a2 = live["cors_pre"]["headers"].get("access-control-allow-origin")
        ev.append(f"CORS Origin {o} → GET `{a1}` · OPTIONS `{a2}`")
        cors_ok = a1 == o and a2 == o
    else:
        ev.append("API가 없어 CORS를 보지 못했다")
    status = "pass" if page_ok and cors_ok else "partial" if page_ok or cors_ok else "fail"
    return result("C4", status, ev)


def check_incidents(gh, owner):
    found = [i for i in nodes(gh, "issues") if (i["title"] or "").startswith("[장애]")]
    if not found:
        return result("X1", "fail", ["«[장애]»로 시작하는 Issue가 없다"], ai=True)
    good, ev = 0, []
    for i in found:
        body = i["body"] or ""
        log = re.search(r"```text\n([\s\S]*?)```", body)
        log_line = (log.group(1).strip() if log else "")
        filled_log = log_line and not log_line.startswith("여기에 원인을 말해 주는")
        cause = re.search(r"^## 원인[ \t]*\n([\s\S]*?)(?=^## |\Z)", body, re.M)
        filled_cause = bool(cause and re.sub(r"<!--[\s\S]*?-->", "", cause.group(1)).strip())
        stage = [l for l in body.splitlines() if l.startswith("- ") and "**" in l]
        one_stage = len(stage) == 1
        ok = filled_log and filled_cause and one_stage
        good += ok
        sel = re.search(r"\*\*(.+?)\*\*", stage[0]).group(1) if one_stage else ("단계를 고르지 않음" if len(stage) > 1 else "단계 칸 없음")
        ev.append(f"#{i['number']} «{short(i['title'], 60)}» — 단계: {sel} · 로그: «{short(log_line, 120) if filled_log else '비어 있음'}» · 원인: {'있음' if filled_cause else '비어 있음'}")
    status = "pass" if good >= 3 else "partial" if good else "fail"
    return result("X1", status, [f"채운 장애 기록 {good}개 / «[장애]» Issue {len(found)}개"] + ev, ai=True)


# ───────────────────────── 한 사람 채점 ─────────────────────────

def direct_pushes(gh):
    hist = ((((gh or {}).get("defaultBranchRef") or {}).get("target") or {}).get("history") or {}).get("nodes") or []
    return [c for c in hist[:-1] if not nodes(c, "associatedPullRequests")]


def grade(raw):
    server, web, local, live, act = raw["server"], raw["web"], raw["local"], raw["live"], raw["actions"]
    owner = server["owner"]["login"]
    prs = layer_prs(server, owner)
    head = (((server.get("defaultBranchRef") or {}).get("target") or {}).get("oid"))
    items = [
        check_flow(server, prs), check_commits(prs, owner), check_reviews(prs, owner),
        check_tests(local), check_layers(local), check_api_js(local),
        check_ci(local, act), check_pipeline(act, server["nameWithOwner"]), check_live(live, head), check_pages(live),
        check_incidents(server, owner),
    ]
    pushed = [f"{server['nameWithOwner']}: `{c['messageHeadline']}` ({c['oid'][:7]})" for c in direct_pushes(server)]
    if web:
        pushed += [f"{web['nameWithOwner']}: `{c['messageHeadline']}` ({c['oid'][:7]})" for c in direct_pushes(web)]
    penalties = []
    if pushed:
        penalties.append({"name": "main 직접 Push", "points": PENALTY, "evidence": pushed})
    if local.get("secrets"):
        penalties.append({"name": "🚨 비밀 값 Commit — DB 비밀번호 · Deploy Hook을 바로 바꾸게 한다", "points": PENALTY, "evidence": local["secrets"]})
    total = max(0, sum(i["score"] for i in items) - sum(p["points"] for p in penalties))
    return {
        "login": owner, "server": server["nameWithOwner"], "web": (web or {}).get("nameWithOwner"),
        "items": items, "penalties": penalties, "total": total,
        "pending_points": sum(i["points"] for i in items if i["status"] == "human"),
        "verdict": "완료" if total >= PASS_SCORE and not any(i["status"] == "fail" for i in items) else "보완",
    }


MARK = {"pass": "충족", "partial": "부분", "fail": "미충족", "human": "사람 확인"}


def to_markdown(graded):
    out = ["| 아이디 | 점수 | 사람 확인 대기 | 판정 |", "|---|---|---|---|"]
    out += [f"| @{g['login']} | {g['total']} | {g['pending_points']}점 | {g['verdict']} |" for g in graded]
    out.append("")
    for g in graded:
        out.append(f"## @{g['login']} — {g['total']} / 100 · {g['verdict']}" + (f" (사람 확인 {g['pending_points']}점 대기)" if g["pending_points"] else ""))
        out.append(f"\n{g['server']} · {g['web'] or '(web 없음)'}\n")
        out.append("| 항목 | 배점 | 판정 | 점수 | 근거 |\n|---|---|---|---|---|")
        for i in g["items"]:
            ev = "<br>".join(e.replace("\n", "<br>").replace("|", "\\|") for e in i["evidence"])
            out.append(f"| {i['id']} {i['title']} | {i['points']} | {MARK[i['status']]}{' · AI 확인' if i['ai_check'] else ''} | {i['score']} | {ev} |")
        for p in g["penalties"]:
            out.append(f"| 감점 · {p['name']} | −{p['points']} | | | {'<br>'.join(p['evidence'])} |")
        out.append("")
    return "\n".join(out)


def parse_line(line):
    parts = line.split()
    opts = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
    return {"login": parts[0].lstrip("@"), **opts}


def main():
    ap = argparse.ArgumentParser(description="3회차 실습 채점")
    ap.add_argument("people", nargs="*", help="아이디 [pages=…] [api=…] [server=…] [web=…]")
    ap.add_argument("--list", help="한 줄에 한 사람씩 적은 파일")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--no-run", action="store_true", help="학생 코드를 실행하지 않는다 (T1은 사람 확인)")
    ap.add_argument("--raw-out", help="모은 원자료를 저장")
    ap.add_argument("--from-json", help="저장해 둔 원자료로 다시 채점")
    a = ap.parse_args()
    if a.from_json:
        with open(a.from_json, encoding="utf-8") as f:
            raws = json.load(f)
    else:
        lines, cur = [], []
        for tok in a.people:
            if "=" in tok and cur:
                cur.append(tok)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [tok]
        if cur:
            lines.append(" ".join(cur))
        if a.list:
            with open(a.list, encoding="utf-8") as f:
                lines += [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
        if not lines:
            ap.error("아이디를 하나 이상 주세요")
        raws = []
        for l in lines:
            spec = parse_line(l)
            print(f"… @{spec['login']} 확인 중", file=sys.stderr)
            raws.append(collect(spec, run_tests=not a.no_run))
        if a.raw_out:
            with open(a.raw_out, "w", encoding="utf-8") as f:
                json.dump(raws, f, ensure_ascii=False, indent=1)
    graded = [grade(r) for r in raws]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(graded, ensure_ascii=False, indent=1) if a.format == "json" else to_markdown(graded))


if __name__ == "__main__":
    main()
