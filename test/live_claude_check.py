#!/usr/bin/env python3
"""워크플로 ②가 실제로 만드는 Claude 요청을 그대로 API에 보내 보는 점검 스크립트.

run_demo_test.py 실행 결과(test/last_run.json)에서 '문의 정리 + AI 요청 구성' 노드가 만든
요청 본문을 꺼내 Claude API에 보내고, 응답이 스키마대로 오는지 확인합니다.

사용법:
  python3 test/run_demo_test.py           # 먼저 1회 실행
  ANTHROPIC_API_KEY=sk-ant-... python3 test/live_claude_check.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
key = os.environ.get("ANTHROPIC_API_KEY")
if not key:
    sys.exit("ANTHROPIC_API_KEY 환경변수를 설정하세요.")

runs = json.loads((ROOT / "test" / "last_run.json").read_text(encoding="utf-8"))
REQUIRED = {"category", "urgency", "sentiment", "summary", "needs_human", "human_reason", "draft_reply"}
failed = 0

for label, result in runs.items():
    node = result["data"]["resultData"]["runData"].get("문의 정리 + AI 요청 구성")
    if not node:
        continue
    payload = node[-1]["data"]["main"][0][0]["json"]
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload["request"]).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2026-10-21",
            "anthropic-beta": "server-side-fallback-2026-07-01",
        },
    )
    print(f"\n=== {label} ===")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            res = json.load(r)
    except urllib.error.HTTPError as e:
        print("  ✗ HTTP", e.code, e.read().decode()[:800])
        failed += 1
        continue
    print("  stop_reason:", res.get("stop_reason"), "· model:", res.get("model"), "· usage:", res.get("usage"))
    text = "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text")
    try:
        ai = json.loads(text)
        missing = REQUIRED - ai.keys()
        if missing:
            raise ValueError(f"누락 필드: {missing}")
        print(f"  ✓ 분류={ai['category']} 긴급도={ai['urgency']} 사람확인={ai['needs_human']}")
        print("  초안:", ai["draft_reply"])
    except Exception as e:  # noqa: BLE001
        print("  ✗ 응답 형식 오류:", e, text[:500])
        failed += 1

sys.exit(1 if failed else 0)
