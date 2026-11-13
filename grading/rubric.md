# 3회차 실습 평가표

3회차는 Repository 두 개(`onboarding-todo-server` · `onboarding-todo-web`)를 **한 사람 몫으로 함께** 채점합니다.
채점하는 사람도, 실습하는 사람도 같은 표를 봅니다 — 실습을 마친 뒤 스스로 점검하는 데 써도 됩니다.

근거는 네 가지입니다.

- **GitHub 기록** — Issue · Pull Request · Review · Commit · Actions 실행 결과
- **코드** — 서버의 `app/`에 `solution-advanced` Branch의 **정본 테스트**(`tests/`)를 붙여 이 컴퓨터에서 돌린다. 학생이 자기 `tests/`를 고쳐도 결과는 같다
- **배포한 서비스** — Render 서버와 Cloudflare Pages 화면에 GET · OPTIONS만 보낸다
- **장애 기록 Issue** — «[장애]»로 시작하는 Issue

## 점수 매기는 법

| 판정 | 점수 |
|---|---|
| 충족 | 배점 전부 |
| 부분 | 배점의 절반 (홀수는 올림) — T1 · T2 · F1은 통과한 비율만큼 |
| 미충족 | 0점 |
| 사람 확인 | 일단 0점. 채점자가 확인하면 바꾼다 |

| 최종 판정 | 조건 |
|---|---|
| 완료 | 70점 이상이고 «미충족» 항목이 없다 («사람 확인»은 미충족이 아니다) |
| 보완 | 그 밖의 경우 — «미충족» · «부분» 항목의 근거를 보고 그 단계만 다시 해 온다 |

## 평가 항목 — 합계 100점

### 기초 실습 (60점)

| # | 항목 | 배점 | 충족 | 부분 | 미충족 |
|---|---|---|---|---|---|
| W1 | Layer로 옮기기 PR 흐름 | 15 | Layer 파일(`routers` · `services` · `repositories`)을 고친 PR이 **세 개 이상**(README 순서대로면 ②–⑤ 네 개) 합쳐졌고, 모두 Issue 연결 · Branch `type/#번호-설명` · 제목 `[#번호] 내용` · Squash and merge · Issue 자동 닫힘 | 합친 PR이 있지만 규칙을 어겼거나 세 개보다 적다 | 합친 PR이 없다 |
| W2 | Commit 규칙 | 5 | Layer PR의 본인 Commit이 모두 `#번호 type: 내용` | 위반이 절반 이하 | 위반이 절반을 넘는다 |
| W3 | Review 받기 | 10 | 모든 Layer PR이 합치기 전에 Pair의 Approve를 받았다 | 일부만 | 없다 |
| T1 | API 동작 | 15 | 정본 테스트 16개를 모두 통과 (API 계약 11 · Service 규칙 5) | 통과한 비율만큼 | 하나도 통과하지 못했거나 앱이 뜨지 않는다 |
| T2 | Layer 규칙 | 10 | 세 파일 모두 비운 함수가 없고, 자기 층에 있으면 안 되는 것이 없다 **(AI 확인)** | 파일 비율만큼 (한 파일 약 3점) | 셋 다 어겼다 |
| F1 | 화면 api.js | 5 | `onboarding-todo-web`의 `js/api.js` 네 함수가 알맞은 Method로 `fetch`를 부른다 | 함수 비율만큼 | 넷 다 비어 있다 |

**T2에서 층마다 있으면 안 되는 것**

| 파일 | 있으면 안 되는 것 | 왜 |
|---|---|---|
| `app/routers/todo.py` | `session.add` · `session.commit` · `session.delete` · `select(` | DB 접근은 Repository의 일 |
| `app/services/todo_service.py` | `HTTPException` · `from fastapi` · `status_code` · `session.` | Service는 HTTP도 SQL도 모른다 |
| `app/repositories/todo_repository.py` | `HTTPException` · `from fastapi` · `status_code` | Repository는 HTTP를 모른다 |

### 심화 실습 (40점)

| # | 항목 | 배점 | 충족 | 부분 | 미충족 |
|---|---|---|---|---|---|
| C1 | CI 켜기 | 5 | `main`에 `.github/workflows/` 파일이 있고, PR에서 CI가 돈 기록이 있다 | 파일은 있는데 PR 실행 기록이 없다 | 파일이 없다 |
| C2 | Pipeline 배포 성공 | 10 | `main`의 가장 최근 끝난 실행이 성공이고 `deploy` Job도 성공 | 예전에 성공한 적은 있지만 최근 실행이 실패 (장애 주입 뒤 되돌리지 않음) | 성공한 적이 없다 |
| C3 | 배포된 서버가 최신 Commit | 10 | web의 `API_BASE` 주소에서 `GET /`의 `version`이 서버 `main`의 최신 Commit이고, `GET /todos`가 배열을 준다 | 서버는 뜨지만 옛 버전이거나 `dev`(CI가 만든 Image가 아님) | `API_BASE`가 아직 localhost이거나 서버가 응답하지 않는다 |
| C4 | Pages 화면 · CORS | 5 | 새 Pages 주소가 TODO 화면을 주고, 그 주소를 `Origin`으로 보내면 API가 허락한다 | 둘 중 하나만 | 둘 다 아니다 |
| X1 | 장애 기록 | 10 | «[장애]» Issue **세 개 이상**에 단계 하나 · 로그 한 줄 · 원인이 채워져 있다 **(AI 확인)** | 한두 개 | 없다 |

Pages 주소는 채점 목록에 `pages=주소`로 적어 줍니다. 없으면 web Repository의 Website 칸이나 Deployments에서 찾고, 그래도 없으면 C4는 «사람 확인»입니다.

### 감점

| 항목 | 감점 | 기준 |
|---|---|---|
| `main` 직접 Push | −10 | 두 Repository 어디든 PR 없이 `main`에 들어간 Commit (만들 때 생긴 첫 Commit은 제외) |
| 🚨 비밀 값 Commit | −10 | 모든 Branch 이력에 DB 비밀번호가 든 주소나 Render Deploy Hook 주소가 있다 — **채점보다 먼저** Supabase 비밀번호 변경 · Deploy Hook 재발급을 시킨다 |

## AI 확인 항목의 기준

자동 판정은 «있는가»만 봅니다. 아래 항목은 내용을 읽고 판정을 **내릴 수만** 있습니다.

**T2 Layer 규칙** — 세 파일을 읽는다.

- 한 파일을 «안 됨»으로 돌릴 때: 금지어는 없지만 같은 효과를 낸다(예: Router가 `TodoRepository`를 직접 부르고 Service를 건너뛴다, Service가 `{"detail": …}` 같은 HTTP 응답 모양을 만든다, 규칙(공백 · 빈 제목)이 Router에 있다).
- 이름 · 들여쓰기 · 주석은 보지 않는다.

**X1 장애 기록** — Issue 본문을 읽는다.

- 한 건을 «안 됨»으로 돌릴 때: 고른 단계와 로그가 맞지 않는다(예: «Test»를 골랐는데 로그가 Render의 DB 오류), 로그 한 줄이 원인을 말하지 않는다(«빨간색이 떴다»), 세 건이 사실상 같은 고장이다.
- 문장 다듬기는 보지 않는다.

## 채점할 때 지킬 것

- **T1은 학생 코드를 내 컴퓨터에서 실행한다.** 임시 폴더 · 임시 SQLite에서 돌고 학생 DB에는 닿지 않는다. 원하지 않으면 `--no-run`.
- **비밀 값을 옮겨 적지 않는다.** 스크립트는 `****`로 가린다.
- 채점 결과는 이 Repository에 Commit하지 않는다.
- 배포한 서비스에는 읽기 요청만 보낸다. GitHub에 Comment · Review를 남기는 것은 채점자가 정한다.
