#!/usr/bin/env python3
"""데모 모드로 세 워크플로를 실제 n8n 엔진에서 끝까지 실행해 보는 테스트.

- 트리거를 수동 실행용 노드로 바꾸고, 외부 계정이 필요한 노드(슬랙·시트·메일)는
  비활성화(입력을 그대로 통과)한 사본을 만들어 `n8n execute` 로 돌립니다.
- 각 노드의 출력과 오류를 확인해서 결과를 요약합니다.

사용법:  N8N=/path/to/n8n python3 test/run_demo_test.py
(n8n 2.x 는 Node.js 24 이상 필요)
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N8N = os.environ.get("N8N", "n8n")
EXTERNAL = {"n8n-nodes-base.slack", "n8n-nodes-base.googleSheets", "n8n-nodes-base.gmail"}
TRIGGERS = {"n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.webhook"}

SAMPLE_INQUIRIES = {
    "complaint": {"name": "최고객", "channel": "스마트스토어 Q&A", "orderNo": "2026110410000002",
                  "message": "감귤 받았는데 절반이 곰팡이 피고 파손돼 있어요. 환불해 주세요. 정말 화가 나네요."},
    "shipping": {"name": "정고객", "channel": "홈페이지", "message": "어제 주문했는데 배송 언제 출발하나요?"},
}


def make_test_copy(wf, idx, inquiry=None):
    wf = copy.deepcopy(wf)
    wf["id"] = f"kmongdemo{idx:07d}"  # 16자 영숫자
    wf["active"] = False
    for n in wf["nodes"]:
        if n["type"] in EXTERNAL:
            n["disabled"] = True
        elif n["type"] in TRIGGERS:
            if n["type"] == "n8n-nodes-base.webhook":
                # 웹훅 출력과 같은 형태 { body: {...} } 를 내는 코드 노드로 교체 (이름 유지)
                n["type"] = "n8n-nodes-base.code"
                n["typeVersion"] = 2
                n["parameters"] = {"jsCode": "return [{ json: { headers: {}, query: {}, body: %s } }];"
                                   % json.dumps(inquiry, ensure_ascii=False)}
                n.pop("webhookId", None)
                manual = {"id": "manual-start", "name": "테스트 시작", "type": "n8n-nodes-base.manualTrigger",
                          "typeVersion": 1, "position": [-200, 0], "parameters": {}}
                wf["nodes"].append(manual)
                wf["connections"]["테스트 시작"] = {"main": [[{"node": n["name"], "type": "main", "index": 0}]]}
            else:
                n["type"] = "n8n-nodes-base.manualTrigger"
                n["typeVersion"] = 1
                n["parameters"] = {}
    return wf


def run(wf):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False)
        path = f.name
    imp = subprocess.run([N8N, "import:workflow", f"--input={path}"], capture_output=True, text=True)
    if imp.returncode != 0:
        return None, "import 실패:\n" + imp.stdout + imp.stderr
    ex = subprocess.run([N8N, "execute", f"--id={wf['id']}", "--rawOutput"], capture_output=True, text=True, timeout=300)
    out = ex.stdout
    start = out.find("{")
    if start < 0:
        return None, "실행 결과 없음:\n" + out[-3000:] + ex.stderr[-3000:]
    try:
        return json.loads(out[start:]), None
    except json.JSONDecodeError:
        return None, "결과 JSON 파싱 실패:\n" + out[-3000:]


def summarize(result):
    run_data = result.get("data", {}).get("resultData", {}).get("runData", {})
    err = result.get("data", {}).get("resultData", {}).get("error")
    nodes = {}
    for name, runs in run_data.items():
        r = runs[-1]
        items = (r.get("data", {}).get("main") or [[]])
        count = sum(len(b or []) for b in items)
        nodes[name] = {"items": count, "error": (r.get("error") or {}).get("message")}
    return nodes, (err or {}).get("message")


def last_json(result, node):
    runs = result["data"]["resultData"]["runData"].get(node)
    if not runs:
        return None
    for branch in runs[-1]["data"]["main"]:
        if branch:
            return [i["json"] for i in branch]
    return None


def main():
    files = sorted((ROOT / "workflows").glob("*.json"))
    cases = []
    for i, f in enumerate(files, 1):
        wf = json.loads(f.read_text(encoding="utf-8"))
        if any(n["type"] == "n8n-nodes-base.webhook" for n in wf["nodes"]):
            for k, inq in SAMPLE_INQUIRIES.items():
                cases.append((f"{f.stem} [{k}]", make_test_copy(wf, i * 10 + len(cases), inq)))
        else:
            cases.append((f.stem, make_test_copy(wf, i)))

    failed = 0
    report = {}
    for label, wf in cases:
        print(f"\n=== {label} ===")
        result, err = run(wf)
        if err:
            print("  ✗", err)
            failed += 1
            continue
        nodes, top_err = summarize(result)
        for name, info in nodes.items():
            mark = "✗" if info["error"] else "✓"
            print(f"  {mark} {name}: {info['items']}개 항목" + (f"  ← {info['error']}" if info["error"] else ""))
        if top_err or any(v["error"] for v in nodes.values()):
            failed += 1
        report[label] = result
    out = ROOT / "test" / "last_run.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{'모두 통과' if not failed else f'{failed}건 실패'} · 상세 결과: {out.relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
