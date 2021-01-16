import os
from pathlib import Path
from dotenv import load_dotenv
from notion.client import NotionClient

postUrl = "https://www.notion.so/prsmlab/2057ce5fa809459684ca8e51c4b6d461?v=c05502589aa34e10bb3004318c84916c"

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
notionClient = NotionClient(token_v2=os.environ["NOTION_TOKEN"])

postCollection = notionClient.get_collection_view(os.environ["POST_URL"])
postRows = postCollection.collection.get_rows()
print("postItem keys:")
print(list(postRows[0].get_all_properties().keys()))

linkCollection = notionClient.get_collection_view(os.environ["LINK_URL"])
linkRows = linkCollection.collection.get_rows()
print("linkItem keys:")
print(list(linkRows[0].get_all_properties().keys()))