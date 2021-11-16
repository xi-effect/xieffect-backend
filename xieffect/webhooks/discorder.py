from discord_webhook import DiscordWebhook
from requests import post, Response

from componets import TypeEnum

"""
https://discordapp.com/developers/docs/resources/webhook#execute-webhook
https://discordapp.com/developers/docs/resources/channel#embed-object

data = {"content": "message content", "username": "custom username", "embeds": []}
result: Response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
"""


class WebhookURLs(TypeEnum):
    STATUS = "843500826223312936/9ZcT7YinTBn4g0hdwPL_ca-YszwRUYrNrLhVEPjDrZQw_lMWHeo7l5LNtl6rq4LAUhgv"
    ERRORS = "843536959624445984/-V9-tEd9Af2mz-0L18YQqlabtK4rJatCSs0YS0XUFh-Tl-s49e2DG1Jg0z3wG2Soo0Op"
    WEIRDO = "843431829931556864/XY-k_4IOZ9NVatCuPEYB8OU6_DPSfUBP_lvGROf55g8GTM6TbDarcvLIJiz5KvGOZZZD"
    GITHUB = "854307355347779614/T5F80VykQKj4-5bwgriePYXWpkIDxpP84KMZ5rohRuLOwrsJcyLvchy3pkXwnV0_QNeJ"
    NOTIF = "854307934233952266/efeU2EMEJvEad9mw45bJscKdX_vMVJE5xYRknfo7bP_BTli_xX7_ubJJBJMjYqKnSHEx"
    HEROKU = "899768347405729892/_-roOKd49JDjD0tPRbY6b0zon469e_KByPL7bakMTBlbEdPxTL0PtqLlIY0fna1B_w3Z"
    NETLIF = "903386251112120360/7WcUs86qDZkjp59PgWQUrbXpFK7ABrNTBc1P1Jopf05BNi05VhoW06oGDrjHAAtdSp3R"


def send_message(webhook_url: WebhookURLs, message: str) -> Response:
    return post(f"https://discord.com/api/webhooks/{webhook_url.value}", json={"content": message})


def send_file_message(webhook_url: WebhookURLs, file_content: str,
                      file_name: str, message: str) -> Response:
    webhook = DiscordWebhook(url=f"https://discord.com/api/webhooks/{webhook_url.value}")
    webhook.add_file(file=file_content, filename=file_name)
    webhook.set_content(message)
    return webhook.execute()
