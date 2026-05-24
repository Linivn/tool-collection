# -*- coding: utf-8 -*-
from googletrans import Translator

from translate_tool.utils import *


class Translate:
    # 谷歌翻译支持语言列表参考：googletrans.constants.LANGUAGES
    # {'sq': '阿尔巴尼亚语', 'ar': '阿拉伯语', 'am': '阿姆哈拉语', 'az': '阿塞拜疆语', 'ga': '爱尔兰语', 'et': '爱沙尼亚语', 'or': '奥利亚语', 'eu': '巴斯克语', 'be': '白俄罗斯语', 'bg': '保加利亚语', 'is': '冰岛语', 'pl': '波兰语', 'bs': '波斯尼亚语', 'fa': '波斯语', 'af': '布尔语(南非荷兰语)', 'da': '丹麦语', 'de': '德语', 'ru': '俄语', 'fr': '法语', 'tl': '菲律宾语', 'fi': '芬兰语', 'fy': '弗里西语', 'km': '高棉语', 'ka': '格鲁吉亚语', 'gu': '古吉拉特语', 'kk': '哈萨克语', 'ht': '海地克里奥尔语', 'ko': '韩语', 'ha': '豪萨语', 'nl': '荷兰语', 'ky': '吉尔吉斯语', 'gl': '加利西亚语', 'ca': '加泰罗尼亚语', 'cs': '捷克语', 'kn': '卡纳达语', 'co': '科西嘉语', 'hr': '克罗地亚语', 'ku': '库尔德语', 'la': '拉丁语', 'lv': '拉脱维亚语', 'lo': '老挝语', 'lt': '立陶宛语', 'lb': '卢森堡语', 'ro': '罗马尼亚语', 'mg': '马尔加什语', 'mt': '马耳他语', 'mr': '马拉地语', 'ml': '马拉雅拉姆语', 'ms': '马来语', 'mk': '马其顿语', 'mi': '毛利语', 'mn': '蒙古语', 'bn': '孟加拉语', 'my': '缅甸语', 'hmn': '苗语', 'xh': '南非科萨语', 'zu': '南非祖鲁语', 'ne': '尼泊尔语', 'no': '挪威语', 'pa': '旁遮普语', 'pt': '葡萄牙语', 'ps': '普什图语', 'ny': '齐切瓦语', 'ja': '日语', 'sv': '瑞典语', 'sm': '萨摩亚语', 'sr': '塞尔维亚语', 'st': '塞索托语', 'si': '僧伽罗语', 'eo': '世界语', 'sk': '斯洛伐克语', 'sl': '斯洛文尼亚语', 'sw': '斯瓦希里语', 'gd': '苏格兰盖尔语', 'ceb': '宿务语', 'so': '索马里语', 'tg': '塔吉克语', 'te': '泰卢固语', 'ta': '泰米尔语', 'th': '泰语', 'tr': '土耳其语', 'cy': '威尔士语', 'ug': '维吾尔语', 'ur': '乌尔都语', 'uk': '乌克兰语', 'uz': '乌兹别克语', 'es': '西班牙语', 'iw': '希伯来语', 'el': '希腊语', 'haw': '夏威夷语', 'sd': '信德语', 'hu': '匈牙利语', 'sn': '修纳语', 'hy': '亚美尼亚语', 'ig': '伊博语', 'it': '意大利语', 'yi': '意第绪语', 'hi': '印地语', 'su': '印尼巽他语', 'id': '印尼语', 'jw': '印尼爪哇语', 'en': '英语', 'yo': '约鲁巴语', 'vi': '越南语', 'zh-tw': '中文（繁体）', 'zh-cn': '中文（简体）'}
    # 多语言翻译系统支持语言列表：['en_us', 'in_id', 'ja_jp', 'ko_kr', 'th_th', 'vi_vn', 'zh_cns', 'zh_cnt']

    def __init__(self, config):
        """
        init
        :param config: {
            'service_urls': googletrans service_urls
            'path': 翻译文件初始位置,
            'languages': 支持翻译语言,
            # 对照 仅翻译新增的文本
            'contrast': '对照文件名',
            'compared': '被对照文名'
        }
        """
        self.main_trans = None
        # 'proxies', 'http://127.0.0.1:10809'
        self.__trans = Translator(service_urls=config.get('service_urls', ('translate.google.cn',)),
                                  timeout=config.get('timeout', 15),
                                  proxies=config.get('proxy', None))
        self.path = config.get('path', './')
        self.languages = config.get('languages', {'en': 'en_us', 'zh-cn': 'zh_cns'})
        self.contrast = config.get('contrast', 'add.json')
        self.compared = config.get('compared', 'zh_cns.json')
        self.is_from_file = False  # 翻译内容是否来自本地文件

    def __get_tran_keys_list(self, data):
        """
        获取翻译成英文的文本列表，作为翻译结果的key
        :param data: 需要处理的数据
        :return:
        """
        result = []
        replace_re = re.compile(r'[., ]')
        for i in data:
            temp = self.__get_translate_text(i).title()
            # temp = self.__get_translate_text(i)
            temp = replace_re.sub('', temp)
            # temp = temp[0].lower() + temp[1:]
            result.append(temp)
        return result

    def __get_merge_json_dict(self, data):
        """
        获取新的翻译合并结果
        仅翻译新添加的文本
        :param data:
        :return:
        """
        result = {}
        for k, v in self.languages.items():
            json_file = open_file(f'{self.path}/results/{v}.json') if self.is_from_file else {}
            result[v] = get_merge_dict(json_file, data[v])

        return result

    def __get_translate_text(self, text, dest='en', src='auto'):
        """
        获取翻译文本
        :param text: 需要翻译的文本
        :param dest: 目标语言
        :param src: 源始语言
        :return:
        """
        if dest and (dest == src):
            return text

        if self.main_trans:
            return self.main_trans(text, to_lang=dest)

        return (self.__trans.translate(text, dest=dest, src=src)).text

    def __tran_list_handler(self, data):
        """
        翻译list类型的文本集合，适用于未确定key的情况，仅翻译不会保存到文件
        :param data: 需要翻译的文本（list）
        :return: 翻译后的结果（dict）
        """
        result = {}
        tran_keys = self.__get_tran_keys_list(data)
        list_len = len(data)

        for k, v in self.languages.items():
            result[v] = {}
            for i in range(0, list_len):
                result[v][tran_keys[i]] = self.__get_translate_text(data[i], k)

        return result

    def __tran_dict_handler(self, data):
        """
        翻译dict类型的文本集合
        :param data: 需要翻译的文本（dict）
        :return: 翻译后的结果（dict）
        """
        result = {}

        def trans_more(key_data, lang):
            more_result = {}
            for k, v in key_data.items():
                if type(v) is str:
                    more_result[k] = self.__get_translate_text(v, lang)
                else:
                    more_result[k] = trans_more(v, lang)

            return more_result

        for key, value in self.languages.items():
            result[value] = trans_more(data, key)

        return result

    @translate_use_time
    def __tran_handler(self, data):
        """
        翻译
        :param data: 需要翻译的文本（dict|list）
        :return: 翻译后的结果（dict）
        """
        # 翻译文本的类型：list、dict
        result = {}
        locales_type = type(data)
        if locales_type is list:
            result = self.__tran_list_handler(data)
        elif locales_type is dict:
            result = self.__get_merge_json_dict(self.__tran_dict_handler(data))

        return result

    @translate_use_time
    def google_translate(self, text, dest='en', src='auto'):
        """
        谷歌翻译
        :param text: 需要翻译的文本
        :param dest: 目标语言
        :param src: 源始语言
        :return:
        """
        return self.__get_translate_text(text, dest=dest, src=src)

    @translate_use_time
    def google_multi_translate(self, text, dest=['en'], src='auto'):
        """
        谷歌翻译
        :param text: 需要翻译的文本
        :param dest: 目标语言
        :param src: 源始语言
        :return:
        """
        result = {}

        for lang in dest:
            result[lang] = self.__get_translate_text(text, dest=lang, src=src)

        return result

    @translate_use_time
    def list_translate(self, data):
        """
        翻译列表类型的文本，适用于未确定key的情况，仅翻译不会保存到文件
        :param data:
        :return: 
        """
        if type(data) is not list:
            return data

        result = {}
        replace_re = re.compile(r'[., ]')
        for i in data:
            tran_str = self.__get_translate_text(i)
            tran_key = replace_re.sub('', tran_str.title())
            result[tran_key] = {
                'zh-cn': i,
                'en_us': tran_str
            }

        return result

    def translate(self, locales=None, main_trans=None):
        """
        翻译，支持dict、list类型
        默认不传参，会获取 add.json 的内容进行翻译，并将翻译结果保存到文件中
        如果传参，则仅进行翻译，不会将翻译结果保存到文件中
        :param main_trans:
        :param locales:
        :return:
        """
        results = {}
        try:
            self.main_trans = main_trans
            if not locales:
                # 对比 contrast、compared 差异，仅翻译新增的字段
                contrast_json = open_file(f'{self.path}/{self.contrast}')
                compared_json = open_file(f'{self.path}/results/{self.compared}')
                # 获取 contrast、compared 的差异结果
                locales = get_differ_dict(contrast_json, compared_json)
                self.is_from_file = True

            if locales:
                # 翻译结果
                results = self.__tran_handler(locales)
                if self.is_from_file:
                    # 保存翻译结果到文件中
                    for k, v in results.items():
                        save_file(v, f'{self.path}/results/{k}.json')
            else:
                # 翻译结果为最新时，获取本地文件内的翻译结果
                for lang in self.languages.values():
                    results[lang] = open_file(f'{self.path}/results/{lang}.json')

                logger(msg='当前已是最新翻译结果', level=logging.INFO)

            return results

        except Exception as e:
            logger(msg=f'Failed in [ translate ]: {e}', level=logging.ERROR)
            return results
