import json
from slackclient import SlackClient
from flask import Flask, request, make_response
import requests
from bs4 import BeautifulSoup
import os
import time

app = Flask(__name__)

slack_token = "xoxb-506062083639-507944158225-gE7Z5YCH0f8lkuoyCWkyy4rt"
slack_client_id = "506062083639.509599120647"
slack_client_secret = "2b5b34f8a307be4bf8a593c83f055053"
slack_verification = "8eXvLzsy6z874viGB1HLdMGc"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    # 파일의 위치
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    req = requests.get('https://www.dogdrip.net/dogdrip')
    req.encoding = 'utf-8'
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    posts = soup.find_all("span", class_="ed title-link")
    output = []
    before_last_txt = []
    after_last_txt = []

    with open(os.path.join(BASE_DIR, 'lastest.txt'), 'r+', encoding='UTF8') as file:
        for line in file:
            before_last_txt = line
    # before_last_txt : 이전에 크롤링해서 만들어낸 최신자료의 제목이 들어가 있는 리스트
    #print("이전 데이터")
    #print(before_last_txt)

    after_last_txt.append(posts[0].get_text())
    with open(os.path.join(BASE_DIR, 'lastest.txt'), 'w+', encoding='UTF8') as file:
        file.write(str(after_last_txt))

    # after_last_txt : 새로 크롤링해서 만들어낸 최신자료의 제목이 들어가 있는 리스트
    if before_last_txt != str(after_last_txt):
        # 같은 경우는 에러 없이 넘기고, 다른 경우에만
        # 메시지 보내는 로직을 넣으면 됩니다.
        #print("새로 가져온 데이터")

        #도메인 크롤링을위한 작업

        domains = soup.find_all("td", class_="title")
        title = str(after_last_txt[0])
        domain = domains[0].find("a")["href"]

        #
        
        #hit 변수담기

        hit = int(soup.find("td", class_="ed voteNum text-primary").get_text())


        #Hit의 강조를 표현하기위한 코드

        if hit <= 10:
            color_code = "#FFFF36"
        elif 10 < hit <= 30:
            color_code = "#FF9436"
        else:
            color_code = "#FF0000"

        #

        #이미지 URL를 가져오는 부분

        new_req = requests.get(domain)
        new_req.encoding = 'utf-8'
        new_html = new_req.text
        new_soup = BeautifulSoup(new_html, 'html.parser')
        new_posts = new_soup.find("div", class_="ed clearfix margin-vertical-large")

        img = new_posts.find("img")  # 이미지 태그
        img_src = img.get("src")  # 이미지 경로
        img_name = img_src.replace("/", "")  # 이미지 src에서 / 없애기
        img_url = "http://www.dogdrip.net/" + img_src  # 다운로드를 위해 base_url과 합침
        print(img_url)

        #
        #형식을 맞추기위한 변수

        out = ''

        #
        return u'\n'.join(out), title , domain, img_url, color_code
    else:
        out = ''
        title = 'None'
        return u'\n'.join(out), title, title, title, title
    file.close()


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):

    print(slack_event["event"])
    i=0
    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]


        #각자 담겨있는 변수 들을 가져온다
        keywords, title, domain, img_url, color_code = _crawl_naver_keywords(text)

        if ( title != "None"):
            sc.api_call(
                 "chat.postMessage",
                 channel=channel,
                 text=keywords,

                 attachments= [
                    {
                    "fallback": "Required plain-text summary of the attachment.",
                     "color": color_code,
                     "pretext": "새글 들어왔다 눈떠라",
                     "title": title,
                     "title_link" : domain,
                     "image_url": img_url,
                    }
                ]

                )

        return make_response("App mention message has been sent", 200, )

    #

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    clock = 0
    while True:
        if "event" in slack_event:
            event_type = slack_event["event"]["type"]
            _event_handler(event_type, slack_event)
            time.sleep(60)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
