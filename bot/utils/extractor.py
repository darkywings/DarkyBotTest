def extract_text_from_reply(event: dict, from_reply: bool = None, from_forward: bool = None) -> str:
    if from_reply: return event["object"]["message"]["reply_message"]["text"]
    elif from_forward: return event["object"]["message"]["fwd_messages"][0]["text"]
    return False