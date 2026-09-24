import os
import datetime
import requests
from google import genai

# ==========================================
# 1. 환경 변수(Secrets) 검증
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("[오류] GitHub Secrets 설정에 GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID가 필요합니다.")

# ==========================================
# 2. 날짜 헤더 생성 (한국 표준시 KST 기준)
# ==========================================
# GitHub Actions 서버 기본 시간(UTC)에 9시간 추가
now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today_str = now_kst.strftime("%Y년 %m월 %d일")
weekday_map = {"Mon": "월", "Tue": "화", "Wed": "수", "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"}
weekday_str = weekday_map[now_kst.strftime("%a")]
date_header = f"{today_str}({weekday_str})"

# ==========================================
# 3. Gemini Client 초기화 및 브리핑 요청
# ==========================================
# google-genai SDK 1.0+ 표준 클라이언트 생성
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
오늘 날짜: {date_header}

당일 증시 심층 분석 브리핑을 작성하라.

[작성 규칙]
1. 글의 가장 첫 줄에는 반드시 아래 타이틀을 적을 것:
   "{date_header} — 국내외 증시 심층 브리핑"
2. 밤사이 미국 증시, 매크로·FOMC, 반도체 사이클, 유가·지정학, 정치·외교·통상·산업(대통령 관련 뉴스 포함) 내용을 심층 정리할 것.
3. 🎯 오늘의 핵심 테마 정리를 포함할 것.
4. 코스피 10개 종목을 1♡ ~ 10♡ 번호 형식으로 적고, 종목명 옆에 테마와 섹터를 적을 것.
5. 코스닥 10개 종목을 1♡ ~ 10♡ 번호 형식으로 적고, 종목명 옆에 테마와 섹터를 적을 것.
6. 투자 유의사항 경고 문구를 반드시 포함할 것:
   "⚠️ 투자 유의사항: 위 종목 및 테마 정리는 최근 뉴스·수급 동향을 바탕으로 한 참고용 정보이며, 특정 종목의 매수·매도를 권유하는 것이 아닙니다. 종목 선정과 투자에 대한 최종 판단 및 그 결과에 대한 책임은 전적으로 투자자 본인에게 있습니다. 투자 전 반드시 최신 공시와 본인의 판단으로 재확인하시기 바랍니다."
7. 글의 가장 마지막 줄에는 반드시 아래 문구를 포함할 것:
   "출처 AI"
"""

# 최신 추천 표준 모델 (gemini-2.5-flash) 사용
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

briefing_text = response.text

# ==========================================
# 4. 텔레그램 API 메시지 발송
# ==========================================
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": briefing_text
}

res = requests.post(telegram_url, json=payload)

if res.status_code == 200:
    print("텔레그램 시황 브리핑 전송 성공!")
else:
    print(f"텔레그램 발송 실패 (상태 코드 {res.status_code}): {res.text}")
    exit(1)
