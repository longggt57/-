"""의뢰 분석 결과 스키마 (Claude structured output 으로 그대로 받음)."""
from typing import List, Literal

from pydantic import BaseModel, Field

StepKind = Literal[
    "schedule_trigger",      # 정해진 시간마다 실행
    "webhook_trigger",       # 외부에서 데이터가 들어오면 실행 (폼, 챗봇, 다른 서비스)
    "manual_trigger",        # 사람이 버튼을 눌러 실행
    "http_request",          # 외부 API 호출 (쇼핑몰, ERP, 택배사 등)
    "code",                  # 데이터 가공·계산·형식 변환
    "if_condition",          # 조건에 따라 분기
    "google_sheets_read",
    "google_sheets_append",
    "slack_message",
    "gmail_send",
    "claude_ai",             # AI 분류·요약·작성
]


class Integration(BaseModel):
    name: str = Field(description="연동할 서비스 이름 (예: 네이버 스마트스토어, 구글시트)")
    api_available: Literal["가능", "불가", "확인필요"]
    note: str = Field(description="API 발급 방법이나 제약 사항 한 줄")


class Step(BaseModel):
    title: str = Field(description="n8n 노드 이름으로 쓸 짧은 한국어 제목 (15자 이내)")
    kind: StepKind
    service: str = Field(description="이 단계가 다루는 서비스. 없으면 빈 문자열")
    detail: str = Field(description="이 단계가 하는 일을 구체적으로 1~2문장")


class ProjectAnalysis(BaseModel):
    client_name: str = Field(description="고객/회사 이름. 모르면 '고객'")
    one_line: str = Field(description="의뢰를 한 문장으로 요약")
    problem: str = Field(description="고객이 겪는 문제 (PROBLEM)")
    why_now: str = Field(description="지금 해결하려는 이유 (WHY). 추정이면 '(추정)' 표시")
    goals: List[str] = Field(description="성공 기준 2~4개")
    current_process: List[str] = Field(description="지금 사람이 하는 작업 순서")
    integrations: List[Integration]
    steps: List[Step] = Field(description="자동화 단계. 첫 단계는 반드시 트리거")
    human_approval: List[str] = Field(description="사람이 확인해야 하는 지점. 없으면 빈 배열")
    risks: List[str] = Field(description="기술·약관·개인정보 위험")
    refuse: bool = Field(description="거절 기준에 해당하면 true")
    refuse_reason: str = Field(description="refuse가 true일 때 이유. 아니면 빈 문자열")
    missing_questions: List[str] = Field(description="견적 확정 전에 고객에게 물어볼 질문 3~6개")
    manual_minutes_per_run: int = Field(description="지금 이 업무 1회에 드는 시간(분), 추정")
    runs_per_month: int = Field(description="한 달에 이 업무를 하는 횟수, 추정")
    complexity: Literal["단순", "보통", "복잡"]
    reply_message: str = Field(description="크몽 채팅에 보낼 첫 답장. 이해한 내용 확인 → 진행 방식 → 추가 질문 순서, 정중한 존댓말")
