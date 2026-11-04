#!/usr/bin/env python3
"""의뢰 처리 도구 단위 테스트 (API 호출 없음): 가격 판정, 거절 처리, n8n 초안 생성."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from draft import build_draft  # noqa: E402
from pricing import make_quote  # noqa: E402
from schema import ProjectAnalysis  # noqa: E402

base = json.loads((ROOT / "tools/fixtures/demo_analysis.json").read_text(encoding="utf-8"))


def variant(**kw):
    d = json.loads(json.dumps(base))
    d.update(kw)
    return ProjectAnalysis.model_validate(d)


def check(name, cond):
    print(("  ✓ " if cond else "  ✗ ") + name)
    return cond


ok = True
# 1) 서비스 5개 → PREMIUM
ok &= check("서비스 5개는 PREMIUM", make_quote(variant()).package == "PREMIUM")
# 2) 단순·2개 서비스·AI 없음 → STANDARD
simple = variant(complexity="단순",
                 integrations=[{"name": "구글시트", "api_available": "가능", "note": ""}],
                 steps=[{"title": "매일 실행", "kind": "schedule_trigger", "service": "", "detail": "x"},
                        {"title": "시트 읽기", "kind": "google_sheets_read", "service": "구글시트", "detail": "x"},
                        {"title": "메일", "kind": "gmail_send", "service": "Gmail", "detail": "x"}])
ok &= check("단순 3단계는 STANDARD 99,000원", make_quote(simple).package == "STANDARD" and make_quote(simple).total == 99_000)
# 3) AI 포함이면 STANDARD 불가
ai = variant(complexity="단순", integrations=[], steps=simple.model_dump()["steps"] + [
    {"title": "AI 요약", "kind": "claude_ai", "service": "", "detail": "x"}])
ok &= check("AI 단계가 있으면 최소 DELUXE", make_quote(ai).package == "DELUXE")
# 4) 절감·회수 계산
q = make_quote(variant())
ok &= check("절감 26시간 → 312,000원, 회수 2.5개월", (q.hours_saved_month, q.savings_month, q.payback_months) == (26.0, 312000, 2.5))

# 5) 초안: 트리거 없으면 수동 트리거 추가, 설정 노드 포함, 이름 중복 없음, 연결 유효
with tempfile.TemporaryDirectory() as t:
    a = variant(steps=[{"title": "정리", "kind": "code", "service": "", "detail": "x"},
                       {"title": "정리", "kind": "code", "service": "", "detail": "y"},
                       {"title": "AI 분류", "kind": "claude_ai", "service": "", "detail": "z"}])
    p = Path(t) / "d.json"
    build_draft(a, p)
    wf = json.loads(p.read_text(encoding="utf-8"))
    names = [n["name"] for n in wf["nodes"]]
    ok &= check("트리거 자동 추가", wf["nodes"][1]["type"] == "n8n-nodes-base.manualTrigger")
    ok &= check("설정 노드 포함", "설정" in names)
    ok &= check("노드 이름 중복 없음", len(names) == len(set(names)))
    ok &= check("연결 대상이 모두 존재", all(c["node"] in names for v in wf["connections"].values()
                                         for outs in v["main"] for c in outs))
    ok &= check("AI 단계는 요청 구성 + Claude 호출 2개 노드", "AI 분류 요청" in names and "AI 분류" in names)

# 6) 거절 대상이면 견적서·초안을 만들지 않음 (CLI 전체 실행)
with tempfile.TemporaryDirectory() as t:
    fx = Path(t) / "fixtures"
    fx.mkdir()
    d = json.loads(json.dumps(base))
    d.update(refuse=True, refuse_reason="티켓 예매 매크로", client_name="거절테스트")
    (fx / "demo_analysis.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    # fixture 경로를 바꿔 실행하기 위해 tools 폴더를 임시 복사
    import shutil
    tools = Path(t) / "tools"
    shutil.copytree(ROOT / "tools", tools)
    shutil.copy(fx / "demo_analysis.json", tools / "fixtures" / "demo_analysis.json")
    (Path(t) / "src").symlink_to(ROOT / "src")
    (Path(t) / "samples").symlink_to(ROOT / "samples")
    r = subprocess.run([sys.executable, str(tools / "intake.py"), "--demo", "--out", t], capture_output=True, text=True)
    out = next(Path(t).glob("*_거절테스트"), None)
    files = {f.name for f in out.iterdir()} if out else set()
    ok &= check("거절 시 답장만 생성, 견적서·초안 없음",
                r.returncode == 0 and "04_크몽_답장.txt" in files and "02_견적서.md" not in files and "05_n8n_초안.json" not in files)

print("\n모두 통과" if ok else "\n실패 있음")
sys.exit(0 if ok else 1)
