import nextcord
from nextcord.ext import commands
import requests
import base64
from datetime import datetime
import pytz
import re
from lxml import etree
from html import escape


def format_content(text):
    # 각 제목을 찾기 위한 정규 표현식
    title_pattern = r'\[(.*?)\]|^(?!- ).*$'
    # li 태그로 감싸는 정규 표현식
    item_pattern = r'-(.*?\.)'

    # 각 제목과 내용을 분리하고, 내용을 '-'로 시작하는 부분을 처리
    text_lines = text.split('\n')
    formatted_text = ""
    current_title = None

    for line in text_lines:
        match = re.match(title_pattern, line)
        if line == '':
            continue

        if match:
            title = match.group(0)

            # 제목이 발견되면, 이전 제목과 내용을 처리하고 새로운 제목을 시작합니다.
            if current_title:
                formatted_text += f'</ul>\n</div>\n'

            # 제목을 div 태그로 감싸고, 내용을 ul 태그로 감싸는 HTML 코드 생성
            formatted_text += f'<div class="patch-note">\n<h3>{escape(title)}</h3>\n<ul>\n'
            current_title = title

        else:
            # 각 줄별로 내용을 '-'로 시작하는 부분을 처리
            match = re.match(item_pattern, line)
            if match:
                formatted_text += f'<li>{escape(match.string[2:])}</li>\n'

    # 마지막 제목과 내용까지 처리
    if current_title:
        formatted_text += f'</ul>\n</div>'

    return formatted_text


def convert_html_entities_to_symbols(html_string):
    # &lt;를 <로, &gt;를 >로 변환
    converted_string = html_string.replace("&lt;", "<").replace("&gt;", ">")
    return converted_string


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
    if response.status_code == 200:
        content_encoded = response.json()["content"]
        content = base64.b64decode(content_encoded).decode("utf-8")
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
            korea_tz = pytz.timezone('Asia/Seoul')
            creation_date_korea = creation_date.astimezone(korea_tz)

            thread_link = thread.jump_url
            author_name = first_message[0].author.display_name
            if author_name == "minho4979":
                author_name = "크작가"
            elif author_name == "dyseo04":
                author_name = "비유"

            message_content = first_message[0].content
            images = []
            for attachment in first_message[0].attachments:
                if attachment.filename.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    images.append(attachment.url.replace('&', '&amp;'))

            print(f"새로운 패치노트가 작성되었습니다")
            print(f"Title: {thread_title}")
            print(
                f"Date: {creation_date_korea.strftime('%a, %d %b %Y %H:%M:%S %z')}"
            )
            print(f"Link: {thread_link}")
            print(f"Name: {author_name}")
            print(f"Content: {message_content}")
            print(f"Images: {images}")

            with open("rss.rss", "r", encoding="utf-8") as file:
                lines = file.readlines()
                guid_line_index = next((i for i, line in enumerate(lines)
                                        if '<!-- last-guid:' in line), 4)
                guid = lines[guid_line_index][18:19]
                guid = int(guid) + 1
                lines[guid_line_index] = f"  <!-- last-guid: {guid}  -->"

            new_item = f"\n<item>\n"
            new_item += f"<title>{thread_title}</title>\n"

            if creation_date.tzinfo is None or creation_date.tzinfo.utcoffset(
                    creation_date) is not None:
                creation_date = creation_date.replace(tzinfo=pytz.UTC)
            new_item += f"<pubDate>{creation_date_korea.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>\n"
            new_item += f"<link>{thread_link}</link>\n"
            new_item += f'<guid isPermaLink="false">{guid}</guid>\n'
            new_item += f"<dc:creator>{author_name}</dc:creator>\n"

            contents = format_content(message_content)
            contents += f"{' '.join([f'<img src=\'{url}\'/>' for url in images])}"
            new_item += f"<content:encoded>{contents}</content:encoded>\n"
            new_item += f"</item>\n"
            new_item += f"<!-- 각 기사 구분 줄 ========================================================================================================================================================================================================== -->\n\n"
            lines[20] += new_item
            with open("rss.rss", "w", encoding="utf-8") as file:
                file.writelines(lines)

            with open("rss.rss", "r", encoding="utf-8") as file:
                content = file.read()
            content_encoded = base64.b64encode(content.encode()).decode()
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
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
                "sha": sha,
            }
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                print("File uploaded successfully.")
            else:
                print(
                    f"Failed to upload file. Status code: {response.status_code}"
                )


# TODO 스레드 수정이 제대로 인식되지 않음 추후 수정 필요

# @bot.event
# async def on_thread_update(before, after):
#     if '패치노트' in before.name and '패치노트' in after.name:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             content_encoded = response.json()["content"]
#             content = base64.b64decode(content_encoded).decode("utf-8")
#             with open("rss.rss", "w", encoding="utf-8") as file:
#                 file.write(content)
#             print("File downloaded successfully.")
#         else:
#             print(
#                 f"Failed to download file. Status code: {response.status_code}"
#             )

#         if before.jump_url == after.jump_url:

#             first_message = await after.history(limit=1).flatten()
#             after_message = first_message[0].content
#             after_contents = format_content(after_message)
#             print(f"패치노트가 수정되었습니다")
#             print(f"Content: {after_message}")

#             # XML 데이터 읽기
#             tree = etree.parse("rss.rss")
#             root = tree.getroot()

#             # content:encoded 태그 찾기
#             content_encoded = root.find(
#                 './/{http://purl.org/rss/1.0/modules/content/}encoded')
#             img = root.find('.//img')

#             # content:encoded 태그 삭제
#             if content_encoded is not None:
#                 parent_node = content_encoded.getparent()
#                 parent_node.remove(content_encoded)

#                 # 새로운 태그 추가
#                 new_tag = etree.SubElement(
#                     parent_node,
#                     '{http://purl.org/rss/1.0/modules/content/}encoded')

#                 # 예시: after_contents에 있는 <와 > 문자를 lt, gt로 변환
#                 after_contents_with_lt_gt = re.sub(
#                     r'(<|>)', lambda m: '&' + {
#                         '<': 'lt;',
#                         '>': 'gt;'
#                     }.get(m.group(), m.group()), after_contents)

#                 # lt, gt를 <, >로 변환
#                 after_contents_with_correct_tags = convert_html_entities_to_symbols(
#                     after_contents_with_lt_gt)

#                 # 이제 after_contents_with_correct_tags를 new_tag.text에 할당할 수 있습니다.
#                 new_tag.text = f"{after_contents_with_correct_tags}"

#                 # img 태그가 존재하는 경우만 처리
#                 if img is not None and img.getparent() == parent_node:
#                     img_tag_string = etree.tostring(img).decode('utf-8')
#                     parent_node.remove(img)
#                     parent_node.append(etree.fromstring(img_tag_string))

#             # 수정된 XML 저장
#             tree.write("rss.rss", pretty_print=False, encoding='utf-8')

#         else:
#             print("xml edit failed")

#         with open("rss.rss", "r", encoding="utf-8") as file:
#             content = file.read()
#         content_encoded = base64.b64encode(content.encode()).decode()
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             data = response.json()
#             sha = data["sha"]
#             print(f"SHA: {sha}")
#         else:
#             print("파일 정보를 가져오는 데 실패했습니다.")
#         data = {
#             "owner": "djl987645",
#             "repo": "MineSquare-Launcher-Bot",
#             "message": "Upload rss.rss file",
#             "path": "rss.rss",
#             "content": content_encoded,
#             "committer": {
#                 "name": "djl987645",
#                 "email": "djl987645@gmail.com"
#             },
#             "branch": "main",
#             "sha": sha,
#         }
#         response = requests.put(url, headers=headers, json=data)
#         if response.status_code == 200:
#             print("File uploaded successfully.")
#         else:
#             print(
#                 f"Failed to upload file. Status code: {response.status_code}")

# 봇을 실행합니다.
bot.run(TOKEN)
