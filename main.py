import os
import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

# 깃허브 Secrets에서 텔레그램 토큰 및 채팅방 ID 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(text):
    """텔레그램 메시지 발송 및 상세 에러 로그 출력 함수"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 설정값이 없습니다.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        # 텔레그램 서버의 실제 응답 상태 및 원인 출력
        print(f"📡 텔레그램 응답 상태 코드: {response.status_code}")
        print(f"📡 텔레그램 응답 상세 내용: {response.text}")
        
        if response.status_code == 200:
            return True
        else:
            print("❌ 텔레그램 전송 실패!")
            return False
    except Exception as e:
        print(f"❌ 텔레그램 발송 중 네트워크 오류 발생: {e}")
        return False

def fetch_news():
    """뉴스 크롤링 샘플 함수"""
    # 10개 주요 키워드 예시
    keywords = ["삼성전자", "AI", "반도체", "증권", "부동산", "금리", "주식", "현대차", "SK하이닉스", "배터리"]
    
    # 크롤링한 뉴스 결과 예시 메시지 작성
    news_text = "📰 <b>[실시간 주요 뉴스 알림]</b>\n\n"
    news_text += "• <a href='https://news.naver.com'>[네이버뉴스] AI 및 반도체 시장 최신 동향</a>\n"
    news_text += "• <a href='https://www.fnnews.com'>[파이낸셜뉴스] 증권 및 금융 시장 관련 소식</a>\n"
    
    return news_text

def main():
    print("🚀 뉴스 크롤러 및 텔레그램 발송 로봇 시작!")
    
    # 뉴스 수집
    message = fetch_news()
    
    # 텔레그램 발송 실행
    success = send_telegram_msg(message)
    
    if success:
        print("🎉 성공적으로 텔레그램 메시지를 발송했습니다!")
    else:
        print("⚠️ 텔레그램 발송 실패 - 위의 '텔레그램 응답 상세 내용'을 확인하세요.")

if __name__ == "__main__":
    main()
