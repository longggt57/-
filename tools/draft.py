"""분석 결과의 단계 목록 → n8n에 바로 import 되는 워크플로 초안."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import build  # noqa: E402  (WF 와 노드 팩토리 재사용)
from schema import Step  # noqa: E402

TRIGGERS = {"schedule_trigger", "webhook_trigger", "manual_trigger"}
X_GAP = 240


def _todo_code(step, prev_title):
    return (
        f"// TODO: {step.detail}\n"
        f"// 서비스: {step.service or '-'}\n"
        f"// 이전 단계('{prev_title}') 출력: $input.all()\n"
        "// 설정 값: $('설정').first().json\n"
        "return $input.all();\n"
    )


def _ai_request_code(step):
    return (
        f"// AI 단계: {step.detail}\n"
        "// TODO: 프롬프트와 출력 형식을 의뢰에 맞게 다듬으세요.\n"
        "const cfg = $('설정').first().json;\n"
        "const input = $input.first().json;\n"
        "return [{ json: { ...input, request: {\n"
        "  model: cfg.model,\n"
        "  max_tokens: 8000,\n"
        f"  system: {json.dumps('당신은 업무 자동화 도우미입니다. ' + step.detail, ensure_ascii=False)},\n"
        "  messages: [{ role: 'user', content: JSON.stringify(input) }],\n"
        "  output_config: { effort: 'low' },\n"
        "  fallbacks: 'default',\n"
        "} } }];\n"
    )


def build_draft(a, out_path: Path):
    wf = build.WF(f"[초안] {a.client_name} · {a.one_line}"[:120])
    steps = list(a.steps)
    if not steps or steps[0].kind not in TRIGGERS:
        steps.insert(0, Step(title="수동 실행", kind="manual_trigger", service="", detail="테스트용 수동 실행"))

    wf.sticky(
        f"## {a.one_line}\n"
        f"**고객**: {a.client_name}\n\n"
        "이 워크플로는 의뢰 분석으로 자동 생성된 **설계 초안**입니다.\n"
        "노드 아래 설명과 코드 노드의 `TODO`를 채워 완성하세요.\n\n"
        "**사람 확인 지점**: " + (", ".join(a.human_approval) or "없음"),
        (-80, -360), w=560, h=280, color=4)

    # 설정 노드: 서비스별로 채울 값 자리
    fields = [("demoMode", True)]
    kinds = {s.kind for s in steps}
    if kinds & {"google_sheets_read", "google_sheets_append"}:
        fields.append(("sheetUrl", "https://docs.google.com/spreadsheets/d/여기에_시트_ID/edit"))
    if "slack_message" in kinds:
        fields.append(("slackChannel", "#알림"))
    if "gmail_send" in kinds:
        fields.append(("emailTo", "owner@example.com"))
    if "claude_ai" in kinds:
        fields.append(("model", build.DEFAULT_MODEL))
    for i in a.integrations:
        if i.api_available != "불가" and not any(k in i.name for k in ("구글", "Google", "슬랙", "Slack", "Gmail", "지메일")):
            fields.append((f"{i.name} API 키", ""))

    used = set()

    def uniq(title):
        t, n = title.strip()[:40] or "단계", 2
        while t in used or t == "설정":
            t = f"{title.strip()[:36]} {n}"
            n += 1
        used.add(t)
        return t

    x = 0
    prev = None
    first_after_trigger = True
    for s in steps:
        name = uniq(s.title)
        pos = (x, 0)
        notes = {"notes": s.detail, "notesInFlow": True}
        if s.kind == "schedule_trigger":
            node = wf.node(name, "n8n-nodes-base.scheduleTrigger", 1.2, pos,
                           {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]}}, **notes)
        elif s.kind == "webhook_trigger":
            node = wf.node(name, "n8n-nodes-base.webhook", 2, pos,
                           {"httpMethod": "POST", "path": "intake", "responseMode": "onReceived", "options": {}}, **notes)
        elif s.kind == "manual_trigger":
            node = wf.node(name, "n8n-nodes-base.manualTrigger", 1, pos, {}, **notes)
        elif s.kind == "http_request":
            node = wf.node(name, "n8n-nodes-base.httpRequest", 4.2, pos,
                           {"method": "GET", "url": "https://api.example.com/TODO", "options": {}}, **notes)
        elif s.kind == "if_condition":
            node = build.if_node(wf, name, pos, "={{ $json.TODO }}")
            wf.nodes[-1].update(notes)
        elif s.kind == "google_sheets_read":
            node = wf.node(name, "n8n-nodes-base.googleSheets", 4.5, pos, {
                "documentId": {"__rl": True, "value": "={{ $('설정').first().json.sheetUrl }}", "mode": "url"},
                "sheetName": {"__rl": True, "value": "Sheet1", "mode": "name"}, "options": {}}, **notes)
        elif s.kind == "google_sheets_append":
            node = build.sheets_append(wf, name, pos, "Sheet1")
            wf.nodes[-1].update(notes)
        elif s.kind == "slack_message":
            node = build.slack_node(wf, name, pos, "={{ $('설정').first().json.slackChannel }}", "={{ $json.text }}")
            wf.nodes[-1].update(notes)
        elif s.kind == "gmail_send":
            node = wf.node(name, "n8n-nodes-base.gmail", 2.1, pos, {
                "sendTo": "={{ $('설정').first().json.emailTo }}", "subject": "TODO", "emailType": "text",
                "message": "={{ $json.text }}", "options": {"appendAttribution": False}}, **notes)
        elif s.kind == "claude_ai":
            req = uniq(f"{s.title} 요청")
            wf.node(req, "n8n-nodes-base.code", 2, pos, {"jsCode": _ai_request_code(s)}, **notes)
            if prev:
                wf.link(prev, req)
            prev = req
            x += X_GAP
            node = build.claude_node(wf, name, (x, 0))
        else:  # code
            node = wf.node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": _todo_code(s, prev or "-")}, **notes)

        if prev:
            wf.link(prev, node)
        prev = node
        x += X_GAP

        # 트리거 바로 뒤에 설정 노드 삽입
        if s.kind in TRIGGERS and first_after_trigger:
            first_after_trigger = False
            cfg = build.set_node(wf, "설정", (x, 0), fields)
            wf.link(prev, cfg)
            prev = cfg
            x += X_GAP

    build.OUT = out_path.parent
    wf.dump(out_path.name)
    return wf
