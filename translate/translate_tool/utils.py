# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import time
from functools import reduce

import pyperclip
from dict_recursive_update import recursive_update

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO)
logger = logging.log


def check_json(data):
    """
    判断是否为json
    :param data:
    :return:
    """
    try:
        data_type = type(data)
        if data_type in [str, list, dict]:
            if data_type is str:
                json.loads(data)
            else:
                json.dumps(data)
            return True
        return False
    except BaseException:
        return False
    except TypeError:
        return False
    except:
        return False


def add_to_clipboard(text):
    """
    将字符串添加到剪切板
    :param text:
    :return:
    """
    try:
        pyperclip.copy(str(text))
    except Exception as e:
        logger(msg=f'Failed in [ add_to_clipboard ]: {e}', level=logging.ERROR)


def get_json_str(data, indent=4):
    """
    获取转换成 json 字符串，便于后续复制使用
    :param data: 需要处理的数据
    :param indent: 缩进
    :return:
    """
    return json.dumps(data, ensure_ascii=False, sort_keys=False, indent=indent, separators=(', ', ': '))


def get_keys_list(data):
    """
    获取dict的key列表
    :param data: 需要处理的数据
    :return:
    """
    return list(data.keys())


def get_values_list(data):
    """
    获取dict的value列表
    :param data: 需要处理的数据
    :return:
    """
    return list(data.values())


def save_file(content, path, mode='w', encoding='utf-8'):
    """
    保存为文件，如文件名后缀为json，则以json格式保存
    :param content:
    :param path:
    :param mode:
    :param encoding:
    :return:
    """
    try:
        # 存在多级文件夹，需先创建不存在的目录再保存
        path_arr = path.split('/')
        path_arr.pop()
        dir_path = '/'.join(path_arr)
        if len(path_arr) > 1 and (not os.path.exists(dir_path)):
            # 目录不存在则创建
            os.makedirs(dir_path)

        with open(path, mode=mode, encoding=encoding) as file:
            # 判断是否为json文件，是则以json格式保存
            result_str = str(content) if not re.match(r'.+\.json$', path) else json.dumps(content, ensure_ascii=False,
                                                                                          sort_keys=False, indent=4,
                                                                                          separators=(',', ': '))
            file.write(result_str)
            file.close()
            # logger(msg=f'Success: file saved to {path}', level=logging.INFO)
    except Exception as e:
        logger(msg=f'Failed in [ save_file ]: {e}', level=logging.ERROR)


def open_file(path, mode='r+', encoding='utf-8'):
    """
    获取文件内容，如文件名后缀为json，则以json格式返回
    :param path:
    :param mode:
    :param encoding:
    :return:
    """
    is_json_file = re.match(r'.+\.json$', path)
    result = {} if is_json_file else ''

    try:
        if not os.path.exists(path):
            # 文件不存在则先创建
            save_file(result, path)

        with open(path, mode=mode, encoding=encoding) as file:
            if file.__sizeof__() > 0:
                # 判断是否为json文件，是则以json格式返回
                result = json.load(file) if is_json_file else file.read()

            file.close()
            return result
    except Exception as e:
        logger(msg=f'Failed in [ open_file ]: {e}', level=logging.ERROR)
        return result


def flatten(data, key=''):
    """
    字典扁平化
    :param data:
    :param key:
    :param path:
    :return:
    """

    def get_new_path(key_path):
        temp_path = list(filter(lambda x: True if x else False, key_path))
        return '|'.join(temp_path) if len(temp_path) > 0 else ''

    result = {}

    if type(data) is not dict:
        result[key] = data
    elif isinstance(data, list):
        for i, item in enumerate(data):
            flatten(item, get_new_path([key, str(i)]))
    else:
        for new_key, value in data.items():
            result = {**result, **flatten(value, get_new_path([key, new_key]))}

    return result


def reverse_flatten(data):
    """
    字典反扁平化
    :param data:
    :return:
    """
    try:
        result = {}
        for k, v in data.items():
            # 使用 reduce 将 键名列表（k.split('|')）处理成嵌套字典
            # 再使用 recursive_update 合并嵌套字典，避免某些字段被覆盖
            result = recursive_update(result, reduce(lambda x, y: {y: x}, reversed(k.split('|')), v))
        return result
    except Exception as e:
        logger(msg=e, level=logging.ERROR)
        return {}


def get_differ_dict(dict1, dict2):
    """
    获取字典差异项
    获取的是在dict1中，但不在dict2中的项
    :param dict1:
    :param dict2:
    :return:
    """
    try:
        flatten_dict1 = flatten(dict1)
        flatten_dict2 = flatten(dict2)

        """
        set(dict1.items()) - set(dict2.items())
        得到的是对比dict1与dict2的key或value不一致的结果
        即dict的key或value其中一个不相等，也符合差异的结果
        因此需要转换为value一样的dict再去比较
        """
        # 将dict的value全部转换为'same_value'
        same_value_dict1 = reduce(lambda x, y: {**x, y: 'same_value'}, flatten_dict1.keys(), {})
        same_value_dict2 = reduce(lambda x, y: {**x, y: 'same_value'}, flatten_dict2.keys(), {})

        # 获取非重复键值对
        data = dict(set(same_value_dict1.items()) - set(same_value_dict2.items()))

        # 转换回原来的value
        for k, v in data.items():
            data[k] = flatten_dict1[k]

        return reverse_flatten(data)
    except Exception as e:
        logger(msg=e, level=logging.ERROR)
        return {}


def get_merge_dict(*dict_args):
    """
    获取嵌套字典合并的结果
    :param dict_args:
    :return:
    """

    def deep_search(dict1, dict2):
        """嵌套字典合并，参数1旧字典，参数2新字典，结果是将新字典合并到旧字典中"""
        for i in dict2:
            if i in dict1:
                if type(dict1[i]) is dict and type(dict2[i]) is dict:
                    dict1[i] = deep_search(dict1[i], dict2[i])
            else:
                dict1[i] = dict2[i]
        return dict1

    return deep_search(dict_args[0], dict_args[1])


def save_edit_to_file(path, edit_data, local_list):
    """
    保存修改翻译数据到 edit.json 文件
    :param path: edit.json 文件路径
    :param edit_data: 修改翻译
    :param local_list: 原始翻译
    :return:
    """
    try:
        edit_file = open_file(path)
        category = edit_data.get('category')
        group = edit_data.get('group')
        key = edit_data.get('key')
        locales = edit_data.get('locales')
        proposer = edit_data.get('proposer')

        # 修改的key不存在时，设置默认值：{}
        edit_file.setdefault(category, {})
        edit_file[category].setdefault(group, {})
        edit_file[category][group].setdefault(key, {})

        edit_item = edit_file[category][group][key] or {}
        edit_item['proposer'] = proposer or '-'

        if not edit_item.get('before'):
            # 仅保存第一次修改的原始翻译数据
            edit_item['before'] = {}
            for lang in locales.keys():
                for local in local_list:
                    if lang == local['locales']:
                        # 仅复制修改翻译数据中语言对应的翻译文字
                        edit_item['before'][lang] = local['value']

        edit_item['after'] = locales
        edit_file[category][group][key] = edit_item
        save_file(edit_file, path)
    except Exception as e:
        logger(msg=e, level=logging.ERROR)


def re_search(key_str, search_str):
    patten = re.compile(r'.+(' + key_str + ').+')
    return re.search(patten, search_str)


def get_edit_table(data=None):
    """
    获取修改翻译的markdown表格，用于编写语言翻译修改文档
    :param data: {
        'category': {
            'group': {
                'key': {
                    'proposer': '提出者名称',
                    'before': { # 修改前
                        'en_us': 'value',
                        ...
                    },
                    'after': { # 修改后
                        'en_us': 'value1',
                        ...
                    }
                },
                ...
            }
        }
    }
    :return:
    """
    if not data:
        return None

    result = ''
    languages_map = {
        'en_us': '英',
        'zh_cns': '简',
        'zh_cnt': '繁',
        'in_id': '印尼',
        'ja_jp': '日',
        'ko_kr': '韩',
        'th_th': '泰',
        'vi_vn': '越'
    }

    for category, category_value in data.items():
        for group, group_value in category_value.items():
            for k, v in group_value.items():
                if 'after' in v:
                    before = v.get('before', {})
                    after = v.get('after')
                    before_text = ''
                    after_text = ''
                    for lang in after.keys():
                        before_text += f'''{languages_map.get(lang)}：{before.get(lang)}<br/>''' if before.get(
                            lang) else ''
                        after_text += f'{languages_map.get(lang)}：{after.get(lang)}<br/>' if after.get(lang) else ''

                    result = result + f'''|{'' if re_search(category, result) else category}|{'' if re_search(group, result) else group}|{k}|{before_text}|{after_text}|{v.get('proposer', '')}|\n'''

    result = f'|category|group|key|修改前|修改后|提出者|\n|---|---|---|---|---|---|\n{result}'
    if '|category|group|key|修改前|修改后|提出者|\n|---|---|---|---|---|---|\n' == result:
        return None
    return result.rstrip('\n')


def get_add_table(data):
    """
    获取新增翻译的markdown表格，用于编写语言翻译修改文档
    :param data:
    :return:
    """
    if not data:
        return None

    if 'en_us' in data:
        data = data.get('en_us', data)

    result = ''

    for category, category_value in data.items():
        for group, group_value in category_value.items():
            for key in group_value.keys():
                hash_key = f'{category}_{group}_{key}'.lower()
                result += f'''|{'' if re_search(category, result) else category}|{'' if re_search(group, result) else group}|{key}|{hash_key}|\n'''

    result = f'|category|group|key|hash_key|\n|---|---|---|---|\n{result}'
    if '|category|group|key|hash_key|\n|---|---|---|---|\n' == result:
        return None
    return result.rstrip('\n')


def convert_add_params(data):
    """
    转换为新增翻译请求参数格式
    :param data:
    :return:
    """
    if not data or type(data) is not dict:
        return {}

    category_locales = data.get('en_us')
    locales_land_list = data.keys()
    result = {}

    for category, category_value in category_locales.items():
        group_locales = category_value
        for group, group_value in group_locales.items():
            key_locales = group_value
            for key in key_locales.keys():
                for lang in locales_land_list:
                    if not result.get(key):
                        result[key] = []
                    value = data[lang][category][group][key]
                    # None: 需要在添加翻译时替换为 null
                    result[key].append({
                        'category': category,
                        'key': key,
                        'value_type': 'string',
                        'appid': '_default',
                        'group': group,
                        'locales': lang,
                        'id': None,
                        'value': value if value else None
                    })
    return result


def convert_edit_params(data):
    """
    转换为修改翻译请求参数格式
    :param data:
    :return:
    """
    if not data or type(data) is not dict:
        return []

    result = []

    for category, category_value in data.items():
        group_locales = category_value
        for group, group_value in group_locales.items():
            key_locales = group_value
            for key, key_value in key_locales.items():
                result.append({
                    'category': category,
                    'group': group,
                    'key': key,
                    'proposer': key_value['proposer'] or '',
                    'locales': key_value['after'] or {}
                })

    return result


def translate_use_time(func):
    """
    翻译用时
    :param func:
    :return:
    """

    def wrapper(*args, **kw):
        start = time.time()
        logger(msg=f'正在翻译，请稍候...', level=logging.INFO)
        result = func(*args, **kw)
        logger(msg=f'翻译完成，用时 {round(time.time() - start, 2)} 秒', level=logging.INFO)
        time.sleep(0)
        return result

    return wrapper
