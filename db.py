from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["bluestudy"]
tasks_collection = db["tasks"]
users_collection = db["users"]
flashcards_collection = db["flashcards"]
