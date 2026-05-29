import os
from discord import Intents
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("CAB_BOT_TOKEN")
intents = Intents.default()