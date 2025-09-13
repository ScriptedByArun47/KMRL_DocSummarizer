# app/scripts/db.py
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://akisback049:kRQPOcjqInE2t5fT@cluster0.9quv2g9.mongodb.net/")
client = AsyncIOMotorClient(MONGO_URI)
db = client.kmrl_summaries

# collection: summaries
