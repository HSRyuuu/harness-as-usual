#!/usr/bin/env python3
"""Fill deterministic answers for the sandbox E2E priority fixture."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ANSWERS = {
    1: "A) Full stack으로 구현합니다. Backend에 priority를 영속화하고 API request/response에 포함하며 React 생성 폼과 목록 표시까지 반영합니다.",
    2: "A) 3단계 enum을 사용합니다. 값은 LOW, MEDIUM, HIGH로 고정합니다.",
    3: "A) 기본값은 MEDIUM입니다. 생성 요청에서 priority가 빠져도 backend가 MEDIUM으로 저장합니다.",
    4: "A) 생성할 때만 priority를 정하고 이후 수정 기능은 만들지 않습니다. 기존 완료 토글과 삭제 동작은 유지합니다.",
    5: "A) 정렬과 필터는 바꾸지 않고 priority badge 또는 label만 목록에 표시합니다. 검증은 backend mvn test와 frontend npm run build로 수행하고, git commit과 optional code cleanup는 실행하지 않습니다.",
}


QUESTION_PATTERN = re.compile(
    r"(## (?:💡\s*)?Question (\d+).*?(?:### (?:✍️\s*)?Answer\s*\n\n|✅ 답변을 입력하세요\.\s*\n))\[Answer\]:\s*(?=\n|---\n|## (?:💡\s*)?Question|\Z)",
    flags=re.DOTALL,
)


def fill_answers(topic: Path) -> list[Path]:
    changed: list[Path] = []
    for path in sorted(topic.glob("question-c*.md")):
        original = path.read_text(encoding="utf-8")

        def replacement(match: re.Match[str]) -> str:
            number = int(match.group(2))
            answer = ANSWERS.get(number)
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
    parser.add_argument("topic_dir")
    args = parser.parse_args()

    topic = Path(args.topic_dir)
    changed = fill_answers(topic)
    if changed:
        for path in changed:
            print(f"filled question-specific answers in {path}")
    else:
        print(f"no blank [Answer]: fields found in {topic}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
