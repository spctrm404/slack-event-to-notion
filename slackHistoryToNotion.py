from notion.block import TextBlock
from notion.client import NotionClient
import slack
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

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
notionClient = NotionClient(token_v2=os.environ["NOTION_TOKEN"])
postCollection = notionClient.get_collection_view(os.environ["POST_URL"])
linkCollection = notionClient.get_collection_view(os.environ["LINK_URL"])

slackClient = slack.WebClient(token=os.environ["SLACK_TOKEN"])
history = slackClient.conversations_history(channel=os.environ["SLACK_CHANNEL_ID"])
messages = history.get("messages")
reversedMessages = reversed(messages)
cnt = 0
for msgItem in reversedMessages:
    if "subtype" not in msgItem:
        postContentsCnt = 0
        postContents = str(msgItem.get("text")).split("\n")
        newPostRow = postCollection.collection.add_row()
        for postContent in postContents:
            if postContent != "":
                postText = newPostRow.children.add_new(TextBlock)
                postText.title = postContent
                postContentsCnt += 1
                if postContentsCnt == 1:
                    newPostRow.ireum = postContent
        if "ts" in msgItem:
            permalink = slackClient.chat_getPermalink(
                channel=os.environ["SLACK_CHANNEL_ID"], message_ts=msgItem.get("ts")
            )
            if permalink["ok"]:
                newPostRow.slack_url = str(permalink["permalink"]).split("?")[0]
        postId = newPostRow.id
        if "attachments" in msgItem:
            linkIds = []
            attachments = msgItem.get("attachments")
            for atchItem in attachments:
                newLinkRow = linkCollection.collection.add_row()
                newLinkRow.translation = "번역없음"
                newLinkRow.related_posts = [postId]
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
                    newLinkRow.set("format.page_cover", str(atchItem.get("image_url")))
                elif "thumb_url" in atchItem:
                    newLinkRow.set("format.page_cover", str(atchItem.get("thumb_url")))
                elif "service_icon" in atchItem:
                    newLinkRow.set(
                        "format.page_cover", str(atchItem.get("service_icon"))
                    )
                if "text" in atchItem:
                    linkContents = str(atchItem.get("text")).split("\n")
                    for linkContent in linkContents:
                        if linkContents != "":
                            linkText = newLinkRow.children.add_new(TextBlock)
                            linkText.title = linkContent
                linkIds.append(newLinkRow.id)
            newPostRow.related_links = linkIds
        cnt += 1
        print(cnt)