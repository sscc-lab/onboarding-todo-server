---
name: 장애 기록
about: 배포가 멈췄을 때 — 어디서, 무엇 때문에 멈췄고 어떻게 풀었는지 남깁니다.
title: "[장애] "
labels: []
assignees: []
---

## 무엇이 안 됐나

<!-- 눈에 보인 증상. 예: Actions가 빨갛다, 화면에 Failed to fetch, Render가 Deploy failed -->

## 어느 단계에서 멈췄나

<!-- 하나를 고르고 나머지는 지웁니다 -->
- Commit → **CI(Test)** → Build → Registry → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → **Build** → Registry → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → Build → **Registry** → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → Build → Registry → **Deploy Hook** → Container → Application → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → **Container** → Application → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → Container → **Application** → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → Container → Application → **Database**

## 로그에서 찾은 한 줄

```text
여기에 원인을 말해 주는 로그 한 줄을 붙입니다 (비밀번호 · 토큰은 지웁니다)
```

로그를 본 곳: <!-- Actions의 어느 Job · Step / Render Events · Logs / 브라우저 Console · Network -->

## 원인

## 어떻게 풀었나

<!-- 고친 PR 번호(#번호)나 바꾼 설정 -->
