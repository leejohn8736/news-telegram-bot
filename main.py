import os
import datetime
import requests
import google.generativeai as genai

# 1. 환경 변수 로드
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. 날짜 설정 (KST)
now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today_str = now.strftime("%Y년 %m월 %d일")
weekday_map = {"Mon": "월", "Tue": "화", "Wed": "수", "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"}
weekday_str = weekday_map[now.strftime("%a")]
date_header = f"{today_str}({weekday_str})"

# 3. Gemini AI 프롬프트 생성 및 요청
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

prompt = f"""
오늘 날짜: {date_header}

당일 증시 심층 분석 브리핑을 작성하라.
[작성 지침]
- 제목 첫 줄: {date_header} — 국내외 증시 심층 브리핑
- 내용 구획:
  1. 밤사이 미국 증시
  2. 매크로 · FOMC
  3. 반도체 사이클
  4. 유가 · 지정학
  5. 정치·외교·통상·산업 (대통령 관련 포함)
- 🎯 오늘의 핵심 테마 정리
- 코스피 10개 종목 (1♡ ~ 10♡ 번호 형식, 종목명 옆 테마/섹터 적을 것)
- 코스닥 10개 종목 (1♡ ~ 10♡ 번호 형식, 종목명 옆 테마/섹터 적을 것)
- 경고 문구: "⚠️ 투자 유의사항: 위 종목 및 테마 정리는 최근 뉴스·수급 동향을 바탕으로 한 참고용 정보이며, 특정 종목의 매수·매도를 권유하는 것이 아닙니다. 종목 선정과 투자에 대한 최종 판단 및 그 결과에 대한 책임은 전적으로 투자자 본인에게 있습니다. 투자 전 반드시 최신 공시와 본인의 판단으로 재확인하시기 바랍니다."
- 맨 마지막 줄: 출처 AI
"""

response = model.generate_content(prompt)
briefing_text = response.text

# 4. 텔레그램 메시지 전송
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": briefing_text,
    "parse_mode": "Markdown"
}

res = requests.post(telegram_url, json=payload)
if res.status_code == 200:
    print("텔레그램 브리핑 전송 성공!")
else:
    print(f"전송 실패: {res.text}")
