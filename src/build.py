#!/usr/bin/env python3
"""src/code/*.js 를 n8n 워크플로 JSON(workflows/*.json)으로 조립합니다.

사용법:  python3 src/build.py
코드 노드 내용은 src/code 에서 수정하고, 이 스크립트로 다시 빌드하세요.
"""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "src" / "code"
OUT = ROOT / "workflows"
VENDOR = ROOT / "src" / "vendor"

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2026-10-21"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
DEFAULT_MODEL = "claude-opus-5-5"
NAVER = "https://api.commerce.naver.com/external"


def code(name: str) -> str:
    src = (CODE / name).read_text(encoding="utf-8")
    if "/*__BCRYPT_BUNDLE__*/" in src:
        src = src.replace("/*__BCRYPT_BUNDLE__*/", (VENDOR / "bcrypt_bundle.js").read_text(encoding="utf-8"))
    return src


class WF:
    def __init__(self, name: str):
        self.name = name
        self.nodes = []
        self.conn = {}

    def node(self, name, type_, version, pos, params, **extra):
        n = {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.name}/{name}")),
            "name": name,
            "type": type_,
            "typeVersion": version,
            "position": list(pos),
            "parameters": params,
        }
        n.update(extra)
        self.nodes.append(n)
        return name

    def link(self, src, dst, out=0):
        outs = self.conn.setdefault(src, {"main": []})["main"]
        while len(outs) <= out:
            outs.append([])
        outs[out].append({"node": dst, "type": "main", "index": 0})

    def chain(self, *names):
        for a, b in zip(names, names[1:]):
            self.link(a, b)

    def sticky(self, text, pos, w=420, h=260, color=None):
        p = {"content": text, "width": w, "height": h}
        if color:
            p["color"] = color
        return self.node(f"메모 {len(self.nodes)}", "n8n-nodes-base.stickyNote", 1, pos, p)

    def dump(self, filename, settings=None):
        wf = {
            "name": self.name,
            "nodes": self.nodes,
            "connections": self.conn,
            "settings": {"executionOrder": "v1", "timezone": "Asia/Seoul", **(settings or {})},
            "pinData": {},
            "meta": {"templateCredsSetupCompleted": False},
            "tags": [],
        }
        OUT.mkdir(exist_ok=True)
        (OUT / filename).write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ {OUT.name}/{filename}  ({len(self.nodes)} nodes)")


# ---------- 공통 노드 팩토리 ----------

def set_node(wf, name, pos, fields):
    """설정 노드: (이름, 값) 목록 → Set(v3.4) assignments"""
    assigns = []
    for k, v in fields:
        t = "boolean" if isinstance(v, bool) else "number" if isinstance(v, (int, float)) else "string"
        assigns.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{wf.name}/{name}/{k}")), "name": k, "value": v, "type": t})
    return wf.node(name, "n8n-nodes-base.set", 3.4, pos, {"assignments": {"assignments": assigns}, "options": {}})


def code_node(wf, name, pos, file, mode=None):
    p = {"jsCode": code(file)}
    if mode:
        p["mode"] = mode
    return wf.node(name, "n8n-nodes-base.code", 2, pos, p)


def if_node(wf, name, pos, left, op="true", right=None, combinator="and", extra=None):
    """IF(v2.2). 기본은 boolean true 검사."""
    def cond(l, o, r):
        c = {"id": str(uuid.uuid4()), "leftValue": l}
        if o == "true":
            c["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
            c["rightValue"] = ""
        elif o == "equals":
            c["operator"] = {"type": "string", "operation": "equals"}
            c["rightValue"] = r
        return c

    conds = [cond(left, op, right)] + [cond(*e) for e in (extra or [])]
    return wf.node(name, "n8n-nodes-base.if", 2.2, pos, {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": conds,
            "combinator": combinator,
        },
        "looseTypeValidation": True,
        "options": {},
    })


def claude_node(wf, name, pos):
    """Claude Messages API 호출 (HTTP Request v4.2, Header Auth 자격증명: x-api-key)"""
    return wf.node(name, "n8n-nodes-base.httpRequest", 4.2, pos, {
        "method": "POST",
        "url": ANTHROPIC_URL,
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "anthropic-version", "value": ANTHROPIC_VERSION},
            {"name": "anthropic-beta", "value": FALLBACK_BETA},
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.request) }}",
        "options": {"timeout": 120000},
    },
       retryOnFail=True, maxTries=3, waitBetweenTries=5000)


def slack_node(wf, name, pos, channel_expr, text_expr):
    return wf.node(name, "n8n-nodes-base.slack", 2.3, pos, {
        "select": "channel",
        "channelId": {"__rl": True, "value": channel_expr, "mode": "name"},
        "text": text_expr,
        "otherOptions": {"includeLinkToWorkflow": False},
    })


def sheets_append(wf, name, pos, sheet_name):
    return wf.node(name, "n8n-nodes-base.googleSheets", 4.5, pos, {
        "operation": "append",
        "documentId": {"__rl": True, "value": "={{ $('설정').first().json.sheetUrl }}", "mode": "url"},
        "sheetName": {"__rl": True, "value": sheet_name, "mode": "name"},
        "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []},
        "options": {},
    })


# ---------- ① 스마트스토어 신규 주문 → 구글시트 → 슬랙 ----------

def build_w1():
    wf = WF("① 스마트스토어 신규주문 → 구글시트 기록 → 슬랙 알림")
    wf.sticky(
        "## ① 신규 주문 자동 기록\n"
        "10분마다 네이버 스마트스토어의 **결제완료 주문**을 가져와\n"
        "구글시트 `주문` 탭에 한 줄씩 기록하고, 슬랙으로 요약을 보냅니다.\n\n"
        "**처음 설정할 것**\n"
        "1. `설정` 노드: demoMode=false, API 키, 시트 URL, 슬랙 채널\n"
        "2. Google Sheets / Slack 자격증명 연결\n"
        "3. 시트 1행에 열 이름 입력 (README 참고)\n\n"
        "demoMode=true 이면 샘플 주문 3건으로 전체 흐름을 시연합니다.",
        (-80, -340), w=520, h=300, color=4)

    t = wf.node("10분마다", "n8n-nodes-base.scheduleTrigger", 1.2, (0, 0),
                {"rule": {"interval": [{"field": "minutes", "minutesInterval": 10}]}})
    cfg = set_node(wf, "설정", (220, 0), [
        ("demoMode", True),
        ("naverClientId", ""),
        ("naverClientSecret", ""),
        ("lookbackMinutes", 15),
        ("sheetUrl", "https://docs.google.com/spreadsheets/d/여기에_시트_ID/edit"),
        ("slackChannel", "#주문알림"),
    ])
    demo = if_node(wf, "데모 모드?", (440, 0), "={{ $json.demoMode }}")
    sample = code_node(wf, "샘플 주문 (데모)", (700, -160), "w1_sample_orders.js")
    sign = code_node(wf, "네이버 API 서명 생성", (700, 120), "w1_naver_sign.js")
    token = wf.node("토큰 발급", "n8n-nodes-base.httpRequest", 4.2, (920, 120), {
        "method": "POST",
        "url": f"{NAVER}/v1/oauth2/token",
        "sendBody": True,
        "contentType": "form-urlencoded",
        "bodyParameters": {"parameters": [
            {"name": k, "value": f"={{{{ $json.{k} }}}}"}
            for k in ("client_id", "timestamp", "client_secret_sign", "grant_type", "type")
        ]},
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    changed = wf.node("변경 주문 조회", "n8n-nodes-base.httpRequest", 4.2, (1140, 120), {
        "method": "GET",
        "url": f"{NAVER}/v1/pay-order/seller/product-orders/last-changed-statuses",
        "sendQuery": True,
        "queryParameters": {"parameters": [
            {"name": "lastChangedFrom", "value": "={{ $('네이버 API 서명 생성').first().json.lastChangedFrom }}"},
            {"name": "lastChangedType", "value": "PAYED"},
        ]},
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "=Bearer {{ $json.access_token }}"},
        ]},
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    ids = code_node(wf, "상품주문번호 추출", (1360, 120), "w1_extract_ids.js")
    detail = wf.node("주문 상세 조회", "n8n-nodes-base.httpRequest", 4.2, (1580, 120), {
        "method": "POST",
        "url": f"{NAVER}/v1/pay-order/seller/product-orders/query",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "=Bearer {{ $('토큰 발급').first().json.access_token }}"},
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ productOrderIds: $json.productOrderIds }) }}",
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    norm = code_node(wf, "주문 정리 + 중복 제외", (1820, 0), "w1_normalize.js")
    sheet = sheets_append(wf, "구글시트에 기록", (2060, -120), "주문")
    msg = code_node(wf, "슬랙 메시지 작성", (2060, 120), "w1_slack_message.js")
    slack = slack_node(wf, "슬랙 알림", (2280, 120),
                       "={{ $('설정').first().json.slackChannel }}", "={{ $json.text }}")

    wf.chain(t, cfg, demo)
    wf.link(demo, sample, 0)
    wf.link(demo, sign, 1)
    wf.chain(sign, token, changed, ids, detail, norm)
    wf.link(sample, norm)
    wf.link(norm, sheet)
    wf.link(norm, msg)
    wf.link(msg, slack)
    wf.dump("01_스마트스토어_주문_시트_슬랙.json")
    return wf


# ---------- ② 고객 문의 AI 분류 + 답변 초안 ----------

POLICIES = """- 배송: 평일 오후 2시 이전 결제 시 당일 출고, CJ대한통운, 출고 후 보통 1~2일 소요. 주말·공휴일 출고 없음.
- 배송비: 3만 원 이상 무료, 미만 3,000원. 제주·도서산간 3,000원 추가.
- 교환/반품: 수령 후 7일 이내. 단순 변심은 왕복 배송비 6,000원 고객 부담. 상품 하자·오배송은 무료.
- 신선식품(감귤 등)은 단순 변심 반품 불가, 상태 불량 시 사진 확인 후 재발송 또는 환불.
- 영수증: 마이페이지에서 현금영수증·카드전표 출력 가능. 세금계산서는 사업자등록증 보내주시면 발행.
- 고객센터: 평일 10:00~17:00 (점심 12:00~13:00)"""


def build_w2():
    wf = WF("② 고객 문의 AI 분류 + 답변 초안 → 슬랙 승인")
    wf.sticky(
        "## ② 고객 문의 AI 답변 초안\n"
        "홈페이지 문의폼·챗봇 등에서 웹훅으로 문의를 받으면\n"
        "Claude가 **분류 · 긴급도 · 답변 초안**을 만들어 슬랙으로 보냅니다.\n"
        "AI는 고객에게 직접 보내지 않습니다. 담당자가 확인 후 발송합니다.\n\n"
        "불만·환불·파손 문의 또는 AI 처리 실패 → 🚨 '사람 확인 필요'로 분리\n"
        "모든 문의는 구글시트 `문의` 탭에 기록됩니다.\n\n"
        "`설정` 노드에서 가게 이름·정책·말투를 바꾸면 답변이 그에 맞춰집니다.",
        (-80, -360), w=560, h=320, color=4)

    hook = wf.node("문의 수신 (웹훅)", "n8n-nodes-base.webhook", 2, (0, 0), {
        "httpMethod": "POST",
        "path": "cs-inquiry",
        "responseMode": "onReceived",
        "responseData": "firstEntryJson",
        "options": {"responseData": ""},
    }, webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, "w2-webhook")))
    cfg = set_node(wf, "설정", (220, 0), [
        ("demoMode", True),
        ("shopName", "곡물상회"),
        ("tone", "정중하고 따뜻한 존댓말, 과한 사과나 이모지는 쓰지 않음"),
        ("policies", POLICIES),
        ("model", DEFAULT_MODEL),
        ("sheetUrl", "https://docs.google.com/spreadsheets/d/여기에_시트_ID/edit"),
        ("slackChannel", "#고객문의"),
    ])
    build = code_node(wf, "문의 정리 + AI 요청 구성", (440, 0), "w2_build_request.js")
    demo = if_node(wf, "데모 모드?", (660, 0), "={{ $('설정').first().json.demoMode }}")
    fake = code_node(wf, "AI 응답 (데모)", (900, -140), "w2_demo_ai.js")
    ai = claude_node(wf, "Claude 분류 + 답변 작성", (900, 140))
    parse = code_node(wf, "AI 결과 해석", (1140, 0), "w2_parse_ai.js")
    msg = code_node(wf, "슬랙 메시지 작성", (1380, -100), "w2_slack_message.js")
    urgent = if_node(wf, "사람 확인 필요?", (1600, -100), "={{ $json.urgent }}")
    s_urg = slack_node(wf, "슬랙: 긴급", (1840, -220),
                       "={{ $('설정').first().json.slackChannel }}", "=<!channel> {{ $json.slackText }}")
    s_norm = slack_node(wf, "슬랙: 일반", (1840, 20),
                        "={{ $('설정').first().json.slackChannel }}", "={{ $json.slackText }}")
    row = code_node(wf, "시트 행 만들기", (1380, 160), "w2_sheet_row.js")
    sheet = sheets_append(wf, "구글시트에 기록", (1600, 160), "문의")

    wf.chain(hook, cfg, build, demo)
    wf.link(demo, fake, 0)
    wf.link(demo, ai, 1)
    wf.link(fake, parse)
    wf.link(ai, parse)
    wf.chain(parse, msg, urgent)
    wf.link(urgent, s_urg, 0)
    wf.link(urgent, s_norm, 1)
    wf.chain(parse, row, sheet)
    wf.dump("02_고객문의_AI_답변초안.json")
    return wf


# ---------- ③ 매일 아침 매출 리포트 ----------

def build_w3():
    wf = WF("③ 매일 아침 매출 리포트 (슬랙 + 메일)")
    wf.sticky(
        "## ③ 일일 매출 리포트\n"
        "매일 오전 8:30, 구글시트 `주문` 탭(워크플로 ①이 기록)을 읽어\n"
        "어제 매출 · 주문수 · 객단가 · 지난주 같은 요일 대비 · TOP5 상품을\n"
        "슬랙과 이메일로 보냅니다. Claude가 2~3문장 코멘트를 붙입니다.\n\n"
        "useAI=false 이거나 데모 모드이면 규칙 기반 코멘트를 씁니다.",
        (-80, -320), w=540, h=260, color=4)

    t = wf.node("매일 08:30", "n8n-nodes-base.scheduleTrigger", 1.2, (0, 0),
                {"rule": {"interval": [{"field": "cronExpression", "expression": "30 8 * * *"}]}})
    cfg = set_node(wf, "설정", (220, 0), [
        ("demoMode", True),
        ("shopName", "곡물상회"),
        ("useAI", True),
        ("model", DEFAULT_MODEL),
        ("sheetUrl", "https://docs.google.com/spreadsheets/d/여기에_시트_ID/edit"),
        ("slackChannel", "#매출리포트"),
        ("emailTo", "owner@example.com"),
    ])
    demo = if_node(wf, "데모 모드?", (440, 0), "={{ $json.demoMode }}")
    sample = code_node(wf, "샘플 주문 35일치 (데모)", (680, -140), "w3_sample_rows.js")
    read = wf.node("주문 시트 읽기", "n8n-nodes-base.googleSheets", 4.5, (680, 140), {
        "documentId": {"__rl": True, "value": "={{ $('설정').first().json.sheetUrl }}", "mode": "url"},
        "sheetName": {"__rl": True, "value": "주문", "mode": "name"},
        "options": {},
    }, alwaysOutputData=True)
    agg = code_node(wf, "어제 매출 집계", (920, 0), "w3_aggregate.js")
    use_ai = if_node(wf, "AI 코멘트 사용?", (1140, 0), "={{ $('설정').first().json.useAI }}",
                     extra=[("={{ !$('설정').first().json.demoMode }}", "true", None)])
    req = code_node(wf, "AI 요청 구성", (1360, -140), "w3_build_request.js")
    ai = claude_node(wf, "Claude 코멘트 작성", (1580, -140))
    ext = code_node(wf, "코멘트 추출", (1800, -140), "w3_extract_comment.js")
    rep = code_node(wf, "리포트 작성", (2020, 0), "w3_report.js")
    slack = slack_node(wf, "슬랙 발송", (2260, -100),
                       "={{ $('설정').first().json.slackChannel }}", "={{ $json.slackText }}")
    mail = wf.node("메일 발송", "n8n-nodes-base.gmail", 2.1, (2260, 100), {
        "sendTo": "={{ $('설정').first().json.emailTo }}",
        "subject": "={{ $json.emailSubject }}",
        "emailType": "html",
        "message": "={{ $json.emailHtml }}",
        "options": {"appendAttribution": False},
    })

    wf.chain(t, cfg, demo)
    wf.link(demo, sample, 0)
    wf.link(demo, read, 1)
    wf.link(sample, agg)
    wf.link(read, agg)
    wf.link(agg, use_ai)
    wf.link(use_ai, req, 0)
    wf.link(use_ai, rep, 1)
    wf.chain(req, ai, ext, rep)
    wf.link(rep, slack)
    wf.link(rep, mail)
    wf.dump("03_일일_매출리포트.json")
    return wf


if __name__ == "__main__":
    print("n8n 워크플로 빌드:")
    build_w1()
    build_w2()
    build_w3()
