# -*- coding: UTF-8 -*-
import json
import os
import pandas as pd
import re

def extract_sql_from_qwen(qwen_result) -> str:
    sql = qwen_result
    pattern = r"```sql(.*?)```"

   
    sql_code_snippets = re.findall(pattern, qwen_result, re.DOTALL)

    if len(sql_code_snippets) > 0:
        sql = sql_code_snippets[-1].strip()

    return sql

def read_text(filename)->list:
    data = []
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file.readlines():
            line = line.strip()
            data.append(line)
    return data


def save_raw_text(filename, content):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)


def read_json_file(path, filter_func=None):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
                if filter_func is not None:
                    json_data = list(filter(filter_func, json_data))
                return json_data
            except Exception as e:
                f.seek(0)
                lines = f.readlines()
                json_list = [json.loads(line.strip(
                )) for line in lines if filter_func is None or filter_func(json.loads(line.strip()))]
                return json_list
    else:
        return None


def write_json_to_file(path: str, data: list, is_json_line: bool = False) -> None:
    valid_path(path)
    with open(path, 'w', encoding='utf-8') as f:
        if is_json_line:
            for line in data:
                f.write(json.dumps(line, ensure_ascii=False) + '\n')
        else:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))


def save_as_csv(path: str, data: list):
    valid_path(path)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding='utf-8')


def valid_path(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


def find_lasest_timastamp_file(root_path):
    pass