import os
import sys
import datetime
import requests
from google import genai

# 1. 환경 변수(GitHub Secrets) 검증
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("[오류] GitHub Secrets 값(GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)이 설정되지 않았습니다.")
    sys.exit(1)

# 2. 한국 시간(KST) 기준 날짜 헤더 생성
now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today_str = now_kst.strftime("%Y년 %m월 %d일")
weekday_map = {"Mon": "월", "Tue": "화", "Wed": "수", "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"}
weekday_str = weekday_map[now_kst.strftime("%a")]
date_header = f"{today_str}({weekday_str})"

# 3. Google GenAI Client 초기화
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
오늘 날짜: {date_header}

당일 증시 심층 분석 브리핑을 작성하라.

[작성 규칙]
1. 글 시작 전 가장 첫 줄에 오늘 날짜를 적을 것: "{date_header} — 국내외 증시 심층 브리핑"
2. 밤사이 미국 증시, 매크로·FOMC, 반도체 사이클, 유가·지정학, 정치·외교·통상·산업(대통령 관련 뉴스 포함) 내용을 심층 정리할 것.
3. 🎯 오늘의 핵심 테마 정리를 포함할 것.
4. 코스피 10개 종목을 1♡ ~ 10♡ 번호 형식으로 적고, 종목명 옆에 테마와 섹터를 표기할 것.
5. 코스닥 10개 종목을 1♡ ~ 10♡ 번호 형식으로 적고, 종목명 옆에 테마와 섹터를 표기할 것.
6. 투자 유의사항 경고 문구를 반드시 포함할 것:
   "⚠️ 투자 유의사항: 위 종목 및 테마 정리는 최근 뉴스·수급 동향을 바탕으로 한 참고용 정보이며, 특정 종목의 매수·매도를 권유하는 것이 아닙니다. 종목 선정과 투자에 대한 최종 판단 및 그 결과에 대한 책임은 전적으로 투자자 본인에게 있습니다. 투자 전 반드시 최신 공시와 본인의 판단으로 재확인하시기 바랍니다."
7. 글의 가장 마지막 줄에는 반드시 "출처 AI" 라고 적을 것.
"""

try:
    # Gemini 최신 모델 호출
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    briefing_text = response.text
except Exception as e:
    print(f"[Gemini API 호출 에러] {e}")
    sys.exit(1)

# 4. 텔레그램 메시지 발송
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": briefing_text
}

try:
    res = requests.post(telegram_url, json=payload)
    if res.status_code == 200:
        print("텔레그램 시황 브리핑 전송 완료!")
    else:
        print(f"[텔레그램 발송 실패] 상태 코드: {res.status_code}, 응답: {res.text}")
        sys.exit(1)
except Exception as e:
    print(f"[텔레그램 요청 에러] {e}")
    sys.exit(1)
