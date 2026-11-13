---
name: grade-arch-practice
description: SSCCOps 3회차 Architecture & CI/CD 실습(onboarding-todo-server · onboarding-todo-web)을 평가표(grading/rubric.md)로 채점한다. 학생 아이디(와 Cloudflare Pages 주소)를 받아 두 Repository의 GitHub 기록 · 정본 테스트 · Actions 결과 · 배포한 서비스 · 장애 기록 Issue를 확인하고, Layer 규칙과 장애 기록의 내용을 판정해 사람별 점수 · 판정 · 보완할 점을 보고한다. "3회차 채점" "Architecture 실습 채점" "CI/CD 실습 확인" 요청에 쓴다.
---

# 3회차 실습 채점

평가 기준의 정본은 `grading/rubric.md`다. 이 절차는 그 표를 그대로 적용하는 방법만 정한다.

## 시작 전 확인

1. **채점 목록** — 한 줄에 한 사람: `아이디 pages=https://….pages.dev`. Repository 이름이 기본(`onboarding-todo-server` · `onboarding-todo-web`)과 다르면 `server=` · `web=`. Pages 주소가 없으면 물어본다.
2. `gh auth status` — 로그인되어 있어야 한다(Actions 실행 결과를 읽는다).
3. 채점은 이 Repository의 **`solution-advanced` Branch**에서 한다 (`git clone -b solution-advanced https://github.com/sscc-lab/onboarding-todo-server.git`). 그 폴더에서 `pip install -r requirements-dev.txt` — T1이 학생 코드에 정본 테스트를 붙여 돌리는 데 필요하다.
4. `grading/rubric.md`를 처음부터 끝까지 읽는다.
5. **T1은 학생 코드를 이 컴퓨터에서 실행한다**는 것을 채점자에게 한 줄로 알린다. 원하지 않으면 `--no-run`.

## 절차

### 1. 기록 모으기와 자동 판정

```bash
python grading/collect.py --list <임시 폴더>/people.txt --format json > <임시 폴더>/evidence.json
```

- 결과는 Repository 바깥에 둔다. Windows에서 한글이 깨지면 `PYTHONIOENCODING=utf-8`.
- Render 무료 인스턴스가 잠들어 있으면 사람마다 최대 90초를 기다린다.
- 다시 채점하려면 `--raw-out raw.json`으로 저장해 두고 `--from-json raw.json`.

### 2. AI 확인 항목 판정

`ai_check: true`인 항목(T2 Layer 규칙 · X1 장애 기록)만 `rubric.md`의 «AI 확인 항목의 기준»으로 판정한다.

- T2는 근거에 파일 내용이 없으므로, 학생의 서버 Repository에서 세 파일을 읽는다:
  `gh api repos/<server>/contents/app/routers/todo.py --jq .content | base64 -d` (services · repositories도 같다).
- **내릴 수만 있다.** «미충족»을 올리지 않는다.
- 바꿨으면 이유를 한 줄로 남기고 점수(T2는 `round(10 × 된 파일 수 / 3)`, X1은 채운 건수 기준) · 합계 · 판정을 평가표 규칙으로 다시 계산한다.

자동 판정 항목은 바꾸지 않는다. 틀려 보이면 «사람 확인»과 이유를 적는다.

### 3. 보고

맨 위에 전체 요약, 그 아래 사람마다 `collect.py`의 항목 표를 둔다.

```markdown
| 아이디 | 점수 | 판정 | 사람 확인 남음 | 보완할 점 |
|---|---|---|---|---|
| @alice | 92 | 완료 | — | 장애 기록 하나 더 |
| @bob | 48 | 보완 | C4 | 🚨 Deploy Hook 재발급 · API_BASE를 새 Render 주소로 · 최근 main 실행이 실패 — revert PR |
```

보완할 점은 학생이 **다음에 무엇을 하면 되는지**로 쓴다. AI가 바꾼 판정에는 «AI 판정: 이유»를 덧붙인다.

## 지킬 것

- 🚨 비밀 값 감점이 있으면 보고 맨 위에 따로 적는다 — Supabase 비밀번호 변경, Render Deploy Hook 재발급(Regenerate)이 채점보다 먼저다.
- GitHub · 배포한 서비스에 쓰지 않는다. Comment · Review · Issue · 재실행(Re-run)은 채점자가 정한다.
- `evidence`에 없는 사실로 점수를 올리지 않는다.
