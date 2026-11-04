"""분석 결과 + 견적 → 고객용/내부용 문서."""
from datetime import date, timedelta

from pricing import MAINTENANCE_MONTHLY, SERVER_SETUP, HOURLY_WAGE

KIND_LABEL = {
    "schedule_trigger": "⏰ 예약 실행", "webhook_trigger": "📥 데이터 수신", "manual_trigger": "▶ 수동 실행",
    "http_request": "🔗 외부 연동", "code": "⚙ 데이터 처리", "if_condition": "🔀 조건 분기",
    "google_sheets_read": "📄 시트 읽기", "google_sheets_append": "📝 시트 기록",
    "slack_message": "💬 슬랙 알림", "gmail_send": "✉ 메일 발송", "claude_ai": "🤖 AI 처리",
}


def won(n):
    return f"{int(n):,}원"


def bullets(items, empty="- 없음"):
    return "\n".join(f"- {i}" for i in items) if items else empty


def requirements_md(a, q):
    ints = "\n".join(f"| {i.name} | {i.api_available} | {i.note} |" for i in a.integrations) or "| - | - | - |"
    return f"""# 요구사항 정리 (내부용) — {a.client_name}

> {a.one_line}

## PROBLEM — 문제
{a.problem}

## WHY — 지금 해결하려는 이유
{a.why_now}

## 성공 기준
{bullets(a.goals)}

## 현재 수작업 순서
{chr(10).join(f"{n}. {s}" for n, s in enumerate(a.current_process, 1))}

## 연동 서비스
| 서비스 | API | 메모 |
|---|---|---|
{ints}

## 사람 확인 지점
{bullets(a.human_approval)}

## 위험 요소
{bullets(a.risks)}

## 견적 전 확인 질문
{chr(10).join(f"{n}. {s}" for n, s in enumerate(a.missing_questions, 1))}

## 판정
- 난이도: **{a.complexity}** · 단계 {len(a.steps)}개 · 연동 {len(q.services)}개 ({", ".join(q.services) or "-"})
- 추천 패키지: **{q.package}** ({won(q.total)})
- 절감 추정: 1회 {a.manual_minutes_per_run}분 × 월 {a.runs_per_month}회 = **월 {q.hours_saved_month}시간** ≈ {won(q.savings_month)} (시급 {won(HOURLY_WAGE)} 기준)
{"- ⛔ **거절 대상**: " + a.refuse_reason if a.refuse else ""}
"""


def quote_md(a, q, seller="판매자"):
    today = date.today()
    valid = today + timedelta(days=14)
    extra = (f"| 추가 연동 서비스 {q.extra_services}개 | {won(q.extra_price)} |\n" if q.extra_services else "")
    payback = (f"약 **{q.payback_months}개월**이면 제작비를 회수합니다." if q.payback_months else "")
    return f"""# 견적서

| | |
|---|---|
| 고객 | {a.client_name} 님 |
| 작성일 | {today.isoformat()} |
| 유효기간 | {valid.isoformat()}까지 |
| 작성 | {seller} |

## 의뢰 내용
{a.one_line}

## 기대 효과
- 지금: 1회 약 {a.manual_minutes_per_run}분 × 월 {a.runs_per_month}회 = **월 {q.hours_saved_month}시간**
- 자동화 후: 확인만 하시면 됩니다{" (" + ", ".join(a.human_approval) + ")" if a.human_approval else ""}
- 인건비로 환산하면 월 약 **{won(q.savings_month)}** 절감 (시급 {won(HOURLY_WAGE)} 기준). {payback}

## 금액
| 항목 | 금액 |
|---|---|
| {q.package} 패키지 | {won(q.base_price)} |
{extra}| **합계** | **{won(q.total)}** |

- 작업 기간: 결제 후 **{q.days}일** (영업일 기준, 자료 수령 후 시작)
- 수정: {q.revisions}회 포함 · 무상 오류 대응: 납품 후 {q.support_days}일

## 포함 범위
{chr(10).join(f"{n}. {s.title} — {s.detail}" for n, s in enumerate(a.steps, 1))}

## 포함되지 않는 것
- n8n 실행 환경 비용 (n8n Cloud 구독 또는 서버) — 세팅 대행 옵션 {won(SERVER_SETUP)}
- 연동 서비스 자체 이용료, AI(Claude) API 사용료 (고객님 계정에서 사용량만큼 발생)
- 위 범위 밖 기능 추가 (별도 견적)
- 납품 후 판매처·사이트 정책 변경 대응 — 월 유지보수 옵션 {won(MAINTENANCE_MONTHLY)}/월

## 진행 순서
1. 견적 확인 및 아래 자료 전달
2. 설계서 확인 → 결제
3. 제작 및 고객님 계정 연결 테스트
4. 사용 가이드 전달 · 구매 확정

## 확인 부탁드릴 사항
{chr(10).join(f"- {q_}" for q_ in a.missing_questions)}
"""


def design_md(a):
    lines = ["flowchart LR"]
    for n, s in enumerate(a.steps):
        label = s.title.replace('"', "'")
        shape = f'{{"{label}"}}' if s.kind == "if_condition" else f'["{label}"]'
        lines.append(f"  S{n}{shape}")
        if n:
            lines.append(f"  S{n-1} --> S{n}")
    rows = "\n".join(
        f"| {n} | {KIND_LABEL.get(s.kind, s.kind)} | **{s.title}** | {s.service or '-'} | {s.detail} |"
        for n, s in enumerate(a.steps, 1))
    return f"""# 자동화 설계서 — {a.client_name}

> {a.one_line}

## 흐름도
```mermaid
{chr(10).join(lines)}
```

## 단계별 동작
| # | 종류 | 단계 | 서비스 | 설명 |
|---|---|---|---|---|
{rows}

## 사람이 확인하는 지점
{bullets(a.human_approval)}

## 이렇게 되면 성공입니다
{bullets(a.goals)}

## 알아두실 점
{bullets(a.risks)}
"""
