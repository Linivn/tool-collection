# coding:utf-8
from translate_tool import Translate
from translate_tool.utils import *


def init_configure(new_configure):
    translate_languages = {  # 需要翻译的语言
        'en': 'en_us',
        'zh-cn': 'zh_cns',
        'zh-tw': 'zh_cnt',
        'id': 'in_id',
        'ja': 'ja_jp',
        'ko': 'ko_kr',
        'th': 'th_th',
        'vi': 'vi_vn'
    }

    if 'languages' in new_configure.get('translate', {}):
        translate_languages = new_configure['translate']['languages']

    base_configure = {
        'translate': {  # 翻译工具配置项
            # 'service_urls': ['translate.google.cn'],  # googletrans service_urls 如有科学上网可以不用配置
            'path': '',  # 翻译文件所在文件目录
            'languages': translate_languages,  # 支持翻译语言
            # 对照 仅翻译新增的文本
            'contrast': 'add.json',  # 对照文件名 默认值: add.json
            'compared': 'zh_cns.json'  # 被对照文名 默认值: zh_cns.json
        }
    }

    return recursive_update(base_configure, new_configure)


if __name__ == '__main__':
    configure = {
        'translate': {
            'service_urls': ('translate.google.cn',), # googletrans service_urls 如有科学上网可以不用配置
            # 'proxy': 'http://127.0.0.1:10809', # 代理
            'path': '',  # 翻译文件所在文件目录
            'languages': {  # 需要翻译什么语言，放开注释即可
                # 谷歌翻译支持语言列表参考：googletrans.constants.LANGUAGES
                'en': 'en_us',
                'zh-cn': 'zh_cns',
                'zh-tw': 'zh_cnt',
                # 'id': 'in_id',
                # 'ja': 'ja_jp',
                # 'ko': 'ko_kr',
                # 'th': 'th_th',
                # 'vi': 'vi_vn'
            }  # 支持翻译语言
        }
    }

    # 初始化配置数据
    configure = init_configure(configure)
    # 初始化翻译工具
    translate_tool = Translate(configure.get('translate', {}))

    # 获取翻译结果
    # 传参为空，将读取add.json文件内容进行翻译
    translate_result = translate_tool.translate()
    # 传参为dict
    # translate_result = translate_tool.translate({
    #     'test': '测试',
    #     'hello': '你好'
    # })
    # 传参为list
    # translate_result = translate_tool.translate(['测试', '你好'])

    print('翻译结果:', translate_result)
