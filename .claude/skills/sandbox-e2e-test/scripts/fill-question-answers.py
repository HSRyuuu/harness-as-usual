#!/usr/bin/env python3
"""Fill deterministic answers for sandbox E2E scenario fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


SCENARIO_ANSWERS = {
    "scenario_1_priority": {
        1: "A) Full stack으로 구현합니다. Backend에 priority를 영속화하고 API request/response에 포함하며 React 생성 폼과 목록 표시까지 반영합니다.",
        2: "A) 3단계 enum을 사용합니다. 값은 LOW, MEDIUM, HIGH로 고정합니다.",
        3: "A) 기본값은 MEDIUM입니다. 생성 요청에서 priority가 빠져도 backend가 MEDIUM으로 저장합니다.",
        4: "A) 생성할 때만 priority를 정하고 이후 수정 기능은 만들지 않습니다. 기존 완료 토글과 삭제 동작은 유지합니다.",
        5: "A) 정렬과 필터는 바꾸지 않고 priority badge 또는 label만 목록에 표시합니다. 검증은 backend mvn test와 frontend npm run build로 수행하고, git commit과 optional code cleanup는 실행하지 않습니다.",
    },
    "scenario_2_complex_workflow": {
        1: "A) Full stack으로 구현합니다. Backend에 dueDate, reminderEnabled, status/overdue 계산을 반영하고 React 생성 폼과 목록 표시까지 변경합니다.",
        2: "A) dueDate는 선택값이고 reminderEnabled는 기본 false입니다. status는 기존 완료 여부와 호환되도록 TODO, DONE, OVERDUE 표시 규칙으로 계획합니다.",
        3: "A) overdue는 서버 기준 오늘 날짜보다 dueDate가 과거이고 완료되지 않은 task에만 표시합니다. dueDate가 없으면 overdue가 아닙니다.",
        4: "A) 생성 시 dueDate/reminder를 입력할 수 있게 하고, 기존 완료 토글과 삭제 동작은 유지합니다. 별도 수정 화면은 만들지 않습니다.",
        5: "A) backend mvn test와 frontend npm run build를 모두 수행합니다. 복합 변경이므로 task-level TDD evidence와 review evidence를 audit에 남기고 git commit과 optional code cleanup은 실행하지 않습니다.",
    },
    "scenario_3_self_improvement": {
        1: "A) Full stack으로 구현합니다. Backend/API/frontend에 task note 또는 source label을 추가하되 변경 폭은 작게 유지합니다.",
        2: "A) note/source label은 선택값입니다. 누락되면 빈 값 또는 null을 허용하고 기존 task 생성/목록 동작은 깨지지 않아야 합니다.",
        3: "A) 자기개선 검증을 포함합니다. 장기 규칙은 '이 sandbox project의 E2E report에는 앞으로 항상 scenario id와 scenario 목적을 남긴다'입니다.",
        4: "A) 이 장기 규칙은 구현 중 memory.candidate로만 기록하고, finalize self-improvement pass에서 사용자 승인 후 MEMORY.md에 반영합니다.",
        5: "A) backend mvn test와 frontend npm run build를 모두 수행합니다. git commit과 optional code cleanup은 실행하지 않고, finalize 후 git action decision requested 상태에서 멈춥니다.",
    },
}


QUESTION_PATTERN = re.compile(
    r"(## (?:💡\s*)?Question (\d+).*?(?:### (?:✍️\s*)?Answer\s*\n\n|✅ 답변을 입력하세요\.\s*\n))\[Answer\]:\s*(?=\n|---\n|## (?:💡\s*)?Question|\Z)",
    flags=re.DOTALL,
)


def normalize_scenario(value: str) -> str:
    aliases = {
        "1": "scenario_1_priority",
        "scenario_1": "scenario_1_priority",
        "scenario_1_priority": "scenario_1_priority",
        "2": "scenario_2_complex_workflow",
        "scenario_2": "scenario_2_complex_workflow",
        "scenario_2_complex": "scenario_2_complex_workflow",
        "scenario_2_complex_workflow": "scenario_2_complex_workflow",
        "3": "scenario_3_self_improvement",
        "scenario_3": "scenario_3_self_improvement",
        "scenario_3_self_improvement": "scenario_3_self_improvement",
    }
    try:
        return aliases[value]
    except KeyError as exc:
        raise ValueError(f"unsupported scenario: {value}") from exc


def fill_answers(topic: Path, scenario: str = "scenario_1_priority") -> list[Path]:
    answers = SCENARIO_ANSWERS[normalize_scenario(scenario)]
    changed: list[Path] = []
    for path in sorted(topic.glob("question-c*.md")):
        original = path.read_text(encoding="utf-8")

        def replacement(match: re.Match[str]) -> str:
            number = int(match.group(2))
            answer = answers.get(number)
            if answer is None:
                return match.group(0)
            return f"{match.group(1)}[Answer]: {answer}"

        updated = QUESTION_PATTERN.sub(replacement, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill sandbox E2E question answers.")
    parser.add_argument("--scenario", default="scenario_1_priority")
    parser.add_argument("topic_dir")
    args = parser.parse_args()

    topic = Path(args.topic_dir)
    try:
        changed = fill_answers(topic, args.scenario)
    except ValueError as exc:
        parser.error(str(exc))
    if changed:
        for path in changed:
            print(f"filled question-specific answers in {path}")
    else:
        print(f"no blank [Answer]: fields found in {topic}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
