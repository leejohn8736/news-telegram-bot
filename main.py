name: Realtime News Notification Bot

on:
  workflow_dispatch:
  schedule:
    - cron: '*/20 * * * *'  # 20분마다 실행 (시간당 3회)

jobs:
  run-bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: 파이썬 환경 설정
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 필요 라이브러리 설치
        run: |
          python -m pip install --upgrade pip

      - name: 뉴스 크롤러 실행 및 텔레그램 발송
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python main.py

      - name: 발송 기록 자동 저장 (중복 발송 차단)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add sent_links.txt
          git commit -m "update sent_links [skip ci]" || echo "No changes to commit"
          git push https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}.git HEAD:main
