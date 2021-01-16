from notion.block import TextBlock
from notion.client import NotionClient
import os
from os import environ
from pathlib import Path
from flask import Flask
import slack
from slackeventsapi import SlackEventAdapter

# from dotenv import load_dotenv

# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path)

notionUrls = {
    "post": "https://www.notion.so/prsmlab/2057ce5fa809459684ca8e51c4b6d461?v=c05502589aa34e10bb3004318c84916c",
    "link": "https://www.notion.so/prsmlab/83b8a8e236cc48e0a5aefba419730411?v=00b41d9014234f5d80b4bb92b88ac5cd",
}
allowedSlackChannels = {
    "material": "C01F9G7KL07"
    # , "experiment": "C01ETM1P4BH"
}
notionPostProps = ["authored", "slack_url", "related_links", "ireum"]
notionLinkProps = [
    "translation",
    "tags",
    "update_logs",
    "related_posts",
    "author",
    "last_updated",
    "url",
    "authored",
    "ireum",
]
notionClient = NotionClient(token_v2=environ["NOTION_TOKEN"])
postCollection = notionClient.get_collection_view(notionUrls["post"])
linkCollection = notionClient.get_collection_view(notionUrls["link"])

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(environ["SIGNING_SECRET"], "/slack/events", app)

slackClient = slack.WebClient(token=environ["SLACK_TOKEN"])

ignoreList = []


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event")
    if "subtype" in event:
        if event.get("subtype") == "message_changed":
            message = event.get("message")
            client_msg_id = message.get("client_msg_id")
            if client_msg_id not in ignoreList:
                ignoreList.append(client_msg_id)
                if len(ignoreList) > 1024:
                    ignoreList.pop(0)
                print(event)
                channel = event.get("channel")
                if channel in allowedSlackChannels.values():
                    postContentsCnt = 0
                    postContents = str(message.get("text")).split("\n")
                    newPostRow = postCollection.collection.add_row()
                    for postContent in postContents:
                        if postContent != "":
                            postText = newPostRow.children.add_new(TextBlock)
                            postText.title = postContent
                            postContentsCnt += 1
                            if postContentsCnt == 1:
                                newPostRow.ireum = postContent
                    permalink = slackClient.chat_getPermalink(
                        channel=channel, message_ts=message.get("ts")
                    )
                    if permalink.get("ok"):
                        newPostRow.slack_url = str(permalink.get("permalink"))
                    postId = newPostRow.id
                    linkIds = []
                    attachments = message.get("attachments")
                    for atchItem in attachments:
                        newLinkRow = linkCollection.collection.add_row()
                        newLinkRow.translation = "번역없음"
                        newLinkRow.slack_message = [postId]
                        if "author_name" in atchItem:
                            newLinkRow.author = str(atchItem.get("author_name"))
                        if "original_url" in atchItem:
                            newLinkRow.url = str(atchItem.get("original_url"))
                        if "title" in atchItem:
                            newLinkRow.ireum = str(atchItem.get("title"))
                        if "service_icon" in atchItem:
                            newLinkRow.set(
                                "format.page_icon", str(atchItem.get("service_icon"))
                            )
                        if "image_url" in atchItem:
                            newLinkRow.set(
                                "format.page_cover", str(atchItem.get("image_url"))
                            )
                        elif "thumb_url" in atchItem:
                            newLinkRow.set(
                                "format.page_cover", str(atchItem.get("thumb_url"))
                            )
                        elif "service_icon" in atchItem:
                            newLinkRow.set(
                                "format.page_cover", str(atchItem.get("service_icon"))
                            )
                        if "text" in atchItem:
                            linkContents = str(atchItem.get("text")).split("\n")
                            for linkContent in linkContents:
                                if linkContent != "":
                                    linkText = newLinkRow.children.add_new(TextBlock)
                                    linkText.title = linkContent
                        linkIds.append(newLinkRow.id)
                    newPostRow.related_links = linkIds


if __name__ == "__main__":
    app.run(debug=True)