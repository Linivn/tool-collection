# translate tool

## 安装依赖

> 理论上支持 `python3.0` 以上版本

```bash
# 进入到 requirements.txt 文件所在目录，运行以下命令
pip install -r requirements.txt
```

---

## 使用

- 文件格式：新增翻译`add.json`

```text
# add.json
# 该文件用来保存新增翻译的内容
# 新增翻译时，需先在此文件中添加内容，再进行翻译
{
  "category": {
    "group": {
      "key": "value",
      ...
    }
  },
  "category": {
    ...
  }
}
```

- 配置

```python
# 运行前需要先进行相关配置
configure = {
    'translate': {  # 翻译工具配置项
        'service_urls': ['translate.google.cn'],  # googletrans service_urls 如有科学上网可以不用配置
        'path': '',  # 翻译文件所在文件目录
        'languages': {  # 需要翻译什么语言，放开注释即可
            'en': 'en_us',
            'zh-cn': 'zh_cns',
            'zh-tw': 'zh_cnt',
            # 'id': 'in_id',
            # 'ja': 'ja_jp',
            # 'ko': 'ko_kr',
            # 'th': 'th_th',
            # 'vi': 'vi_vn'
        },  # 支持翻译语言
        # 对照 仅翻译新增的文本
        'contrast': 'add.json',  # 对照文件名 默认值：add.json
        'compared': 'zh_cns.json'  # 被对照文名 默认值：zh_cns.json
    }
}
```

- 运行

> translate.py: google翻译工具
>
> ~~update.py: 某翻译系统相关工具，用于新增、删除、修改、查询翻译~~ 忽略

```bash
# 基本用法参考 mian.py，相关函数的说明参考: 附录
# 需要使用什么功能，放开注释即可

# 运行
python mian.py
```

> 翻译多语言：读取 `add.json` 文件中内容，将其翻译成多语言并保存，每次仅翻译添加部分（会先比较 `add.json` 与 `zh_cns.json` 的差异）
>
> 使用步骤：
> 1. 在 `add.json` 中添加新增翻译内容
> 2. 调用 `Translate.translate` 翻译成其他语言（仅翻译添加部分），并将翻译结果保存到相应的文件中
> 3. 返回翻译结果（如无新增内容，则读取 `results` 文件夹下的所有文件内容返回）

---

## 附录

```text
# translate.py
__init__(self, config)
init
:param config: {
    'service_urls': googletrans service_urls
    'path': 翻译文件初始位置,
    'languages': 支持翻译语言,
    # 对照 仅翻译新增的文本
    'contrast': '对照文件名',
    'compared': '被对照文名'
}

google_translate(self, text, dest='en', src='auto')
获取翻译文本
:param text: 需要翻译的文本
:param dest: 目标语言
:param src: 源始语言
:return:

translate(self, locales=None)
翻译，支持dict、list类型
默认不传参，会获取 add.json 的内容进行翻译，并将翻译结果保存到文件中
如果传参，则仅进行翻译，不会将翻译结果保存到文件中
:param locales:
:return:
```

```text
# utils.py
add_to_clipboard(text)
将字符串添加到剪切板
:param text:
:return:

check_json(input_str)
判断是否为json字符串
:param input_str:
:return:

convert_to_add_params(data)
转换为新增翻译请求参数格式
:param data:
:return:

flatten(data, key='', path='')
字典扁平化
:param data:
:param key:
:param path:
:return:

get_add_table(data)
获取新增翻译的markdown表格，用于编写语言翻译修改文档
:param data:
:return:

get_differ_dict(dict1, dict2)
获取字典差异项
获取的是在dict1中，但不在dict2中的项
:param dict1:
:param dict2:
:return:

get_edit_table(data=None)
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

open_file(path, mode='r+', encoding='utf-8')
获取文件内容，如文件名后缀为json，则以json格式返回
:param path:
:param mode:
:param encoding:
:return:

get_json_str(data, indent=4)
获取转换成 json 字符串，便于后续复制使用
:param data: 需要处理的数据
:param indent: 缩进
:return:

get_keys_list(data)
获取dict的key列表
:param data: 需要处理的数据
:return:

get_merge_dict(*dict_args)
获取嵌套字典合并的结果
:param dict_args:
:return:

get_values_list(data)
获取dict的value列表
:param data: 需要处理的数据
:return:

re_search(key_str, search_str)

reverse_flatten(data)
字典反扁平化
:param data:
:return:

save_edit_to_file(path, edit_data, local_list)
保存修改翻译数据到 edit.json 文件
:param path: edit.json 文件路径
:param edit_data: 修改翻译
:param local_list: 原始翻译
:return:

save_file(content, path, mode='w', encoding='utf-8')
保存为文件，如文件名后缀为json，则以json格式保存
:param content:
:param path:
:param mode:
:param encoding:
:return:

translate_use_time(func)
翻译用时
:param func:
:return:
```