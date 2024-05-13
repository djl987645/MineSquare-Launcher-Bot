import nextcord
from nextcord.ext import commands
import html
import requests
import base64

TOKEN = "MTIzODQzNjA0NjYzMTQ2OTA2OA.GidIUP.5yvxL3kh_CgY9aASrY5LhnpdeAmGdHvSLznXMo"
CHANNEL_ID = 1239330102160916480
url = "https://api.github.com/repos/djl987645/MineSquare-Launcher-Bot/contents/rss.rss"
token = "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"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}


bot = commands.Bot()
intents = nextcord.Intents.default()
intents.messages = True  # Enable message event


client = nextcord.Client(intents=intents)


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


@bot.event
async def on_thread_create(thread):
    if thread.parent_id == CHANNEL_ID and "패치노트" in thread.name:
        first_message = await thread.history(limit=1).flatten()
        if first_message:
            thread_title = thread.name
            creation_date = thread.created_at
            thread_link = thread.jump_url
            author_name = first_message[0].author.name
            message_content = first_message[0].content
            images = []
            for attachment in first_message[0].attachments:
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    images.append(attachment.url.replace('&', '&amp;'))

            print(
                f"Title: {thread_title}, Date: {creation_date}, Author: {author_name}, Message: {message_content}, Images: {images}"
            )

            with open("rss.rss", "r", encoding="utf-8") as file:
                lines = file.readlines()
                guid = lines[6][19:20]
                guid = int(guid) + 1  # guid를 정수로 변환하고 1을 더합니다.
                lines[6] = f"  <!-- last-guid: {guid}  -->"

            new_item = f"<item>"
            new_item += f"<title>{thread_title}</title>"
            new_item += f"<pubDate>{creation_date.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>"
            new_item += f"<link>{thread_link}</link>"
            new_item += f"<guid isPermaLink=\"false\">{guid}</guid>"
            new_item += f"<dc:creator>{author_name}</dc:creator>"

            def format_content(message_content):
                parts = message_content.split('[')
                if len(parts) < 2:
                    return ''
                else:
                    formatted_parts = []
                    for part in parts[1:]:
                        split_part = part.split(']', 1)  # 최대 1번만 분할
                        if len(split_part) > 1:
                            title = html.escape(split_part[0])
                            content_lines = html.escape(split_part[1]).split('\n')
                            content_formatted = ''.join(f'<li>{line}</li>' for line in content_lines if line.strip() != '')
                            formatted_parts.append(f'<div class="patch-note">\n<h3>[{title}]</h3>\n<ul>\n{content_formatted}\n</ul>\n</div>')
                        else:
                            # ] 문자가 없는 경우, 전체 부분을 내용으로 처리
                            content = html.escape(part)
                            formatted_parts.append(f'<div class="patch-note"><ul><li>[{content}]</li></ul></div>')
                    return ''.join(formatted_parts)

            contents = format_content(message_content)
            contents += f"{' '.join([f'<img src=\'{url}\'/>' for url in images])}"
            new_item += f"<content:encoded>{contents}</content:encoded>"
            new_item += f"</item>"
            new_item += f"<!-- 각 기사 구분 줄 ========================================================================================================================================================================================================== -->"
            lines[20] += new_item

            with open("rss.rss", "w", encoding="utf-8") as file:
                file.writelines(lines)

            with open("rss.rss", "r", encoding="utf-8") as file:
                content = file.read()
            content_encoded = base64.b64encode(content.encode()).decode()
            data = {
                "owner": "djl987645",
                "repo": "MineSquare-Launcher-Bot",
                "message": "Upload rss.rss file",
                "path": "rss.rss",
                "content": content_encoded,
                "committer": {"name": "djl987645", "email": "djl987645@gmail.com"},
                "branch": "main",
                "sha": "23e57b25aadcd132dcf2f2d1fddc415b5b7a4071",  # 업로드할 브랜치 이름
            }
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 201:
                print("File uploaded successfully.")
            else:
                print(f"Failed to upload file. Status code: {response.status_code}")

bot.run(TOKEN)
