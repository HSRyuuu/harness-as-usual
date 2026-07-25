# ④ templates/ — 템플릿 7개 리뷰

템플릿의 주석 가이드는 "사용 시점에 보이는 지시"라는 점에서 스킬 본문보다 위치
효율이 좋다. 전반 판정: **적정.** 이 층에서 줄일 것은 거의 없고, 오히려 ②층의
이중 기술(F2-3/F2-5)을 이쪽으로 몰아주는 것이 개선 방향이다.

## contexts.md (63줄) — 적정

3밴드 규칙이 core-rules §3 표 + gathering-context 본문 + 이 템플릿 주석까지
**3곳에 진술**되는 것이 유일한 흠이다(단일 소유 관례 위반). 다만 각 진술이 짧고,
템플릿 주석은 밴드별 편집 규칙이 실제로 적용되는 위치라 삭제 효용이 낮다.
권고: core-rules §3에 소유를 두고, gathering-context의 "Where Answers Go" 절에서
mutability 규칙 재설명(~10줄)을 참조로 축약. 우선순위 낮음.

- "edit the earlier entry so the section always reads as the current agreement.
  The history is not lost: audit.jsonl is append-only and keeps it." —
  `[유지 — 암묵지]`. "역사 보존 vs 현재성"의 긴장을 푸는 이 시스템 고유의 답.

## requirements.md (46줄) — 적정

섹션별 주석이 간결하고, "If a requirement cannot be checked, it is not a
requirement yet", "An assumption buried inside a requirement is an assumption
nobody will notice" 같은 문장은 밀도 높은 판단 기준이다. F2-3에 따라 스킬 쪽
표를 줄이고 이 템플릿이 섹션 정의의 단일 소유가 되는 것을 권고.

## plan.md (53줄) — 적정

- 강도 분기 주석(topic 5섹션 / direct-work 2섹션 "Do not inflate a checklist into
  a document") — `[유지]`. write-plan 표와 표현이 다른 각도라 중복감이 덜하다.
- Safety 필드의 "Naming it here does not grant permission" — `[유지 — 암묵지]`.
  계획 승인을 고위험 승인으로 오독하는 실패 모드를 정확히 막는다.
- **F3-2와의 관계**: 이 템플릿은 v2에서 올바르게 다이어트되었다. 문제는 템플릿이
  아니라 이 템플릿을 전제하지 않는 plan-quality-reference.md 쪽이다. 템플릿에
  섹션을 되돌려 넣는 방향의 개선은 하지 말 것.

## review.md (46줄) — 적정

"A clean review needs no file at all; record it as an event instead" — cleanup
4종 프롬프트의 "무발견도 파일 생성"과 미세 충돌(③층 리뷰 참조). 템플릿 쪽이
설계 의도로 보이므로 프롬프트 쪽을 확인·정리할 것.

## report.md (38줄) — 적정

"Never invent a verification result to fill a gap" — 레코드 층. 유지.

## conclusion.md (33줄) — 적정

seq 인용 요구와 "could not reproduce because … is a legitimate result, not a gap
to hide" — 레코드 층. 유지.

## MEMORY.md (26줄) — 적정

3000자 예산, "Store form == inject form", good/bad entry 예시 각 1개 — 최소량으로
정확하다. 유지.

---

## 층 종합

| 템플릿 | 판정 | 조치 |
| --- | --- | --- |
| contexts.md | 적정 | 3중 진술의 소유 정리(낮은 우선순위) |
| requirements.md | 적정 | 섹션 정의의 단일 소유처로 승격(F2-3) |
| plan.md | 적정 | 변경 금지 — ③층을 이쪽에 맞출 것 |
| review.md | 적정 | cleanup 프롬프트와 무발견 정책 정합 확인 |
| report.md / conclusion.md / MEMORY.md | 적정 | 없음 |
