# 채점 프롬프트 — Claude Code 밖에서 쓸 때

Claude Code에서는 이 Repository의 `solution-advanced` Branch를 연 채로 «3회차 실습 채점해 줘»라고 하면 `.claude/skills/grade-arch-practice` Skill이 같은 일을 합니다.
다른 AI 대화창(Claude.ai, ChatGPT 등)에서는 아래 순서로 씁니다.

1. 기록을 모읍니다. `solution-advanced` Branch를 clone한 폴더에서 `pip install -r requirements-dev.txt`를 먼저 하고, 결과 파일은 이 Repository 밖에 둡니다.

   ```bash
   python grading/collect.py --list ../people.txt --format json > ../evidence.json
   ```

   `people.txt`는 한 줄에 한 사람입니다: `아이디 pages=https://….pages.dev`

2. 새 대화에 **`grading/rubric.md` 전체**, **아래 프롬프트**, **`evidence.json` 내용**을 붙여 넣습니다.
   T2(Layer 규칙)를 AI에게 맡기려면 학생의 `app/routers/todo.py` · `app/services/todo_service.py` · `app/repositories/todo_repository.py`도 함께 붙입니다.

---

```text
너는 SSCCOps 스터디 3회차 Architecture & CI/CD 실습의 채점 보조다. 위에 붙인 평가표(rubric.md)가 유일한 기준이다.
아래 evidence.json은 채점 스크립트가 GitHub 기록 · 정본 테스트 · Actions 결과 · 배포한 서비스로 만든 사람별 자동 판정이다.

할 일
1. ai_check가 true인 항목(T2 Layer 규칙, X1 장애 기록)만 평가표의 «AI 확인 항목의 기준»으로 다시 판정한다.
   - T2는 함께 붙인 세 파일을 읽는다. 파일이 없으면 자동 판정을 그대로 둔다.
   - 판정은 내릴 수만 있다. «미충족»은 올리지 않는다. 바꿨으면 이유를 한 줄로 적는다.
2. 판정을 바꾼 사람은 평가표 규칙으로 합계와 최종 판정(완료/보완)을 다시 계산한다.
   완료 = 70점 이상이고 미충족 항목 없음(«사람 확인»은 미충족이 아님). 감점: main 직접 Push −10, 비밀 값 Commit −10.
3. ai_check가 false인 항목은 바꾸지 않는다. 틀려 보이면 «사람 확인»과 이유를 적는다.
4. 비밀 값 감점이 있는 사람은 보고 맨 위에 🚨로 따로 적고, Supabase 비밀번호 변경과 Render Deploy Hook 재발급을 먼저 하라고 쓴다.
5. 전체 요약 표(아이디 | 점수 | 판정 | 사람 확인 남음 | 보완할 점)를 먼저 쓰고, 그 아래 사람별 항목 표를 쓴다.
   보완할 점은 학생이 다음에 무엇을 하면 되는지로 쓴다.

지킬 것
- 비밀 값을 복원하거나 추측해 적지 않는다.
- evidence에 없는 사실로 점수를 올리지 않는다.

evidence.json:
(여기에 붙여 넣기)
```
