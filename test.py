from dotenv import load_dotenv
from pymongo import MongoClient
import json
import os
import datetime

load_dotenv()
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")


client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/")
db = client["testDB"]

with open("example_data.json") as f:
    data = json.load(f)

for db_name, systems in data.items():
    for collection_name, values in systems.items():
        for value in values:
            value["timestamp"] = datetime.datetime.now(tz=datetime.timezone.utc)
        client[db_name][collection_name].insert_many(values)
