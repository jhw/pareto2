import base64, gzip, json, os, urllib.request

# https://colorswall.com/palette/3

Levels={"info":  "#5bc0de",
        "warning": "#f0ad4e",
        "error": "#d9534f"}

def post_webhook(struct, url):
    req = urllib.request.Request(url, method = "POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(struct).encode()
    return urllib.request.urlopen(req, data = data).read()

def handler(event, context = None,
            colour = Levels[os.environ["SLACK_LOGGING_LEVEL"]],
            webhookurl = os.environ["SLACK_WEBHOOK_URL"]):
    struct = json.loads(gzip.decompress(base64.b64decode(event["awslogs"]["data"])))
    text = json.dumps(struct)
    struct = {"attachments": [{"text": text,
                               "color": colour}]}
    post_webhook(struct, webhookurl)
