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
        c = {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{wf.name}/{name}/{l}")), "leftValue": l}
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


# ---------- ④ 매일 아침 택배 업로드 엑셀 자동 생성 ----------

CJ_COLUMNS = """받는분성명=수령인
받는분전화번호=연락처
받는분주소=주소
품목명=품목
내품수량=수량
배송메세지=배송메모
고객주문번호=주문번호
합포장=합포장"""


def build_w4():
    wf = WF("④ 매일 아침 택배 업로드 엑셀 자동 생성 → 메일 첨부")
    wf.sticky(
        "## ④ 택배 업로드 엑셀 자동 생성\n"
        "출고일(월~토) 오전 8:40, 구글시트 `주문` 탭(워크플로 ①이 기록)에서\n"
        "지난번 이후 결제된 주문을 골라 **택배사 업로드용 엑셀 파일**을 새로 만들고\n"
        "메일에 첨부해서 보냅니다.\n\n"
        "- 같은 사람·같은 주소 주문은 한 박스로 합침 (`combineSameAddress`)\n"
        "- 주소·연락처가 이상한 주문은 엑셀에서 빼고 메일에 '확인 필요'로 표시\n"
        "- 한 번 보낸 주문은 다음 파일에 다시 들어가지 않음\n\n"
        "엑셀 열 이름·순서는 `설정 → columnMap`에서 택배사 양식에 맞게 바꾸세요.",
        (-80, -380), w=600, h=330, color=4)

    t = wf.node("출고일 08:40", "n8n-nodes-base.scheduleTrigger", 1.2, (0, 0),
                {"rule": {"interval": [{"field": "cronExpression", "expression": "40 8 * * 1-6"}]}})
    cfg = set_node(wf, "설정", (220, 0), [
        ("demoMode", True),
        ("shopName", "곡물상회"),
        ("sheetUrl", "https://docs.google.com/spreadsheets/d/여기에_시트_ID/edit"),
        ("emailTo", "owner@example.com"),
        ("combineSameAddress", True),
        ("columnMap", CJ_COLUMNS),
    ])
    demo = if_node(wf, "데모 모드?", (440, 0), "={{ $json.demoMode }}")
    sample = code_node(wf, "샘플 주문 (데모)", (680, -140), "w4_sample_rows.js")
    read = wf.node("주문 시트 읽기", "n8n-nodes-base.googleSheets", 4.5, (680, 140), {
        "documentId": {"__rl": True, "value": "={{ $('설정').first().json.sheetUrl }}", "mode": "url"},
        "sheetName": {"__rl": True, "value": "주문", "mode": "name"},
        "options": {},
    }, alwaysOutputData=True)
    sel = code_node(wf, "출고 대상 선별", (920, 0), "w4_select.js")
    has = if_node(wf, "택배 있음?", (1140, 0), "={{ $json.shipmentCount > 0 }}")
    rows = code_node(wf, "엑셀 행 만들기", (1380, -120), "w4_excel_rows.js")
    xlsx = wf.node("엑셀 파일 만들기", "n8n-nodes-base.convertToFile", 1.1, (1600, -120), {
        "operation": "xlsx",
        "binaryPropertyName": "data",
        "options": {
            "fileName": "={{ $('출고 대상 선별').first().json.fileName }}",
            "sheetName": "업로드",
            "headerRow": True,
        },
    })
    body1 = code_node(wf, "메일 내용 (파일 첨부)", (1820, -120), "w4_email.js")
    mail1 = wf.node("메일 발송 (엑셀 첨부)", "n8n-nodes-base.gmail", 2.1, (2040, -120), {
        "sendTo": "={{ $('설정').first().json.emailTo }}",
        "subject": "={{ $json.subject }}",
        "emailType": "html",
        "message": "={{ $json.html }}",
        "options": {
            "appendAttribution": False,
            "attachmentsUi": {"attachmentsBinary": [{"property": "data"}]},
        },
    })
    body2 = code_node(wf, "메일 내용 (출고 없음)", (1380, 140), "w4_email.js")
    mail2 = wf.node("메일 발송 (알림)", "n8n-nodes-base.gmail", 2.1, (1600, 140), {
        "sendTo": "={{ $('설정').first().json.emailTo }}",
        "subject": "={{ $json.subject }}",
        "emailType": "html",
        "message": "={{ $json.html }}",
        "options": {"appendAttribution": False},
    })
    done = code_node(wf, "처리 완료 기록", (2280, 0), "w4_mark_done.js")

    wf.chain(t, cfg, demo)
    wf.link(demo, sample, 0)
    wf.link(demo, read, 1)
    wf.link(sample, sel)
    wf.link(read, sel)
    wf.link(sel, has)
    wf.link(has, rows, 0)
    wf.link(has, body2, 1)
    wf.chain(rows, xlsx, body1, mail1, done)
    wf.chain(body2, mail2, done)
    wf.dump("04_택배업로드_엑셀_자동생성.json")
    return wf


# ---------- ⑤ 판매채널 주문 취합 → 택배 업로드 엑셀 + 구글 스프레드시트 자동 생성 ----------

def google_http(wf, name, pos, method, url, body_expr=None, cred="googleSheetsOAuth2Api"):
    p = {
        "method": method,
        "url": url,
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": cred,
        "options": {},
    }
    if body_expr:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": body_expr})
    return wf.node(name, "n8n-nodes-base.httpRequest", 4.2, pos, p, retryOnFail=True, maxTries=3, waitBetweenTries=3000)


def build_w5():
    wf = WF("⑤ 판매채널 주문 취합 → 택배 업로드 엑셀 + 구글 스프레드시트 자동 생성")
    wf.sticky(
        "## ⑤ 주문 취합 · 택배 업로드 자동화\n"
        "출고일 아침마다 **스마트스토어 + 쿠팡** 새 주문을 API로 가져와 하나로 합치고\n"
        "1. 구글 스프레드시트를 **새로 만들어** 탭 3개(택배업로드 · 주문전체 · 확인필요)에 정리\n"
        "2. 택배사 업로드용 **엑셀 파일** 생성\n"
        "3. 시트 링크 + 엑셀 첨부를 메일로, 요약은 슬랙으로\n\n"
        "- 판매처가 달라도 같은 집이면 합포장\n"
        "- 주소·연락처 이상 주문은 '확인필요' 탭으로 분리\n"
        "- 한 번 처리한 주문은 다시 들어가지 않음\n\n"
        "판매처 키를 비워 두면 그 판매처는 건너뜁니다. demoMode=true 이면 샘플 주문 8건으로 시연합니다.",
        (-80, -460), w=640, h=400, color=4)

    t = wf.node("출고일 08:40", "n8n-nodes-base.scheduleTrigger", 1.2, (0, 0),
                {"rule": {"interval": [{"field": "cronExpression", "expression": "40 8 * * 1-6"}]}})
    cfg = set_node(wf, "설정", (220, 0), [
        ("demoMode", True),
        ("shopName", "곡물상회"),
        ("naverClientId", ""),
        ("naverClientSecret", ""),
        ("naverLookbackHours", 0),
        ("coupangVendorId", ""),
        ("coupangAccessKey", ""),
        ("coupangStatus", "ACCEPT"),
        ("coupangLookbackDays", 2),
        ("combineSameAddress", True),
        ("columnMap", "판매처=판매처\n" + CJ_COLUMNS + "\n우편번호=우편번호"),
        ("driveFolderId", ""),
        ("emailTo", "owner@example.com"),
        ("slackChannel", ""),
    ])
    demo = if_node(wf, "데모 모드?", (440, 0), "={{ $json.demoMode }}")
    sample = code_node(wf, "샘플 주문 (데모)", (700, -260), "w5_sample.js")

    # 스마트스토어
    use_n = if_node(wf, "스마트스토어 연결?", (700, 120), "={{ !!$('설정').first().json.naverClientId }}")
    sign = code_node(wf, "네이버 API 서명 생성", (940, 0), "w1_naver_sign.js")
    token = wf.node("네이버 토큰 발급", "n8n-nodes-base.httpRequest", 4.2, (1160, 0), {
        "method": "POST", "url": f"{NAVER}/v1/oauth2/token",
        "sendBody": True, "contentType": "form-urlencoded",
        "bodyParameters": {"parameters": [{"name": k, "value": f"={{{{ $json.{k} }}}}"}
                                          for k in ("client_id", "timestamp", "client_secret_sign", "grant_type", "type")]},
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    win = code_node(wf, "조회 구간 나누기 (24시간)", (1380, 0), "w5_naver_windows.js")
    changed = wf.node("스마트스토어 변경 주문", "n8n-nodes-base.httpRequest", 4.2, (1600, 0), {
        "method": "GET", "url": f"{NAVER}/v1/pay-order/seller/product-orders/last-changed-statuses",
        "sendQuery": True, "queryParameters": {"parameters": [
            {"name": "lastChangedFrom", "value": "={{ $json.lastChangedFrom }}"},
            {"name": "lastChangedTo", "value": "={{ $json.lastChangedTo }}"},
            {"name": "lastChangedType", "value": "PAYED"}]},
        "sendHeaders": True, "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "=Bearer {{ $json.access_token }}"}]},
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    ids = code_node(wf, "상품주문번호 추출", (1820, 0), "w5_naver_ids.js")
    new_n = if_node(wf, "스마트스토어 새 주문?", (2040, 0), "={{ $json.productOrderIds.length > 0 }}")
    detail = wf.node("스마트스토어 주문 상세", "n8n-nodes-base.httpRequest", 4.2, (2260, -80), {
        "method": "POST", "url": f"{NAVER}/v1/pay-order/seller/product-orders/query",
        "sendHeaders": True, "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "=Bearer {{ $('네이버 토큰 발급').first().json.access_token }}"}]},
        "sendBody": True, "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ productOrderIds: $json.productOrderIds }) }}",
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    n_norm = code_node(wf, "스마트스토어 정리", (2480, 0), "w5_naver_normalize.js")

    # 쿠팡
    use_c = if_node(wf, "쿠팡 연결?", (2700, 120), "={{ !!$('설정').first().json.coupangAccessKey }}")
    c_prep = code_node(wf, "쿠팡 요청 준비", (2920, 240), "w5_coupang_prepare.js")
    c_sign = wf.node("쿠팡 서명 (HMAC)", "n8n-nodes-base.crypto", 2, (3140, 240), {
        "action": "hmac", "type": "SHA256", "value": "={{ $json.message }}",
        "dataPropertyName": "signature", "encoding": "hex",
    })
    c_get = wf.node("쿠팡 발주서 조회", "n8n-nodes-base.httpRequest", 4.2, (3360, 240), {
        "method": "GET",
        "url": "=https://api-gateway.coupang.com{{ $json.path }}?{{ $json.query }}",
        "sendHeaders": True, "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "=CEA algorithm=HmacSHA256, access-key={{ $('설정').first().json.coupangAccessKey }}, signed-date={{ $json.signedDate }}, signature={{ $json.signature }}"},
            {"name": "Content-Type", "value": "application/json;charset=UTF-8"}]},
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=3000)
    c_norm = code_node(wf, "쿠팡 정리", (3580, 240), "w5_coupang_normalize.js")

    # 취합 → 출력
    col = code_node(wf, "주문 취합", (3820, 0), "w5_collect.js")
    has = if_node(wf, "택배 있음?", (4040, 0), "={{ $json.shipmentCount > 0 }}")
    g_new = google_http(wf, "구글시트 새 파일 만들기", (4280, -140), "POST",
                        "https://sheets.googleapis.com/v4/spreadsheets", "={{ JSON.stringify($json.createRequest) }}")
    g_req = code_node(wf, "시트 쓰기 요청 구성", (4500, -140), "w5_sheet_requests.js")
    g_val = google_http(wf, "시트에 데이터 쓰기", (4720, -140), "POST",
                        "=https://sheets.googleapis.com/v4/spreadsheets/{{ $json.spreadsheetId }}/values:batchUpdate",
                        "={{ JSON.stringify($json.valuesBody) }}")
    g_fmt = google_http(wf, "시트 서식 (머리글·열 너비)", (4940, -140), "POST",
                        "=https://sheets.googleapis.com/v4/spreadsheets/{{ $('시트 쓰기 요청 구성').first().json.spreadsheetId }}:batchUpdate",
                        "={{ JSON.stringify($('시트 쓰기 요청 구성').first().json.formatBody) }}")
    use_f = if_node(wf, "드라이브 폴더 지정?", (5160, -140), "={{ !!$('설정').first().json.driveFolderId }}")
    g_move = google_http(wf, "드라이브 폴더로 이동", (5380, -260), "PATCH",
                         "=https://www.googleapis.com/drive/v3/files/{{ $('시트 쓰기 요청 구성').first().json.spreadsheetId }}"
                         "?addParents={{ $('설정').first().json.driveFolderId }}&removeParents=root&fields=id,parents",
                         cred="googleDriveOAuth2Api")
    rows = code_node(wf, "엑셀 행 만들기", (5600, -140), "w5_excel_rows.js")
    xlsx = wf.node("엑셀 파일 만들기", "n8n-nodes-base.convertToFile", 1.1, (5820, -140), {
        "operation": "xlsx", "binaryPropertyName": "data",
        "options": {"fileName": "={{ $('주문 취합').first().json.fileName }}", "sheetName": "택배업로드", "headerRow": True},
    })
    n1 = code_node(wf, "알림 내용 (파일 첨부)", (6040, -140), "w5_notify.js")
    m1 = wf.node("메일 발송 (시트 링크 + 엑셀)", "n8n-nodes-base.gmail", 2.1, (6260, -140), {
        "sendTo": "={{ $('설정').first().json.emailTo }}", "subject": "={{ $json.subject }}",
        "emailType": "html", "message": "={{ $json.html }}",
        "options": {"appendAttribution": False, "attachmentsUi": {"attachmentsBinary": [{"property": "data"}]}},
    })
    n2 = code_node(wf, "알림 내용 (출고 없음)", (4280, 160), "w5_notify.js")
    m2 = wf.node("메일 발송 (알림)", "n8n-nodes-base.gmail", 2.1, (4500, 160), {
        "sendTo": "={{ $('설정').first().json.emailTo }}", "subject": "={{ $json.subject }}",
        "emailType": "html", "message": "={{ $json.html }}", "options": {"appendAttribution": False},
    })
    use_s = if_node(wf, "슬랙 사용?", (6480, 0), "={{ !!$('설정').first().json.slackChannel }}")
    slack = slack_node(wf, "슬랙 요약", (6700, -100),
                       "={{ $('설정').first().json.slackChannel }}",
                       "={{ $('알림 내용 (파일 첨부)').isExecuted ? $('알림 내용 (파일 첨부)').first().json.slackText : $('알림 내용 (출고 없음)').first().json.slackText }}")
    done = code_node(wf, "처리 완료 기록", (6920, 0), "w5_mark_done.js")

    wf.chain(t, cfg, demo)
    wf.link(demo, sample, 0)
    wf.link(demo, use_n, 1)
    wf.link(sample, col)
    wf.link(use_n, sign, 0)
    wf.link(use_n, use_c, 1)
    wf.chain(sign, token, win, changed, ids, new_n)
    wf.link(new_n, detail, 0)
    wf.link(new_n, n_norm, 1)
    wf.link(detail, n_norm)
    wf.link(n_norm, use_c)
    wf.link(use_c, c_prep, 0)
    wf.link(use_c, col, 1)
    wf.chain(c_prep, c_sign, c_get, c_norm, col)
    wf.link(col, has)
    wf.link(has, g_new, 0)
    wf.link(has, n2, 1)
    wf.chain(g_new, g_req, g_val, g_fmt, use_f)
    wf.link(use_f, g_move, 0)
    wf.link(use_f, rows, 1)
    wf.link(g_move, rows)
    wf.chain(rows, xlsx, n1, m1, use_s)
    wf.chain(n2, m2, use_s)
    wf.link(use_s, slack, 0)
    wf.link(use_s, done, 1)
    wf.link(slack, done)
    # 보기 좋게 두 줄 배치: 윗줄 = 판매처별 수집, 아랫줄 = 취합 이후 출력
    out_names = {col, has, g_new, g_req, g_val, g_fmt, use_f, g_move, rows, xlsx, n1, m1, n2, m2, use_s, slack, done}
    for n in wf.nodes:
        if n["name"] in out_names:
            n["position"] = [n["position"][0] - 3380, n["position"][1] + 720]
    wf.sticky("### 1단계 · 판매처별 주문 수집\n스마트스토어(24시간 구간 조회) → 쿠팡(HMAC 서명) → 공통 형식으로 정리",
              (940, -300), w=560, h=110, color=7)
    wf.sticky("### 2단계 · 취합 → 구글시트 · 엑셀 · 알림\n중복 제외 · 검증 · 합포장 → 새 스프레드시트(탭 3개) + 엑셀 첨부 메일 + 슬랙",
              (180, 440), w=560, h=110, color=7)
    wf.dump("05_주문취합_택배엑셀_구글시트_자동생성.json")
    return wf


if __name__ == "__main__":
    print("n8n 워크플로 빌드:")
    build_w1()
    build_w2()
    build_w3()
    build_w4()
    build_w5()
