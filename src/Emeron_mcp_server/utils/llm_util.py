from openai import OpenAI


def call_openai_sdk(**args):
    key = args['key']
    base_url = args['url']
    client = OpenAI(
        api_key=key,
        base_url=base_url,
    )
    del args['key']
    del args['url']
    completion = client.chat.completions.create(
        **args
    )
    return completion

