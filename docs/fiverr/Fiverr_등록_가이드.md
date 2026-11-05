# Fiverr 등록 가이드

> 영어 부분은 Fiverr에 그대로 붙여 넣으면 됩니다. 한국어로 된 부분은 등록할 때 참고할 메모입니다.

## 한국어 메모 (먼저 읽기)
- **타깃이 크몽과 다릅니다.** Fiverr 구매자는 미국·유럽의 Shopify·Amazon·Etsy 셀러입니다. 그래서 스마트스토어·쿠팡 대신 Shopify·Amazon 기준으로 바꿨습니다.
- **아직 만들지 않은 것:** Shopify·Amazon용 n8n 워크플로는 아직 없습니다. 지금 있는 건 스마트스토어·쿠팡용입니다. 첫 주문이 들어오면 그 고객 환경에 맞춰 만들면 됩니다. 아래 설명은 "맞춤 제작" 기준으로 써서 거짓말이 되지 않게 했습니다.
  - Shopify 주문 조회는 n8n에 Shopify 노드가 있어 쉽습니다.
  - Amazon(SP-API)은 셀러 계정 승인 절차가 있어서 시간이 더 걸립니다. 그래서 Premium에만 넣었습니다.
- **Fiverr 규칙:**
  - 설명이나 이미지에 연락처, 외부 링크, "Fiverr 밖에서 거래" 같은 문구를 넣으면 안 됩니다.
  - 콘솔 링크도 설명에 넣지 말고, 이미지와 포트폴리오로만 보여주세요.
- **수수료와 정산:** Fiverr는 판매자 수수료가 20%이고, 정산은 Payoneer나 PayPal로 받습니다.
- **가격:** 처음 리뷰를 모으는 동안은 아래 가격으로 시작하고, 리뷰 10개 이후 30~50% 올리기를 권합니다.
- **이미지 업로드 순서:**
  1. `gig_1_main.png` (대표)
  2. `gig_2_console.png`
  3. `gig_3_before_after.png`

  크기는 모두 1280×769입니다.

---

## Gig title (80자 이내 · 2안)
- I will automate your Shopify and Amazon orders with n8n and Google Sheets
- I will build n8n automations that turn your daily orders into a ready shipping file

## Category (서비스 · 포트폴리오 프로젝트 공통)
- 1순위: **Programming & Tech → AI Coding → AI Integrations**
- 목록에 **AI Agents**나 **Automation(n8n)** 하위 항목이 보이면 그쪽도 괜찮습니다. 서비스 유형(Service type)에 n8n이 있으면 n8n을 고르세요.
- 메뉴 이름은 Fiverr가 자주 바꾸니, 등록 화면 드롭다운에서 가장 가까운 이름을 고르면 됩니다.

## Industry (업종 · 서비스 정보/포트폴리오 항목에 나오면 선택)
- 1순위: **E-commerce**
- 함께 고를 수 있으면: **Retail**
- 포트폴리오 이미지의 샘플 가게(곡물 판매)에 맞추려면: **Food & Beverage**

## Search tags (5)
`n8n` · `shopify automation` · `workflow automation` · `google sheets automation` · `ecommerce automation`

---

## Packages

| | Basic | Standard | Premium |
|---|---|---|---|
| **Name** | Order Sync Starter | Custom Order Workflow | Full Ops Automation |
| **Price** | $60 | $180 | $450 |
| **Description** | One workflow: new Shopify orders logged to Google Sheets with an email or Slack alert | One custom workflow: orders merged, same-address orders combined, address check, shipping upload file + new Google Sheet daily | Up to 3 connected workflows (order sync, inquiry triage with reply drafts, daily sales report) + an operations dashboard |
| **Delivery** | 3 days | 5 days | 10 days |
| **Revisions** | 1 | 2 | 3 |
| **Integrations** | 2 | up to 4 | up to 6 (incl. Amazon SP-API) |
| **Setup in your n8n** | ✓ | ✓ | ✓ |
| **Walkthrough video** | – | ✓ | ✓ |
| **Support after delivery** | 14 days | 30 days | 30 days |

**Gig extras**
- n8n Cloud or self-hosted setup: +$40
- Extra integration: +$40
- Monthly maintenance (API changes, small edits): $50/month

---

## Description (붙여넣기용)

**Stop copy-pasting orders every morning.**

If you sell on Shopify, Amazon, or both, you probably start the day exporting orders, merging spreadsheets and retyping addresses into your shipping app. I build n8n automations that do this for you before you open your laptop.

**What I can automate for you**
- **Order sync:** pull new paid orders from Shopify and Amazon on a schedule
- **Shipping file:** one upload-ready file in your shipping app's column format
- **Combined shipments:** same household across channels becomes one box
- **Address check:** missing or broken addresses and phones go to a "Needs review" list instead of the label file
- **Google Sheets:** a fresh, formatted sheet every ship day (shipments, all orders, needs review)
- **Alerts:** email and Slack summaries with the sheet link and file attached
- **Inquiry triage (Premium):** each customer message is sorted by topic and urgency, with a reply draft your team reviews before sending
- **Daily sales report (Premium):** yesterday's revenue, orders and top products in your inbox

**How we work**
1. You tell me how you handle orders today (a short screen recording is perfect)
2. I send a workflow plan before any build starts
3. I build and test it in your n8n with your accounts
4. You get a walkthrough and a simple guide for small changes

**Why work with me**
- I design for the messy parts: duplicate orders, weekend backlogs, API timeouts and retries
- Settings like alert channels, schedules and file columns sit in one place you can edit without code
- Everything runs in your own n8n and Google account, so you own it

Not sure which package fits? Send me a message describing your current process and I will recommend one.

---

## FAQ

**Do I need n8n already?**
No. I can set up n8n Cloud for you (paid by you directly to n8n) or install it on your own server as an extra.

**Which shipping apps are supported?**
Anything that accepts a CSV or Excel upload (for example ShipStation, Pirate Ship, Shippo or your carrier's bulk upload). I match the file to your app's columns.

**Can it buy labels automatically?**
Not in the standard packages. The workflow prepares the upload file and you confirm the labels. That keeps a person in the loop for cancellations and last-minute changes.

**Is my customer data safe?**
The automation runs in your accounts. I only need temporary access during setup, and you can revoke it after delivery.

**What if Shopify or Amazon changes their API?**
Bugs in what I delivered are fixed free during the support period. API changes after that are covered by the monthly maintenance extra.

---

## Requirements (구매자에게 받는 질문)
1. Which sales channels do you use? (Shopify, Amazon, Etsy, other)
2. About how many orders do you ship per day?
3. Which shipping app or carrier do you upload labels to? Please attach a sample upload file if you have one.
4. Where should results go? (email, Slack, Google Sheets)
5. Do you already use n8n? (Cloud, self-hosted, or not yet)
6. Optional: a 1–2 minute screen recording of how you process orders today
