// [데모 모드] 네이버 커머스 API '상품주문 상세 조회' 응답과 같은 형태의 샘플 데이터
// 실제 계정 없이 워크플로 전체 흐름을 시연할 때 사용합니다.
const now = new Date();
const kst = (minAgo) =>
  new Date(now.getTime() + 9 * 3600e3 - minAgo * 60e3).toISOString().replace('Z', '+09:00');

const sample = [
  ['2026110411000001', '2026110410000001', '[1+1] 국산 무농약 현미 4kg', '용량: 4kg x 2', 1, 32900, '김민준', '010-1234-5678', '서울특별시 강남구 테헤란로 123', '101동 1001호', '문 앞에 놓아주세요'],
  ['2026110411000002', '2026110410000002', '제주 감귤 5kg 가정용', '크기: 중과', 2, 41800, '이서연', '010-2345-6789', '경기도 성남시 분당구 판교역로 45', '3층', ''],
  ['2026110411000003', '2026110410000003', '[1+1] 국산 무농약 현미 4kg', '용량: 4kg x 2', 1, 32900, '박지호', '010-3456-7890', '부산광역시 해운대구 센텀중앙로 78', '502호', '부재 시 경비실'],
];

return [{
  json: {
    data: sample.map(([poid, oid, name, opt, qty, amt, buyer, tel, addr, addr2, memo], i) => ({
      order: {
        orderId: oid,
        orderDate: kst(30 - i * 5),
        paymentDate: kst(29 - i * 5),
        ordererName: buyer,
        ordererTel: tel,
      },
      productOrder: {
        productOrderId: poid,
        productName: name,
        productOption: opt,
        quantity: qty,
        totalPaymentAmount: amt,
        shippingMemo: memo,
        shippingAddress: { name: buyer, tel1: tel, baseAddress: addr, detailedAddress: addr2, zipCode: '00000' },
      },
    })),
  },
}];
