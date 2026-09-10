import os
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from curl_cffi import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DB_FILE = "sent_links.txt"

def load_sent_links():
    """이미 발송한 뉴스 링크 읽어오기"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_links(sent_links):
    """발송 완료된 뉴스 링크 저장하기 (최대 500개 유지)"""
    links_list = list(sent_links)[-500:]
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for link in links_list:
            f.write(f"{link}\n")

def send_telegram_msg(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정 오류")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"텔레그램 발송 오류: {e}")

def get_rss_news(rss_url, sent_links, max_items=5):
    """새로운 기사만 추출"""
    new_articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(rss_url, impersonate="chrome120", headers=headers, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            for item in items[:max_items]:
                title = item.findtext("title")
                link = item.findtext("link")
                
                if title and link:
                    title = title.strip()
                    link = link.strip()
                    # 이전에 보내지 않은 '새로운 뉴스'만 수집
                    if link not in sent_links:
                        new_articles.append((title, link))
                        sent_links.add(link)
    except Exception as e:
        print(f"RSS 오류 ({rss_url}): {e}")
        
    return new_articles

def main():
    sent_links = load_sent_links()
    
    keywords = [
        "삼성전자", "한국항공우주", "구리", "AI", "데이타 센터",
        "데이터 센터", "스타트업", "주식", "반도체", "로봇"
    ]

    full_message = ""
    total_new_count = 0

    # 1. 키워드 검색 뉴스
    for kw in keywords:
        encoded_kw = urllib.parse.quote(kw)
        google_url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=ko&gl=KR&ceid=KR:ko"
        articles = get_rss_news(google_url, sent_links)
        
        if articles:
            full_message += f"⚡ <b>[속보/뉴스: {kw}]</b>\n"
            for title, link in articles:
                full_message += f"🔹 {title}\n🔗 {link}\n\n"
                total_new_count += 1

    # 2. 파이낸셜뉴스 전체
    fn_url = "http://www.fnnews.com/rss/r20/fn_realnews_all.xml"
    fn_articles = get_rss_news(fn_url, sent_links)
    if fn_articles:
        full_message += "⚡ <b>[파이낸셜뉴스]</b>\n"
        for title, link in fn_articles:
            full_message += f"🔹 {title}\n🔗 {link}\n\n"
            total_new_count += 1

    # 3. 네이버 뉴스 (AI)
    naver_kw = urllib.parse.quote("AI")
    naver_url = f"https://news.google.com/rss/search?q={naver_kw}+site:news.naver.com&hl=ko&gl=KR&ceid=KR:ko"
    naver_articles = get_rss_news(naver_url, sent_links)
    if naver_articles:
        full_message += "⚡ <b>[네이버 뉴스 - AI]</b>\n"
        for title, link in naver_articles:
            full_message += f"🔹 {title}\n🔗 {link}\n\n"
            total_new_count += 1

    # 새로운 기사가 있을 때만 전송
    if total_new_count > 0:
        send_telegram_msg(full_message)
        save_sent_links(sent_links)
        print(f"🎉 신규 기사 {total_new_count}건 발송 완료!")
    else:
        print("💡 새로운 신규 기사가 없습니다.")

if __name__ == "__main__":
    main()
