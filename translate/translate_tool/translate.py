# coding:utf-8
from googletrans import Translator
from translate_tool.utils import *


class Translate:
    # 谷歌翻译支持语言列表参考：googletrans.constants.LANGUAGES
    # 多语言翻译系统支持语言列表：['en_us', 'in_id', 'ja_jp', 'ko_kr', 'th_th', 'vi_vn', 'zh_cns', 'zh_cnt']

    def __init__(self, config):
        """
        init
        :param config: {
            'path': 翻译文件初始位置,
            'languages': 支持翻译语言,
            # 对照 仅翻译新增的文本
            'contrast': '对照文件名',
            'compared': '被对照文名'
        }
        """
        self.__trans = Translator()
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
            temp = self.google_translate(i).title()
            # temp = self.google_translate(i)
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
            json_file = get_file(f'{self.path}/results/{v}.json') if self.is_from_file else {}
            result[v] = get_merge_dict(json_file, data[v])

        return result

    def __tran_list_handler(self, data):
        """
        翻译list类型的文本集合
        :param data: 需要翻译的文本（list）
        :return: 翻译后的结果（dict）
        """
        result = {}
        tran_keys = self.__get_tran_keys_list(data)
        list_len = len(data)

        for k, v in self.languages.items():
            result[v] = {}
            for i in range(0, list_len):
                result[v][tran_keys[i]] = self.google_translate(data[i], k)

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
                    more_result[k] = self.google_translate(v, lang)
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

    def google_translate(self, text, dest='en'):
        """
        获取翻译文本
        :param text: 需要翻译的文本
        :param dest: 翻译语言
        :return:
        """
        if dest == 'zh-cn':
            return text

        return (self.__trans.translate(text, dest=dest)).text

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
            tran_str = self.google_translate(i)
            tran_key = replace_re.sub('', tran_str.title())
            result[tran_key] = {
                'zh-cn': i,
                'en_us': tran_str
            }

        return result

    def translate(self, locales=None):
        """
        翻译，支持dict、list类型
        默认不传参，会获取 add.json 的内容进行翻译，并将翻译结果保存到文件中
        如果传参，则仅进行翻译，不会将翻译结果保存到文件中
        :param locales:
        :return:
        """
        results = {}
        try:
            if not locales:
                # 对比 contrast、compared 差异，仅翻译新增的字段
                contrast_json = get_file(f'{self.path}/{self.contrast}')
                compared_json = get_file(f'{self.path}/results/{self.compared}')
                # 获取 contrast、compared 的差异结果
                locales = get_differ_dict(flatten(contrast_json), flatten(compared_json))
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
                    results[lang] = get_file(f'{self.path}/results/{lang}.json')

                logger(msg='当前已是最新翻译结果', level=logging.INFO)

            return results

        except Exception as e:
            logger(msg=f'Failed in [ translate ]: {e}', level=logging.ERROR)
            return results
