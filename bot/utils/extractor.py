def extract_text_from_reply(event: dict, from_reply: bool = None, from_forward: bool = None) -> str:
    if from_reply: return event["object"]["message"]["reply_message"]["text"]
    elif from_forward: return event["object"]["message"]["fwd_messages"][0]["text"]
    return False

def extract_userid_from_reply(event: dict, from_reply: bool = None, from_forward: bool = None) -> int:
    if from_reply: return event["object"]["message"]["reply_message"]["from_id"]
    elif from_forward: return event["object"]["message"]["fwd_messages"][0]["from_id"]
    return False