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


# 실제 API 경로 테스트용: 외부 호출 노드를 가짜 응답을 내는 코드 노드로 바꿉니다.
W5_MOCKS = {
    "네이버 토큰 발급": "return [{ json: { access_token: 'tok' } }];",
    "스마트스토어 변경 주문": """return $input.all().map((_, i) => ({ json: { data: { lastChangeStatuses: i === 0
      ? [{ productOrderId: 'P1', lastChangedType: 'PAYED' }, { productOrderId: 'P2', lastChangedType: 'PAYED' }]
      : [{ productOrderId: 'P2', lastChangedType: 'PAYED' }] } } }));""",
    "스마트스토어 주문 상세": """const ids = $input.first().json.productOrderIds;
      const mk = (id, name, who, addr) => ({ order: { orderId: 'O' + id, paymentDate: '2026-11-04T09:00:00.000+09:00', ordererName: who },
        productOrder: { productOrderId: id, productName: name, quantity: 1, totalPaymentAmount: 10000,
          shippingAddress: { name: who, tel1: '010-1111-2222', baseAddress: addr, detailedAddress: '101호', zipCode: '03000' } } });
      return [{ json: { data: ids.map((id) => id === 'P1' ? mk(id, '현미 4kg', '가나다', '서울특별시 종로구 세종대로 1') : mk(id, '찹쌀 2kg', '라마바', '부산광역시 중구 중앙대로 2')) } }];""",
    "쿠팡 서명 (HMAC)": "return [{ json: { ...$input.first().json, signature: 'deadbeef' } }];",
    "쿠팡 발주서 조회": """return [{ json: { code: 200, data: [{ shipmentBoxId: 111, orderId: 222, paidAt: '2026-11-04T08:00:00',
      orderer: { name: '가나다' }, receiver: { name: '가나다', safeNumber: '0503-1111-2222', addr1: '서울특별시 종로구 세종대로 1', addr2: '101호', postCode: '03000' },
      parcelPrintMessage: '문 앞', orderItems: [{ vendorItemId: 9, sellerProductName: '귀리 1kg', sellerProductItemName: '1개', shippingCount: 2, orderPrice: 15000 }] }] } }];""",
}
GOOGLE_MOCKS = {
    "구글시트 새 파일 만들기": """const req = $input.first().json.createRequest;
      if (!req?.properties?.title || req.sheets.length !== 3) throw new Error('생성 요청 형식 오류');
      return [{ json: { spreadsheetId: 'TEST_SHEET_ID', spreadsheetUrl: 'https://docs.google.com/spreadsheets/d/TEST_SHEET_ID/edit',
        sheets: req.sheets } }];""",
    "시트에 데이터 쓰기": """const b = $input.first().json.valuesBody;
      if (b.valueInputOption !== 'RAW' || b.data.length !== 3) throw new Error('쓰기 요청 형식 오류');
      return [{ json: { spreadsheetId: 'TEST_SHEET_ID', totalUpdatedRows: b.data.reduce((s, d) => s + d.values.length, 0) } }];""",
    "시트 서식 (머리글·열 너비)": "return [{ json: { spreadsheetId: 'TEST_SHEET_ID', replies: [] } }];",
    "드라이브 폴더로 이동": "return [{ json: { id: 'TEST_SHEET_ID' } }];",
}
W5_SETTINGS = {"demoMode": False, "naverClientId": "test-client",
               "naverClientSecret": "$2a$04$abcdefghijklmnopqrstuu", "coupangVendorId": "A00012345", "coupangAccessKey": "ak"}


def make_test_copy(wf, idx, inquiry=None, mocks=None, settings=None):
    wf = copy.deepcopy(wf)
    wf["id"] = f"kmongdemo{idx:07d}"  # 16자 영숫자
    wf["active"] = False
    for n in wf["nodes"]:
        if mocks and n["name"] in mocks:
            n.update(type="n8n-nodes-base.code", typeVersion=2, parameters={"jsCode": mocks[n["name"]]})
            n.pop("credentials", None)
            continue
        if settings and n["name"] == "설정":
            for a in n["parameters"]["assignments"]["assignments"]:
                if a["name"] in settings:
                    a["value"] = settings[a["name"]]
                    a["type"] = "boolean" if isinstance(settings[a["name"]], bool) else "string"
        if n["type"] in EXTERNAL or (n["type"] == "n8n-nodes-base.httpRequest"
                                     and "googleapis.com" in str(n["parameters"].get("url", ""))):
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
            cases.append((f.stem, make_test_copy(wf, i, mocks=GOOGLE_MOCKS)))
        if f.stem.startswith("05_"):
            cases.append((f"{f.stem} [실제 경로·가짜 API]",
                          make_test_copy(wf, 90 + i, mocks={**W5_MOCKS, **GOOGLE_MOCKS}, settings={**W5_SETTINGS, "driveFolderId": "FOLDER1"})))

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
