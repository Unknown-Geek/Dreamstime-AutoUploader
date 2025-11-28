from dotenv import load_dotenv
import os

load_dotenv()
print(f"Username: '{os.getenv('DREAMSTIME_USERNAME')}'")
print(f"Password: '{os.getenv('DREAMSTIME_PASSWORD')}'")
