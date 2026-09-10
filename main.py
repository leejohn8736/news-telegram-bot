import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

# 1. 깃허브 Secrets에서 텔레그램 정보 가져오기
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. 감시할 키워드 목록 (10개)
KEYWORDS = ["삼성전자", "AI", "반도체", "증권", "부동산", "금리", "주식", "현대차", "SK하이닉스", "배터리"]

# 이미 발송한 기사 링크 저장 파일
SENT_LINKS_FILE = "sent_links.txt"

def load_sent_links():
    """발송된 기사 링크 목록 불러오기"""
    if os.path.exists(SENT_LINKS_FILE):
        with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_links(sent_links):
    """발송된 기사 링크 저장하기"""
    with open(SENT_LINKS_FILE, "w", encoding="utf-8") as f:
        for link in sent_links:
            f.write(f"{link}\n")

def send_telegram_msg(text):
    """메시지 1개당 기사 1건 개별 발송 함수"""
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

def fetch_rss_news(keyword):
    """구글 뉴스 RSS에서 키워드가 제목에 들어간 최신 기사 수집"""
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    articles = []
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
            
            # 간단 XML 파싱 (item 단위)
            items = xml_data.split('<item>')
            for item in items[1:]:
                # 제목 추출
                title = ""
                if '<title>' in item and '</title>' in item:
                    title = item.split('<title>')[1].split('</title>')[0]
                    title = title.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # 링크 추출
                link = ""
                if '<link>' in item and '</link>' in item:
                    link = item.split('<link>')[1].split('</link>')[0].strip()
                
                # 발행 시간 추출
                pub_date_str = ""
                if '<pubDate>' in item and '</pubDate>' in item:
                    pub_date_str = item.split('<pubDate>')[1].split('</pubDate>')[0].strip()
                
                # 언론사/출처 추출
                source = "언론사 미상"
                if '<source' in item and '</source>' in item:
                    source = item.split('>')[1].split('</source>')[0].strip()

                # 조건 1: 제목에 감시 키워드가 반드시 포함되어야 함
                if keyword in title and link:
                    articles.append({
                        'keyword': keyword,
                        'title': title,
                        'link': link,
                        'source': source,
                        'pub_date': pub_date_str
                    })
    except Exception as e:
        print(f"❌ [{keyword}] 뉴스 수집 실패: {e}")
        
    return articles

def format_date_now():
    """한국 표준시(KST) 기준 날짜/시간 생성"""
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def main():
    print("🚀 조건별 개별 뉴스 감시 로봇 실행...")
    sent_links = load_sent_links()
    new_sent_count = 0
    
    # 10개 키워드 순회하며 신규 뉴스 수집
    for keyword in KEYWORDS:
        articles = fetch_rss_news(keyword)
        
        for article in articles:
            link = article['link']
            
            # 조건 2: 이미 발송한 중복 기사는 제외 (자주 오지 않도록 방지)
            if link in sent_links:
                continue
            
            # 조건 3: 한 메시지에 한 기사만 서식에 맞추어 작성
            message = (
                f"📰 <b>[{article['keyword']}] 관련 신규 기사</b>\n\n"
                f"<b>제목:</b> {article['title']}\n"
                f"<b>언론사/기자:</b> {article['source']}\n"
                f"<b>수집 시간:</b> {format_date_now()}\n\n"
                f"🔗 <a href='{article['link']}'>기사 바로가기</a>"
            )
            
            # 텔레그램으로 1건씩 개별 발송
            if send_telegram_msg(message):
                sent_links.add(link)
                new_sent_count += 1
                print(f"✅ 발송 성공: {article['title']}")
    
    # 새로운 발송 기록 저장
    save_sent_links(sent_links)
    print(f"🎉 총 {new_sent_count}건의 신규 기사를 개별 발송했습니다.")

if __name__ == "__main__":
    main()
