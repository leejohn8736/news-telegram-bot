import os
import sys
import json
import time
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

# 1. Secrets에서 텔레그램 정보 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. 감시할 키워드 목록 (10개)
KEYWORDS = ["삼성전자", "AI", "반도체", "증권", "부동산", "금리", "주식", "현대차", "SK하이닉스", "배터리"]

# 중복 방지 파일
SENT_LINKS_FILE = "sent_links.txt"

def load_sent_links():
    if os.path.exists(SENT_LINKS_FILE):
        with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_links(sent_links):
    with open(SENT_LINKS_FILE, "w", encoding="utf-8") as f:
        for link in sent_links:
            f.write(f"{link}\n")

def send_telegram_msg(text):
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
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"❌ 텔레그램 전송 실패 (HTTP {e.code}): {err_body}")
        return False
    except Exception as e:
        print(f"❌ 텔레그램 발송 오류: {e}")
        return False

def fetch_rss_news(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    articles = []
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
            
            items = xml_data.split('<item>')
            for item in items[1:]:
                title = ""
                if '<title>' in item and '</title>' in item:
                    title = item.split('<title>')[1].split('</title>')[0]
                    title = title.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                link = ""
                if '<link>' in item and '</link>' in item:
                    link = item.split('<link>')[1].split('</link>')[0].strip()
                
                source = "언론사 미상"
                if '<source' in item and '</source>' in item:
                    source = item.split('>')[1].split('</source>')[0].strip()

                if keyword in title and link:
                    articles.append({
                        'keyword': keyword,
                        'title': title,
                        'link': link,
                        'source': source
                    })
    except Exception as e:
        print(f"❌ [{keyword}] 뉴스 수집 실패: {e}")
        
    return articles

def format_date_now():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def main():
    print("🚀 뉴스 감시 및 텔레그램 발송 로봇 실행...")
    sent_links = load_sent_links()
    new_sent_count = 0
    
    for keyword in KEYWORDS:
        articles = fetch_rss_news(keyword)
        
        for article in articles:
            link = article['link']
            
            if link in sent_links:
                continue
            
            # HTML 특수문자 변환 처리 (400 Bad Request 에러 방지 핵심)
            safe_keyword = html.escape(article['keyword'])
            safe_title = html.escape(article['title'])
            safe_source = html.escape(article['source'])
            
            # 메시지 작성
            message = (
                f"📰 <b>[{safe_keyword}] 관련 신규 기사</b>\n\n"
                f"<b>제목:</b> {safe_title}\n"
                f"<b>언론사/출처:</b> {safe_source}\n"
                f"<b>수집 시간:</b> {format_date_now()}\n\n"
                f"🔗 <a href='{link}'>기사 바로가기</a>"
            )
            
            if send_telegram_msg(message):
                sent_links.add(link)
                new_sent_count += 1
                print(f"✅ 발송 성공: {article['title']}")
                time.sleep(0.5)  # 텔레그램 API 부하 방지 대기
            else:
                print(f"❌ 발송 실패: {article['title']}")
    
    save_sent_links(sent_links)
    print(f"🎉 총 {new_sent_count}건의 신규 기사를 발송했습니다.")

if __name__ == "__main__":
    main()
