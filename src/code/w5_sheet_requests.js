// 새로 만든 스프레드시트에 데이터 쓰기 + 서식 요청 만들기 (Sheets API values:batchUpdate / batchUpdate)
const s = $('주문 취합').first().json;
const created = $input.first().json;           // 새 파일 만들기 응답
const spreadsheetId = created.spreadsheetId;
if (!spreadsheetId) throw new Error('스프레드시트 생성 응답에 spreadsheetId 가 없습니다.');

const tabs = Object.keys(s.sheets);
const values = {
  valueInputOption: 'RAW',
  data: tabs.map((t) => ({ range: `'${t}'!A1`, values: s.sheets[t] })),
};

const color = { 택배업로드: { red: 1, green: 0.82, blue: 0.25 }, 주문전체: { red: 0.87, green: 0.9, blue: 0.94 }, 확인필요: { red: 0.99, green: 0.85, blue: 0.83 } };
const requests = [];
tabs.forEach((t, sheetId) => {
  const width = Math.max(1, s.sheets[t][0].length);
  requests.push({
    repeatCell: {
      range: { sheetId, startRowIndex: 0, endRowIndex: 1, startColumnIndex: 0, endColumnIndex: width },
      cell: { userEnteredFormat: { backgroundColor: color[t], textFormat: { bold: true } } },
      fields: 'userEnteredFormat(backgroundColor,textFormat)',
    },
  });
  requests.push({ autoResizeDimensions: { dimensions: { sheetId, dimension: 'COLUMNS', startIndex: 0, endIndex: width } } });
});

return [{
  json: {
    spreadsheetId,
    spreadsheetUrl: created.spreadsheetUrl || `https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`,
    valuesBody: values,
    formatBody: { requests },
  },
}];
