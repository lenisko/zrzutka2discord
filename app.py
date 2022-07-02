# https://github.com/lenisko
import time
import datetime
import requests

from dotenv import dotenv_values

zrzutka_api_url = "https://zrzutka.pl/api/v1/public/whipRounds/{}/payments"


def get_payments(zrzutka_id, zrzutka_api_key):
    headers = {
        "user-agent": "zrzutka2discord/0.1.0",
        "Authorization": "Bearer " + zrzutka_api_key,
    }
    url = zrzutka_api_url.format(zrzutka_id)
    req = requests.get(url, params={"t": int(time.time())}, headers=headers, timeout=10)
    data = req.json()

    return data


def send_webhook(webhook_url, username, messages):
    def _send_data(output_message):
        message_data = {
            "username": username,
            "content": output_message,
        }
        req = requests.post(
            webhook_url, params={"wait": True}, json=message_data, timeout=10
        )
        req.raise_for_status()

    output_message = ""

    for message in messages[::-1]:
        if len(output_message) + len(message) < 2000:
            output_message += message
        else:
            _send_data(output_message)
            output_message = ""

    if len(output_message):
        _send_data(output_message)


def format_message(input_data, message_format):
    output = message_format.format(**input_data)
    return output


def in_between(start, end):
    now = datetime.datetime.now().hour
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end


if __name__ == "__main__":
    config = dotenv_values(".env")

    last_payment_id = ""
    dnd = list(map(int, config["DND_BETWEEN"].split(" ")))

    while True:
        messages = []

        # dnd check
        if in_between(dnd[0], dnd[1]):
            time.sleep(int(config["SLEEP"]))
            continue

        try:
            payments = get_payments(config["ZRZUTKA_ID"], config["ZRZUTKA_API_KEY"])

            for row in payments["data"]:
                if row["id"] != last_payment_id:
                    output_message = format_message(row, config["WEBHOOK_MESSAGE"])
                    messages.append(output_message)
                    print(f"[Message / {row['id']}] {output_message}")
                else:
                    break

            send_webhook(
                config["DISCORD_WEBHOOK"], config["DISCORD_USERNAME"], messages
            )
            last_payment_id = payments["data"][0]["id"]

        except Exception as e:
            print(f"Error: {e}")
        finally:
            time.sleep(int(config["SLEEP"]))
