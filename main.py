import os
import sys
import json
import urllib.request
import urllib.parse

# 깃허브 Secrets에서 텔레그램 토큰 및 채팅방 ID 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(text):
    """파이썬 기본 내장 라이브러리로 텔레그램 메시지 발송 및 에러 상세 출력"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 설정값이 없습니다.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode('utf-8')
            print(f"📡 텔레그램 응답 상태 코드: {response.status}")
            print(f"📡 텔레그램 응답 상세 내용: {res_body}")
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"❌ 텔레그램 전송 실패! HTTP 에러 코드: {e.code}")
        print(f"📡 텔레그램 응답 상세 내용: {err_body}")
        return False
    except Exception as e:
        print(f"❌ 텔레그램 발송 중 오류 발생: {e}")
        return False

def fetch_news():
    """뉴스 데이터 생성 함수"""
    news_text = "📰 <b>[실시간 주요 뉴스 알림]</b>\n\n"
    news_text += "• <a href='https://news.naver.com'>[네이버뉴스] AI 및 반도체 시장 최신 동향</a>\n"
    news_text += "• <a href='https://www.fnnews.com'>[파이낸셜뉴스] 증권 및 금융 시장 관련 소식</a>\n"
    return news_text

def main():
    print("🚀 뉴스 크롤러 및 텔레그램 발송 로봇 시작!")
    
    message = fetch_news()
    success = send_telegram_msg(message)
    
    if success:
        print("🎉 성공적으로 텔레그램 메시지를 발송했습니다!")
    else:
        print("⚠️ 텔레그램 발송 실패 - 위의 '텔레그램 응답 상세 내용'을 확인하세요.")

if __name__ == "__main__":
    main()
