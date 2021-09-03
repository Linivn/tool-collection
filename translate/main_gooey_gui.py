# -*- coding: utf-8 -*-
import sys

from gooey import Gooey, GooeyParser

from translate_tool import Translate, Update
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

    # setting
    setting = soft_config.get('setting', {})
    # 代理
    proxy = setting.get('proxy', {})

    base_configure = {
        'translate': {  # 翻译工具配置项
            # googletrans service_urls 如有科学上网可以不用配置
            'service_urls': (setting.get('service_urls'),) if setting.get('service_urls', '') else (
                'translate.google.cn',),
            'proxy': proxy.get('host', None) if proxy.get('enable', False) else None,
            'path': '',  # 翻译文件所在文件目录
            'languages': translate_languages,  # 支持翻译语言
            # 对照 仅翻译新增的文本
            'contrast': 'add.json',  # 对照文件名 默认值: add.json
            'compared': 'zh_cns.json'  # 被对照文名 默认值: zh_cns.json
        },
        'update': {  # main更新工具配置项
            'base_url': 'https://xxx.com',  # main url
            'selenium_login': False,  # 是否使用模拟登录，建议直接复制浏览器的cookie进行登录
            'executable_path': '',  # chromedriver 文件路径，仅在利用 selenium 模拟登录时需要配置
            'cookies': ''  # cookie
        }
    }

    return recursive_update(base_configure, new_configure)


def format_print(title, content='', indent=None):
    content = json.dumps(content, ensure_ascii=False, indent=indent) if check_json(content) else content
    print(f'\n{title}\n{content}')


def run(config):
    def get_key(key):
        return config.get(key)

    support_languages = {
        'zh_cns': 'zh-cn',
        'zh_cnt': 'zh-tw',
        'en_us': 'en',
        'in_id': 'id',
        'ja_jp': 'ja',
        'ko_kr': 'ko',
        'th_th': 'th',
        'vi_vn': 'vi'
    }

    multi_translate_content = get_key('multi_translate_content')
    translate_content = get_key('translate_content')
    if multi_translate_content:
        convert_languages = {}
        # for lang in config.keys():
        #     temp = lang[5:]
        #     if temp != '_translate_content' and get_key(lang):
        #         convert_languages[support_languages[temp]] = temp
        for item in get_key('languages'):
            lang = item.split('-')[1]
            convert_languages[support_languages[lang]] = lang

        # 初始化配置数据
        configure = init_configure({
            'translate': {
                'languages': convert_languages
            },
            'update': {
                'base_url': get_key('base_url'),
                'cookies': get_key('cookies')
            }
        })
        # 初始化翻译工具
        translate_tool = Translate(configure.get('translate', {}))
        # 初始化更新工具
        # update_tool = Update(configure.get('update', {}))
        # 翻译
        # translate_result = translate_tool.translate(json.loads(multi_translate_content), update_tool.google_trans)
        translate_result = translate_tool.translate(json.loads(multi_translate_content))
        # 翻译结果
        format_print('翻译结果:', translate_result, indent=2)
    elif translate_content:
        def add_space(key, max_width):
            key_len = len(key)
            return '　' * (max_width - key_len + 1)

        # 初始化配置数据
        configure = init_configure({'translate': {}})
        # 初始化翻译工具
        translate_tool = Translate(configure.get('translate', {}))
        # 转换code
        src_lang = get_key('src_lang')
        src = langcodes.get(src_lang, 'auto')
        dest_lang = get_key('dest_lang')
        # 截取前八种语言
        dest_lang = dest_lang[:8]
        dest = reduce(lambda x, y: ([*x, langcodes.get(y)]), dest_lang, [])
        # 目标语言文字最大长度
        max_width = len(max(dest_lang, key=lambda i: len(i)))
        # 翻译
        translate_res = translate_tool.google_multi_translate(translate_content, dest=dest, src=src)
        translate_result = f'{src_lang}{add_space(src_lang, max_width)} >　 {translate_content} \n\n'
        for k, v in translate_res.items():
            lang_text = google_languages.get(k)
            translate_result += f'{lang_text}{add_space(lang_text, max_width)} >　 {v} \n'
        # 翻译结果
        format_print('翻译结果:', translate_result, indent=2)
    else:
        # 转换翻译语言
        languages = get_key('languages')
        convert_languages = {}
        for item in languages:
            lang = item.split('-')[1]
            convert_languages[support_languages[lang]] = lang

        # 初始化配置数据
        configure = init_configure({
            'translate': {
                'path': get_key('path'),
                'languages': convert_languages
            },
            'update': {
                'base_url': get_key('base_url'),
                'cookies': get_key('cookies')
            }
        })

        # 初始化翻译工具
        translate_tool = Translate(configure.get('translate', {}))
        # 初始化更新工具
        update_tool = Update(configure.get('update', {}))
        # edit.json 路径
        edit_file_path = f'''{configure['translate']['path']}/edit.json'''
        # 翻译
        # translate_result = translate_tool.translate(None, update_tool.google_trans)
        translate_result = translate_tool.translate()

        # 登录信息
        get_key('show_user') and format_print('登录信息:', update_tool.user_info)

        # 翻译结果
        get_key('show_result') and format_print('翻译结果:', translate_result)

        # 新增翻译
        # 获取新增翻译参数 convert_to_add_params(translate_result)
        get_key('update_add') and format_print('新增结果:', update_tool.multi_add(convert_add_params(translate_result)))

        # 修改翻译
        get_key('update_edit') and format_print('修改结果:',
                                                update_tool.multi_edit(convert_edit_params(open_file(edit_file_path)),
                                                                       edit_file_path))

        # 查询翻译
        search_key = get_key('search_key')
        if len(search_key):
            if get_key('search_type') == '详情':
                search_key_list = search_key.split(',')
                search_details = {}
                for k in search_key_list:
                    search_details = {**search_details,
                                      **update_tool.get_detail({'hash_key': k.lower()}, is_search=True)}

                format_print('查询结果:', search_details, indent=2)
            else:
                search_key_list = search_key.split('|')
                category = ''
                group = ''
                list_len = len(search_key_list)

                if list_len == 1:
                    search = search_key_list[0]
                elif list_len == 2:
                    category = search_key_list[0]
                    search = search_key_list[1]
                else:
                    category = search_key_list[0]
                    group = search_key_list[1]
                    search = search_key_list[2]

                format_print('查询结果:', update_tool.search({
                    'search_mode': get_key('search_mode') or 'key',
                    'search': search,
                    'category': category,
                    'group': group,
                    'locales': '',
                    'page': 1,
                    'page_size': 150,
                    'group_by': 1
                }, is_search=True), indent=2)

        # 删除翻译
        delete_hash_key = get_key('delete_hash_key')
        delete_hash_key and format_print('删除结果:', update_tool.multi_delete(delete_hash_key.split(',')))

        # 同步翻译
        sync_cdn_key = get_key('sync_cdn')
        sync_cdn_key and format_print('同步结果:', update_tool.sync_cdn(sync_cdn_key.split(',')))

        # 新增表格
        get_key('show_add_table') and format_print('新增表格:', get_add_table(
            open_file(f'''{configure['translate']['path']}/add.json''')))
        # 翻译表格
        get_key('show_edit_table') and format_print('翻译表格:', get_edit_table(open_file(edit_file_path)))


def get_default_value(config_key):
    return default_value.get(config_key)


def create_main_tab(subs):
    main_parser = subs.add_parser('main')
    group1 = main_parser.add_argument_group('必要参数', gooey_options={
        'show_border': True,
        'show_underline': True,
        'columns': 5,
        'margin_top': 0
    })
    group1.add_argument('path', metavar='翻译文件根目录', widget='DirChooser', gooey_options={'show_help': False},
                        default=get_default_value('path'))
    group1.add_argument('base_url', metavar='main URL', widget='Textarea',
                        gooey_options={'height': 70, 'show_help': False},
                        default=get_default_value('base_url'))
    group1.add_argument('languages', metavar='翻译语言', nargs='+',
                        choices=['简体中文-zh_cns', '繁体中文-zh_cnt', '英语-en_us', '印尼语-in_id', '日语-ja_jp', '韩语-ko_kr',
                                 '泰语-th_th', '越南语-vi_vn'], widget='Listbox',
                        gooey_options={'height': 70, 'show_help': False}, default=get_default_value('languages'))
    group1.add_argument('--cookies', metavar='cookies', widget='Textarea',
                        gooey_options={'height': 70, 'show_help': False}, default=get_default_value('cookies'))

    group2 = main_parser.add_argument_group('功能', gooey_options={
        'show_border': True,
        'show_underline': True,
        'columns': 4,
        'margin_top': 0
    })
    group2.add_argument('--show_user', metavar='显示登录信息', action='store_true', help='启用',
                        widget='CheckBox', default=get_default_value('show_user'))
    group2.add_argument('--show_result', metavar='显示翻译结果', action='store_true', help='启用',
                        widget='CheckBox', default=get_default_value('show_result'))
    group2.add_argument('--update_add', metavar='新增翻译', action='store_true', help='将`add.json`的内容更新到main',
                        widget='CheckBox', default=get_default_value('update_add'))
    group2.add_argument('--update_edit', metavar='修改翻译', action='store_true', help='将`edit.json`的内容更新到main',
                        widget='CheckBox', default=get_default_value('update_edit'))

    group21 = group2.add_argument_group('', gooey_options={
        'show_border': False,
        'show_underline': False,
        'columns': 2,
        'margin_top': -15,
    })

    group211 = group21.add_argument_group('查询', gooey_options={
        'show_border': True,
        'show_underline': True,
        'columns': 2,
        'margin_top': 0,
    })
    group211.add_argument('--search_type', metavar='查询类型', choices=['列表', '详情'],
                          help='获取`add.json`的内容到main', widget='Dropdown',
                          gooey_options={
                              # 'show_label': False,
                              'show_help': False,
                          }, default=get_default_value('search_type'))
    group211.add_argument('--search_mode', metavar='查询模式', choices=['key', 'value'],
                          help='获取`add.json`的内容到main', widget='Dropdown',
                          gooey_options={
                              # 'show_label': False,
                              'show_help': False,
                          }, default=get_default_value('search_mode'))
    group211.add_argument('--search_key', metavar='查询内容',
                          help='''查询类型为`列表`时，输入`category|group|keyword`，以竖线`|`隔开\n查询类型为`详情`时，输入`hash_key`，多个`hash_key`以逗号`,`隔开''',
                          widget='Textarea', gooey_options={'height': 83}, default=get_default_value('search_key'))
    group212 = group21.add_argument_group('同步、删除', gooey_options={
        'show_border': True,
        'show_underline': True,
        'columns': 1,
        'margin_top': 0
    })
    group212.add_argument('--sync_cdn', metavar='同步翻译', help='输入`category`，多个`category`以逗号`,`隔开',
                          default=get_default_value('sync_cdn'))
    group212.add_argument('--delete_hash_key', metavar='删除翻译', help='输入`hash_key`，多个`hash_key`以逗号`,`隔开',
                          widget='Textarea', gooey_options={'height': 80},
                          default=get_default_value('delete_hash_key'))

    group22 = group21.add_argument_group('获取表格', gooey_options={
        'show_border': True,
        'show_underline': False,
        'columns': 2,
        'margin_top': 0,
        'height': 250
    })

    group22.add_argument('--show_add_table', metavar='新增表格', action='store_true',
                         help='将`add.json`的内容转换成 Markdown 表格',
                         widget='CheckBox', default=get_default_value('show_add_table'))
    group22.add_argument('--show_edit_table', metavar='修改表格', action='store_true',
                         help='将`edit.json`的内容转换成 Markdown 表格',
                         widget='CheckBox', default=get_default_value('show_edit_table'))


def create_mtran_tab(subs):
    mtran_parser = subs.add_parser('批量翻译')
    group1 = mtran_parser.add_argument_group('必要参数', gooey_options={
        'show_border': True,
        'show_underline': False,
        'columns': 4,
        # 'margin_top': -50,
    })

    # group1.add_argument('base_url', metavar='main URL', widget='Textarea',
    #                     gooey_options={'height': 70, 'show_help': False},
    #                     default=get_default_value('base_url'))
    group1.add_argument('languages', metavar='翻译语言', nargs='+',
                        choices=['简体中文-zh_cns', '繁体中文-zh_cnt', '英语-en_us', '印尼语-in_id', '日语-ja_jp', '韩语-ko_kr',
                                 '泰语-th_th', '越南语-vi_vn'], widget='Listbox',
                        gooey_options={'height': 80, 'show_help': False}, default=get_default_value('languages'))
    # group1.add_argument('--cookies', metavar='cookies', widget='Textarea',
    #                     gooey_options={'height': 70, 'show_help': False}, default=get_default_value('cookies'))

    # '简体中文-zh_cns', '繁体中文-zh_cnt', '英语-en_us', '印尼语-in_id', '日语-ja_jp', '韩语-ko_kr', '泰语-th_th', '越南语-vi_vn'
    # group1.add_argument('lang_zh_cns', action='store_true', help='简体中文-zh_cns', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_zh_cnt', action='store_true', help='繁体中文-zh_cnt', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_en_us', action='store_true', help='英语-en_us', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_in_id', action='store_true', help='印尼语-in_id', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_ja_jp', action='store_true', help='日语-ja_jp', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_ko_kr', action='store_true', help='韩语-ko_kr', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_th_th', action='store_true', help='泰语-th_th', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    # group1.add_argument('--lang_vi_vn', action='store_true', help='越南语-vi_vn', widget='CheckBox',
    #                     gooey_options={'show_label': False, 'show_help': False})
    group2 = mtran_parser.add_argument_group('', gooey_options={
        'show_border': False,
        'show_underline': False,
        'columns': 1,
        'margin_top': -40,
    })
    group2.add_argument('multi_translate_content', help='翻译内容(输入内容必须为json格式且为单行文本)', widget='Textarea',
                        gooey_options={'show_label': False, 'height': 310})


def create_tran_tab(subs):
    default_keys = ['中文（简体）', '中文（繁体）', '英语', '印尼语', '日语', '韩语', '泰语', '越南语']
    langcodes_keys = [*default_keys]
    for lang_key in langcodes.keys():
        if lang_key not in langcodes_keys:
            langcodes_keys.append(lang_key)

    tran_parser = subs.add_parser('Google翻译')
    group1 = tran_parser.add_argument_group('必要参数', gooey_options={
        'show_border': True,
        'show_help': False,
        # 'show_underline': False,
        'columns': 2,
        # 'margin_top': -50,
    })
    group1.add_argument('src_lang', metavar='源始语言', choices=['自动检测', *langcodes_keys], widget='Dropdown',
                        gooey_options={'show_help': False}, default='自动检测')
    group1.add_argument('dest_lang', metavar='目标语言', nargs='+',
                        choices=langcodes_keys, widget='Listbox',
                        gooey_options={'height': 80, 'show_help': False}, default=['中文（简体）'])

    group2 = tran_parser.add_argument_group('', gooey_options={
        'show_border': False,
        'show_underline': False,
        'columns': 1,
        'margin_top': -40,
    })
    group2.add_argument('translate_content', help='翻译文字(输入内容必须为单行文本)', widget='Textarea',
                        gooey_options={'show_label': False, 'height': 310})


@Gooey(
    language='chinese',
    program_name='Toolkit',
    encoding='utf-8',
    navigation='TABBED',
    header_height=11,
    header_show_subtitle=False,
    header_show_title=False,
    show_success_modal=False,
    clear_before_run=True,
    default_size=(960, 700)
)
def main():
    parser = GooeyParser()
    subs = parser.add_subparsers()

    tabs = soft_config.get('tabs', ['tran'])
    create_tab_map = {
        'main': create_main_tab,
        'mtran': create_mtran_tab,
        'tran': create_tran_tab
    }
    for tab in tabs:
        create_tab_map.get(tab)(subs)

    args = vars(parser.parse_args())  # 接收界面传递的参数
    run(args)


if __name__ == '__main__':
    """
    打包后，控制台出现英文以外的文字导致报错
    解决方法：
        一（不推荐，仅能解决中文报错）：
            1. @Gooey(encoding='utf-8') 配置为utf-8
            2. gooey/gui/processor.py[_forward_stdout() => 75行、_extract_progress() => 84行] 
               在此文件中将 decode(self.encoding) 修改为 decode('gbk')
        二（推荐）
            1. @Gooey(encoding='utf-8') 配置为utf-8
            2. 将 sys.stdout、sys.stderr 的 encoding 设置为 'utf-8'
    """
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'UTF-8':
        sys.stderr.reconfigure(encoding='utf-8')

    # 本地配置
    soft_config = open_file('./config.json')
    # 默认配置
    default_value = recursive_update({
        'path': None,
        'base_url': 'https://xxx.com',
        'languages': [
            '简体中文-zh_cns',
            '繁体中文-zh_cnt',
            '英语-en_us'
        ],
        'cookies': '',
        'update_add': False,
        'update_edit': False,
        'show_result': False,
        'show_user': False,
        'search_type': '列表',
        'search_mode': 'key',
        'search_key': '',
        'sync_cdn': '',
        'delete_hash_key': '',
        'show_add_table': False,
        'show_edit_table': False
    }, soft_config.get('default_value', {}))
    google_languages = {
        'sq': '阿尔巴尼亚语', 'ar': '阿拉伯语', 'am': '阿姆哈拉语', 'az': '阿塞拜疆语', 'ga': '爱尔兰语', 'et': '爱沙尼亚语', 'or': '奥利亚语',
        'eu': '巴斯克语', 'be': '白俄罗斯语', 'bg': '保加利亚语', 'is': '冰岛语', 'pl': '波兰语', 'bs': '波斯尼亚语', 'fa': '波斯语',
        'af': '布尔语(南非荷兰语)', 'da': '丹麦语', 'de': '德语', 'ru': '俄语', 'fr': '法语', 'tl': '菲律宾语', 'fi': '芬兰语',
        'fy': '弗里西语', 'km': '高棉语', 'ka': '格鲁吉亚语', 'gu': '古吉拉特语', 'kk': '哈萨克语', 'ht': '海地克里奥尔语', 'ko': '韩语',
        'ha': '豪萨语', 'nl': '荷兰语', 'ky': '吉尔吉斯语', 'gl': '加利西亚语', 'ca': '加泰罗尼亚语', 'cs': '捷克语', 'kn': '卡纳达语',
        'co': '科西嘉语', 'hr': '克罗地亚语', 'ku': '库尔德语', 'la': '拉丁语', 'lv': '拉脱维亚语', 'lo': '老挝语', 'lt': '立陶宛语',
        'lb': '卢森堡语', 'ro': '罗马尼亚语', 'mg': '马尔加什语', 'mt': '马耳他语', 'mr': '马拉地语', 'ml': '马拉雅拉姆语', 'ms': '马来语',
        'mk': '马其顿语', 'mi': '毛利语', 'mn': '蒙古语', 'bn': '孟加拉语', 'my': '缅甸语', 'hmn': '苗语', 'xh': '南非科萨语',
        'zu': '南非祖鲁语', 'ne': '尼泊尔语', 'no': '挪威语', 'pa': '旁遮普语', 'pt': '葡萄牙语', 'ps': '普什图语', 'ny': '齐切瓦语',
        'ja': '日语', 'sv': '瑞典语', 'sm': '萨摩亚语', 'sr': '塞尔维亚语', 'st': '塞索托语', 'si': '僧伽罗语', 'eo': '世界语',
        'sk': '斯洛伐克语', 'sl': '斯洛文尼亚语', 'sw': '斯瓦希里语', 'gd': '苏格兰盖尔语', 'ceb': '宿务语', 'so': '索马里语', 'tg': '塔吉克语',
        'te': '泰卢固语', 'ta': '泰米尔语', 'th': '泰语', 'tr': '土耳其语', 'cy': '威尔士语', 'ug': '维吾尔语', 'ur': '乌尔都语',
        'uk': '乌克兰语', 'uz': '乌兹别克语', 'es': '西班牙语', 'iw': '希伯来语', 'el': '希腊语', 'haw': '夏威夷语', 'sd': '信德语',
        'hu': '匈牙利语', 'sn': '修纳语', 'hy': '亚美尼亚语', 'ig': '伊博语', 'it': '意大利语', 'yi': '意第绪语', 'hi': '印地语',
        'su': '印尼巽他语', 'id': '印尼语', 'jw': '印尼爪哇语', 'en': '英语', 'yo': '约鲁巴语', 'vi': '越南语', 'zh-tw': '中文（繁体）',
        'zh-cn': '中文（简体）'
    }
    langcodes = dict(map(reversed, google_languages.items()))
    try:
        main()
    except Exception as e:
        logger(msg=f'Failed in [ main ]: {e}', level=logging.ERROR)
