from _datetime import datetime


def get_timestamp() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return timestamp


def extract_llm_messages(messages: list) -> list:
    messages = [message for message in messages if message['role'] in ['system', 'assistant', 'user', 'tool']]
    return messages