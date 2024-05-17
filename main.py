import nextcord
from nextcord.ext import commands
import html
import requests
import base64
from datetime import datetime
import pytz

# 봇 토큰을 읽어옵니다.
TOKEN = open("token", "r").readline()

# 채널 ID를 설정합니다.
CHANNEL_ID = 1233436867844898856

# GitHub API URL을 설정합니다.
url = "https://api.github.com/repos/djl987645/MineSquare-Launcher-Bot/contents/rss.rss"

# GitHub API 인증을 위한 토큰을 읽어옵니다.
token = open("token", "r").readlines()[1].strip()

# GitHub API 요청 헤더를 설정합니다.
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

# 봇 객체를 생성합니다.
bot = commands.Bot()

# 디스코드 인텐트를 설정합니다.
intents = nextcord.Intents.default()
intents.messages = True  # 메시지 이벤트를 활성화합니다.

# 클라이언트 객체를 생성합니다.
client = nextcord.Client(intents=intents)


# 봇이 준비되었을 때 실행되는 함수입니다.
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    response = requests.get(url, headers=headers)
    # 응답을 확인합니다.
    if response.status_code == 200:
        # 파일 내용을 디코딩합니다.
        content_encoded = response.json()["content"]
        content = base64.b64decode(content_encoded).decode("utf-8")

        # 디코딩된 내용을 파일에 쓰기
        with open("rss.rss", "w", encoding="utf-8") as file:
            file.write(content)

        print("File downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


# 스레드가 생성되었을 때 실행되는 함수입니다.
@bot.event
async def on_thread_create(thread):
    if thread.parent_id == CHANNEL_ID and "패치노트" in thread.name:
        first_message = await thread.history(limit=1).flatten()
        if first_message:
            # 스레드의 제목을 가져옵니다.
            thread_title = thread.name
            # 스레드 생성 날짜를 가져옵니다.
            creation_date = thread.created_at
            # 스레드 링크를 가져옵니다.
            thread_link = thread.jump_url
            # 첫 번째 메시지 작성자의 이름을 가져옵니다.
            author_name = first_message[0].author.display_name
            # 첫 번째 메시지의 내용을 가져옵니다.
            message_content = first_message[0].content
            # 첨부 파일 목록을 초기화합니다.
            images = []
            for attachment in first_message[0].attachments:
                # 이미지 파일인지 확인합니다.
                if attachment.filename.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    # 이미지 URL을 추가합니다.
                    images.append(attachment.url.replace('&', '&amp;'))

            # 스레드 정보를 출력합니다.
            print(
                f"Title: {thread_title}, Date: {creation_date}, Author: {author_name}, Message: {message_content}, Images: {images}"
            )

            # RSS 파일을 엽니다.
            with open("rss.rss", "r", encoding="utf-8") as file:
                lines = file.readlines()
                # 기존 guid 값을 가져와서 1을 더합니다.
                guid = lines[6][18:19]
                guid = int(guid) + 1  # guid를 정수로 변환하고 1을 더합니다.
                # 새로운 guid 값을 설정합니다.
                lines[6] = f"  <!-- last-guid: {guid}  -->"

            # 새로운 RSS 아이템을 생성합니다.
            new_item = f"<item>\n"
            new_item += f"<title>{thread_title}</title>\n"

            # creation_date가 UTC가 아닌 경우, UTC로 변환
            if creation_date.tzinfo is None or creation_date.tzinfo.utcoffset(
                    creation_date) is not None:
                creation_date = creation_date.replace(tzinfo=pytz.UTC)
            # UTC+9 시간대로 변환
            korea_tz = pytz.timezone('Asia/Seoul')
            creation_date_korea = creation_date.astimezone(korea_tz)
            new_item += f"<pubDate>{creation_date_korea.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>\n"

            new_item += f"<link>{thread_link}</link>\n"
            new_item += f'<guid isPermaLink="false">{guid}</guid>\n'
            new_item += f"<dc:creator>{author_name}</dc:creator>\n"

            # 메시지 내용을 형식화하는 함수입니다.
            def format_content(message_content):
                parts = message_content.split('[')
                if len(parts) < 2:
                    return ''
                else:
                    formatted_parts = []
                    for part in parts[1:]:
                        split_part = part.split(']', 1)  # 최대 1번만 분할
                        if len(split_part) > 1:
                            # 분리된 부분을 HTML로 이스케이프합니다.
                            title = html.escape(split_part[0])
                            content_lines = html.escape(
                                split_part[1]).split('\n')
                            content_formatted = ''.join(
                                f'<li>{line}</li>' for line in content_lines
                                if line.strip() != '')
                            formatted_parts.append(
                                f'<div class="patch-note">\n<h3>[{title}]</h3>\n<ul>\n{content_formatted}\n</ul>\n</div>'
                            )
                        else:
                            # ] 문자가 없는 경우, 전체 부분을 내용으로 처리
                            content = html.escape(part)
                            formatted_parts.append(
                                f'<div class="patch-note"><ul><li>[{content}]</li></ul></div>'
                            )
                    return ''.join(formatted_parts)

            # 내용을 형식화합니다.
            contents = format_content(message_content)
            # 이미지 URL을 추가합니다.
            contents += f"{' '.join([f'<img src=\'{url}\'/>' for url in images])}"
            new_item += f"<content:encoded>{contents}</content:encoded>"
            new_item += f"</item>"
            # 각 기사 구분 줄을 추가합니다.
            new_item += f"<!-- 각 기사 구분 줄 ========================================================================================================================================================================================================== -->\n\n"
            lines[21] += new_item
            # 변경된 내용을 파일에 씁니다.
            with open("rss.rss", "w", encoding="utf-8") as file:
                file.writelines(lines)

            # 파일 내용을 읽어옵니다.
            with open("rss.rss", "r", encoding="utf-8") as file:
                content = file.read()

            # 파일 내용을 base64로 인코딩합니다.
            content_encoded = base64.b64encode(content.encode()).decode()
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # 응답 데이터 JSON으로 파싱
                data = response.json()
                sha = data["sha"]
                print(f"SHA: {sha}")
            else:
                print("파일 정보를 가져오는 데 실패했습니다.")
            data = {
                "owner": "djl987645",
                "repo": "MineSquare-Launcher-Bot",
                "message": "Upload rss.rss file",
                "path": "rss.rss",
                "content": content_encoded,
                "committer": {
                    "name": "djl987645",
                    "email": "djl987645@gmail.com"
                },
                "branch": "main",
                "sha": sha,  # 업로드할 브랜치 이름
            }
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                print("File uploaded successfully.")
            else:
                print(
                    f"Failed to upload file. Status code: {response.status_code}"
                )


# 봇을 실행합니다.
bot.run(TOKEN)
