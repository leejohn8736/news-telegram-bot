import os
import sys
import json
import time
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# 1. Secrets에서 텔레그램 정보 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. 순환 감시할 키워드 목록 (지정하신 순서)
KEYWORDS = [
    "삼성전자",
    "AI",
    "반도체",
    "증권",
    "부동산",
    "금리",
    "주식",
    "현대차",
    "SK하이닉스",
    "배터리"
]

SENT_LINKS_FILE = "sent_links.txt"
LAST_INDEX_FILE = "last_keyword_index.txt"  # 마지막 발송 키워드 순번 저장 파일

def load_sent_links():
    if os.path.exists(SENT_LINKS_FILE):
        with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_links(sent_links):
    with open(SENT_LINKS_FILE, "w", encoding="utf-8") as f:
        for link in sent_links:
            f.write(f"{link}\n")

def load_last_index():
    """마지막으로 발송 성공했던 키워드 인덱스 불러오기"""
    if os.path.exists(LAST_INDEX_FILE):
        try:
            with open(LAST_INDEX_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except ValueError:
            return 0
    return 0

def save_last_index(index):
    """마지막으로 발송 성공한 키워드 인덱스 저장하기"""
    with open(LAST_INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(index))

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
    except Exception as e:
        print(f"❌ 텔레그램 발송 오류: {e}")
        return False

def get_kst_today_str():
    """현재 한국 날짜 (YYYY-MM-DD) 반환"""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%d")

def fetch_rss_news(keyword):
    """오늘 작성된 뉴스만 골라내는 크롤러"""
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    articles = []
    kst = timezone(timedelta(hours=9))
    today_kst_str = get_kst_today_str()
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
            items = xml_data.split('<item>')
            
            for item in items[1:]:
                pub_date_str = ""
                if '<pubDate>' in item and '</pubDate>' in item:
                    pub_date_str = item.split('<pubDate>')[1].split('</pubDate>')[0].strip()
                
                is_today = False
                pub_formatted = ""
                if pub_date_str:
                    try:
                        dt = parsedate_to_datetime(pub_date_str).astimezone(kst)
                        pub_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                        if dt.strftime("%Y-%m-%d") == today_kst_str:
                            is_today = True
                    except Exception:
                        pass
                
                if not is_today:
                    continue

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
                        'source': source,
                        'pub_time': pub_formatted
                    })
    except Exception as e:
        print(f"❌ [{keyword}] 뉴스 수집 실패: {e}")
        
    return articles

def main():
    print("🚀 순환형 당일 뉴스 감시 로봇 실행...")
    sent_links = load_sent_links()
    last_index = load_last_index()
    total_keywords = len(KEYWORDS)
    
    sent_in_this_run = False
    
    # 마지막 발송한 다음 키워드부터 순서대로 검사 (순환 로직)
    for i in range(1, total_keywords + 1):
        target_index = (last_index + i) % total_keywords
        keyword = KEYWORDS[target_index]
        
        articles = fetch_rss_news(keyword)
        
        for article in articles:
            link = article['link']
            if link in sent_links:
                continue
            
            safe_keyword = html.escape(article['keyword'])
            safe_title = html.escape(article['title'])
            safe_source = html.escape(article['source'])
            safe_pub_time = html.escape(article['pub_time'])
            
            message = (
                f"📰 <b>[{safe_keyword}] 당일 신규 뉴스</b>\n\n"
                f"<b>제목:</b> {safe_title}\n"
                f"<b>출처:</b> {safe_source}\n"
                f"<b>발행 시간:</b> {safe_pub_time}\n\n"
                f"🔗 <a href='{link}'>기사 읽기</a>"
            )
            
            if send_telegram_msg(message):
                sent_links.add(link)
                save_sent_links(sent_links)
                # 발송 성공 시 해당 키워드 위치를 저장하여 다음 번에는 그다음 키워드로 넘어가도록 함
                save_last_index(target_index)
                print(f"✅ [{keyword}] 뉴스 발송 성공: {article['title']}")
                sent_in_this_run = True
                break
                
        if sent_in_this_run:
            break
            
    if not sent_in_this_run:
        print("ℹ️ 이번 스케줄에서는 조건에 맞는 새로운 '오늘 자' 뉴스가 없습니다.")

if __name__ == "__main__":
    main()
