import datetime

def log(message):
    current_date = datetime.datetime.now().strftime("%d_%m_%Y")
    with open(f"log/system_log_{current_date}.txt", "a") as f:
        f.write(f'{datetime.datetime.now()} {message}\n')