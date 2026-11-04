"""견적 계산 (AI가 아니라 규칙으로 계산 — 같은 의뢰면 항상 같은 가격)."""
from dataclasses import dataclass

# 크몽 상세페이지 가격과 맞춰서 관리하세요.
PACKAGES = {
    "STANDARD": {"price": 99_000, "days": 2, "revisions": 1, "support_days": 30, "max_steps": 5, "max_services": 2},
    "DELUXE": {"price": 330_000, "days": 5, "revisions": 2, "support_days": 30, "max_steps": 12, "max_services": 3},
    "PREMIUM": {"price": 770_000, "days": 10, "revisions": 3, "support_days": 60, "max_steps": 30, "max_services": 5},
}
EXTRA_SERVICE = 55_000       # 패키지 한도를 넘는 연동 서비스 1개당
SERVER_SETUP = 55_000        # n8n 서버 세팅 대행 (선택)
MAINTENANCE_MONTHLY = 55_000 # 월 유지보수 (선택)
HOURLY_WAGE = 12_000         # 절감 효과 계산용 인건비 (원/시간)

NON_SERVICES = {"", "n8n", "없음", "내부", "-"}


@dataclass
class Quote:
    package: str
    base_price: int
    extra_services: int
    extra_price: int
    total: int
    days: int
    revisions: int
    support_days: int
    services: list
    hours_saved_month: float
    savings_month: int
    payback_months: float | None


def services_of(a) -> list:
    names = {i.name.strip() for i in a.integrations}
    names |= {s.service.strip() for s in a.steps}
    return sorted(n for n in names if n not in NON_SERVICES)


def make_quote(a) -> Quote:
    services = services_of(a)
    n_steps = len(a.steps)
    uses_ai = any(s.kind == "claude_ai" for s in a.steps)

    if a.complexity == "복잡" or n_steps > PACKAGES["DELUXE"]["max_steps"] or len(services) > PACKAGES["DELUXE"]["max_services"]:
        pkg = "PREMIUM"
    elif a.complexity == "단순" and not uses_ai and n_steps <= PACKAGES["STANDARD"]["max_steps"] and len(services) <= PACKAGES["STANDARD"]["max_services"]:
        pkg = "STANDARD"
    else:
        pkg = "DELUXE"

    p = PACKAGES[pkg]
    extra = max(0, len(services) - p["max_services"])
    total = p["price"] + extra * EXTRA_SERVICE
    hours = round(a.manual_minutes_per_run * a.runs_per_month / 60, 1)
    savings = int(hours * HOURLY_WAGE)
    payback = round(total / savings, 1) if savings else None
    return Quote(pkg, p["price"], extra, extra * EXTRA_SERVICE, total, p["days"], p["revisions"],
                 p["support_days"], services, hours, savings, payback)
