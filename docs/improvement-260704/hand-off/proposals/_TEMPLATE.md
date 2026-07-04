# 개선 제안: <제목>

- **작성:** Fable / <yyyy-MM-dd>
- **개선 축:** ① 단일작업 / ② 워크플로우 / ③ 아키텍처 / ④ 프롬프트 (택1)
- **규모:** Small / Medium / Large
- **상태:** 제안(승인 대기) / 승인됨 / 반려

## 1. 문제 (근거 인용)
현재 동작/규칙의 문제. 반드시 원본 파일 경로와 인용으로 뒷받침. (추측 금지)

## 2. 변경 제안
무엇을 어떻게 바꾸는가. before/after를 구체적으로.

## 3. 함께 갱신할 대상 (정합성)
core-workflow ↔ skill ↔ template ↔ reviewer prompt / manifest 이중화 / 미러 / tests 중 해당 항목.

## 4. 가드레일 점검
- [ ] 안전 게이트를 약화시키지 않는다 (`PROJECT_IDENTITY.md`)
- [ ] runtime ↔ maintainer 경계를 지킨다
- [ ] 단일 원본 원칙(체크리스트 복제 금지 등)을 지킨다
- [ ] machine-readable marker/status 값을 보존한다

## 5. 검증 계획
실행할 검증 게이트(unittest / manifest jq / hook smoke / verify-* 절차)와 예상 결과.

## 6. 롤백
변경 되돌리는 방법(파일 단위).
