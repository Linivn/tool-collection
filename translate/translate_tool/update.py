# -*- coding: utf-8 -*-
import json
import time

import requests
from selenium import webdriver

from translate_tool.utils import check_json, logger, logging, save_edit_to_file


def block_logout(func):
    def wrapper(*args, **kw):
        login_result = Update.check_login(args[0])
        if login_result:
            return func(*args, **kw)
        else:
            return {'code': 403, 'msg': '请先登录'}

    return wrapper


class Update:
    def __init__(self, config):
        """
        init
        :param config: {
            'account_data': office365账户(用于模拟手动登录),
            'executable_path': chromedriver 文件路径,
            'cookies': cookie,
            'base_url': main url,
            'selenium_login': 是否使用模拟登录
        }
        """
        self.user_info = {}
        self.account_data = config.get('account_data', {})
        self.executable_path = config.get('executable_path', './software/chromedriver_win32/chromedriver.exe')
        self.cookies = config.get('cookies', '')
        self.base_url = config.get('base_url', '').rstrip('/')  # 删除域名最后的斜杠
        self.selenium_login = config.get('selenium_login', False)  # 是否使用模拟登录
        self.is_login = False
        self.request = requests.session()
        # 初始化cookies
        self.__init_cookie()

    def __init_cookie(self):
        """
        初始化cookies
        :return:
        """
        self.cookies = self.get_cookies(self.cookies)
        self.request.cookies.update(self.cookies)

    def __request(self, options):
        """
        请求utils
        :param options: {
            'method': 请求方式,
            'url': 请求url,
            'params': 请求参数,
            'data': 请求数据,
        }
        :return:
        """
        request_methods = {
            'GET': self.request.get,
            'POST': self.request.post,
            'PUT': self.request.put,
            'DELETE': self.request.delete,
        }
        request = request_methods[options.get('method', 'GET')]

        try:
            res = request(self.__get_full_url(options['url']), params=options.get('params', ''),
                          data=options.get('data', ''))
            if res.status_code == 200:
                if check_json(res.text):
                    return res.json()
                else:
                    return res.text
            else:
                return {
                    'code': res.status_code,
                    'msg': res.reason
                }
        except Exception as e:
            logger(msg=f'''__request: {options['url']}: {e}''', level=logging.ERROR)
            return {}

    def __get_full_url(self, path):
        return f'{self.base_url}{path}'

    def get_cookies(self, origin_cookies=''):
        """
        获取 cookies
        :param origin_cookies:
        :return:
        """
        cookie_dict = {}
        try:
            # origin_cookies_file = open_file('./cookies.json')
            if origin_cookies:
                # 从 origin_cookies 字符串获取
                cookie_dict = dict([cookie.split('=', 1) for cookie in origin_cookies.split('; ')])
            # elif origin_cookies_file:
            #     # 从 已保存的文件中获取
            #     cookie_dict = origin_cookies_file

            # 检查cookies是否过期
            self.request.cookies.update(cookie_dict)
            self.is_login = self.check_login()

            # 用户未登录或登录失效
            if not self.is_login:
                # if self.selenium_login:
                #     logger(msg='账户未登录或登录失效，即将进行模拟登录，请在控制台输入相应的登录信息', level=logging.INFO)
                #     # 模拟登录
                #     cookie_dict = self.user_login()
                # else:
                #     logger(msg='模拟登录已关闭，请配置 cookies 进行登录', level=logging.INFO)
                logger(msg='账户未登录或登录失效，请重新配置 cookies 进行登录', level=logging.INFO)

            # if json.dumps(origin_cookies_file) != json.dumps(cookie_dict) and self.is_login:
            #     # 保存cookies，便于下次登录
            #     save_file(cookie_dict, path='./cookies.json')

            return cookie_dict
        except Exception as e:
            logger(msg=f'Failed in [ get_cookies ]: {e}', level=logging.ERROR)
            return cookie_dict

    def user_login(self):
        """
        模拟用户手动登录
        :return:
        """
        cookie_dict = {}
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # 隐藏浏览器窗口
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(executable_path=self.executable_path,
                                  options=options)
        driver.get(self.base_url)
        time.sleep(3)
        driver.find_element_by_id('submit-sso-login').click()
        time.sleep(3)
        input_account = self.account_data['account'] if self.account_data['account'] else input(
            '请输入账户（office365邮箱）：\n')
        driver.find_element_by_name('loginfmt').send_keys(input_account)
        driver.find_element_by_xpath('''//input[@value='下一步']''').click()
        # driver.find_element_by_id('i0116').send_keys(input_account)
        # driver.find_element_by_id('idSIButton9').click()
        time.sleep(1)
        input_password = self.account_data['password'] if self.account_data['password'] else input('请输入密码：\n')
        driver.find_element_by_name('passwd').send_keys(input_password)
        driver.find_element_by_xpath('''//input[@value='登录']''').click()
        # driver.find_element_by_id('i0118').send_keys(input_password)
        # driver.find_element_by_id('idSIButton9').click()
        time.sleep(2)
        input_code = input('请输入验证码：\n')
        driver.find_element_by_name('otc').send_keys(input_code)
        driver.find_element_by_xpath('''//input[@value='验证']''').click()
        # driver.find_element_by_id('idTxtBx_SAOTCC_OTC').send_keys(input_code)
        # driver.find_element_by_id('idSubmit_SAOTCC_Continue').click()
        time.sleep(1)
        driver.find_element_by_xpath('''//input[@value='是']''').click()
        # driver.find_element_by_id('idSIButton9').click()
        time.sleep(5)
        cookies = driver.get_cookies()
        time.sleep(1)
        driver.close()
        cookie_len = len(cookies)
        if cookie_len > 0:
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']

        return cookie_dict

    def user_logout(self):
        return self.__request({'method': 'GET', 'url': '/link'})

    def check_login(self):
        """
        判断是否已登录
        :return:
        """
        try:
            if not self.user_info:
                self.user_info = self.get_user_info()
            result = self.user_info
            if result['data'] and result['data']['email']:
                return True
            else:
                # cookie 失效，退出
                # self.user_logout()
                return False
        except Exception as e:
            logger(msg=f'Failed in [ check_login ]: {e}', level=logging.ERROR)
            return False

    def get_user_info(self):
        """
        获取登录信息
        :return:
        非登录状态 返回结果为
        { 'code': 0, 'data': {} }
        登录状态 返回结果为
        { 'code': 0, 'data': {“email”: “登录邮箱”, ...} }
        """
        return self.__request({'method': 'GET', 'url': '/link'})

    def google_trans(self, query='', to_lang='zh-cn'):
        """
        main 翻译
        :param query:
        :param to_lang:
        :return:
        """
        try:
            data = {'query': query, 'to_lang': to_lang}

            result = ''
            res = self.__request({'method': 'POST', 'url': '/link', 'data': json.dumps(data)})

            if res.get('code') == 0:
                data = res.get('data', {})
                translations = data.get('translations', [{}])
                result = translations[0].get('translatedText')

            return result
        except Exception as e:
            logger(msg=f'Failed in [ google_trans ]: {e}', level=logging.ERROR)
            return ''

    @block_logout
    def search(self, param, is_search=False):
        """
        搜索翻译
        :param is_search: 是否来自查询 是则会处理请求结果后返回，否则直接返回请求结果
        :param param: {
            'search_mode': 搜索类型 key、value,
            'search': 搜索关键字,
            'category': 搜索分类,
            'group': 搜索分组,
            'locales': 搜索语言,
            'page': 页数,
            'page_size': 页结果大小,
            'group_by': 排序
        }
        :return:
        """
        if not param:
            return None
        params = {
            'search_mode': param.get('search_mode', 'key'),
            'search': param.get('search', ''),
            'category': param.get('category', ''),
            'group': param.get('group', ''),
            'locales': param.get('locales', ''),
            'page': param.get('page', '1'),
            'page_size': param.get('page_size', '50'),
            'group_by': param.get('group_by', '1')
        }

        result = {
            'total': 0,
            'list': {}
        }

        res = self.__request({'method': 'GET', 'url': '/link', 'params': params})

        if not is_search:
            return res

        if res['code'] == 0 and res['data'] and res['data']['list']:
            data_list = res['data']['list']
            result['total'] = res['data']['totalCounts']
            for item in data_list:
                result['list'][item['hash_key']] = item['count']

        return result

    @property
    @block_logout
    def category_list(self):
        return self.__request({'method': 'GET', 'url': '/static/config/category-default.json'})

    @block_logout
    def get_detail(self, param, is_search=False):
        """
        获取翻译详情
        :param is_search: 是否来自查询 是则会处理请求结果后返回，否则直接返回请求结果
        :param param: {
            'hash_key': hash_key,
            'page': 页数,
            'page_size': 页结果大小,
            'creation_mode':
        }
        :return:
        """
        params = {
            'hash_key': param.get('hash_key', ''),
            'page': param.get('page', '1'),
            'page_size': param.get('page_size', '10000'),
            'creation_mode': param.get('creation_mode', '0')
        }

        result = {}
        res = self.__request({'method': 'GET', 'url': '/link', 'params': params})

        if not is_search:
            return res

        if res['code'] == 0 and res['data'] and res['data']['list']:
            temp = {
                'key': '',
                'locales': {}
            }
            data_list = res['data']['list']
            temp['key'] = '.'.join([data_list[0]['group'], data_list[0]['key']])

            for item in data_list:
                if item['value']:
                    temp['locales'][item['locales']] = item['value']

            result[param['hash_key']] = temp

        return result

    @block_logout
    def add(self, data):
        """
        新增翻译
        :param data: {'category': category, 'key': key, 'value_type': 'string', 'appid': '_default',
        'group': group, 'locales': 'en_us', 'id': None, 'value': value}
        :return:
        """
        if not data:
            return None

        params = {
            'creation_mode': '1'
        }

        # 将 None 替换为 null
        data = json.dumps(data).replace('None', 'null')

        return self.__request({'method': 'PUT', 'url': '/link', 'params': params, 'data': data})

    @block_logout
    def multi_add(self, multi_data):
        """
        新增多个翻译
        :param multi_data:
        :return:
        """

        def check_exist(x, y):
            return ((True if z.get('key') == y else False) for z in x)

        results = {
            'success': [],
            'failure': []
        }
        multi_data_keys = multi_data.keys()
        for key in multi_data_keys:
            temp = {}
            data = multi_data.get(key)
            category = data[0].get('category')
            group = data[0].get('group')

            hash_key = f'{category}_{group}_{key}'.lower()
            search_result = self.get_detail({'hash_key': hash_key})
            result_data = search_result['data']
            if search_result['code'] == 0 and result_data.get('totalCounts') == 0:
                add_result = self.add(data)
                if add_result.get('code') == 0:
                    temp[hash_key] = '添加成功'
                    results['success'].append(temp)
                else:
                    temp[hash_key] = add_result
                    results['failure'].append(temp)
            else:
                temp[hash_key] = '已存在，添加失败'
                results['failure'].append(temp)

        return results

    @block_logout
    def edit(self, data, path=None):
        """
        修改翻译
        :param data: {
            'category': category,
            'group': group,
            'key': 'key',
            'proposer': '提出者',
            # 修改翻译集合
            'locales': {
                'en_us': 文本,
                ...
            }
        }
        :param path:
        :return:
        """
        category = data.get('category')
        group = data.get('group')
        key = data.get('key')
        locales = data.get('locales')

        if not category or not group or not key:
            return None

        hash_key = f'{category}_{group}_{key}'.lower()
        detail = self.get_detail({'hash_key': hash_key})

        params = {
            'creation_mode': '0'
        }

        if detail['code'] == 0 and detail['data']['totalCounts']:
            local_list = detail['data']['list']
            new_local_list = []
            is_not_edit = True
            for local in local_list:
                if locales.get(local['locales']) != local['value']:
                    is_not_edit = False
                new_local_list.append({
                    **local,
                    'value': locales.get(local['locales'], local['value'])
                })

            if is_not_edit:
                # 没有修改则直接返回旧数据
                return {
                    'code': '0',
                    'data': local_list
                }

            result = self.__request({'method': 'PUT', 'url': '/link', 'params': params,
                                     'data': json.dumps(new_local_list).replace('None', 'null')})

            if result['code'] == 0 and len(result['data']) and path is not None:
                # 保存修改翻译数据到 edit.json 文件
                save_edit_to_file(path, data, local_list)
            return result
        else:
            return {
                'code': -1,
                'msg': f'''key: {'_'.join([category, group, key]).lower()}，不存在'''
            }

    @block_logout
    def multi_edit(self, multi_data, path=None):
        """
        修改多个翻译
        :param multi_data:
        :param path:
        :return:
        """
        if not multi_data or type(multi_data) is not list or not path:
            return None

        results = {
            'success': [],
            'failure': []
        }

        for data in multi_data:
            edit_result = self.edit(data, path)
            edit_key = '_'.join([data.get('category'), data.get('group'), data.get('key')]).lower()
            temp = {}
            code = edit_result.get('code')
            if (code == 0 or code == '0') and len(edit_result.get('data')):
                temp[edit_key] = '修改成功' if code == 0 else '内容相同，未做修改'
                results['success'].append(temp)
            else:
                temp[edit_key] = edit_result
                results['failure'].append(temp)

        return results

    @block_logout
    def delete(self, param=None):
        """
        删除翻译
        :param param: {
            'hash_key': 翻译的hash_key，如 inte_manager_global_test_le
        }
        :return:
        """
        if param is None:
            param = {}

        params = {
            'hash_key': param.get('hash_key', '')
        }

        return self.__request({'method': 'DELETE', 'url': '/link', 'params': params})

    @block_logout
    def multi_delete(self, multi_data):
        """
        删除多个翻译
        :param multi_data:
        :return:
        """
        if type(multi_data) != list:
            return None

        results = {
            'success': [],
            'failure': []
        }

        for key in multi_data:
            res = self.delete({'hash_key': key})
            res_data = res.get('data') or {}
            row_deleted = res_data.get('row_deleted')
            if res.get('code') == 0 and row_deleted > 0:
                results['success'].append({key: f'删除成功[total: {row_deleted}]'})
            elif res.get('code') == 0 and row_deleted == 0:
                results['failure'].append({key: f'不存在，删除失败'})
            else:
                results['failure'].append({key: f'''删除失败[res: {res}]'''})

        return results

    @block_logout
    def sync_cdn(self, category_list):
        """
        同步cdn
        :param category_list:
        :return:
        """
        if not category_list:
            return None
        result = {}
        for category in category_list:
            result[category] = self.__request(
                {'method': 'POST', 'url': '/link', 'data': f'''{{"category":"{category}"}}'''})
        return result

    @block_logout
    def create_release_tag(self, data):
        """
        创建 release tag
        :param data:
        :return:
        """
        release_category = data.get('release_category')
        release_tag = data.get('release_tag')

        if not release_category or not release_tag:
            return None

        params = {
            'create': '1'
        }

        submit_data = f'''{{"release_category":"{release_category}","release_tag":"{release_tag}","data":""}}'''

        return self.__request(
            {'method': 'POST', 'url': '/link', 'params': params, 'data': submit_data})

    @block_logout
    def release_dump(self, release_id):
        """
        同步数据
        :param release_id:
        :return:
        """
        if not release_id:
            return None

        data = f'''{{"release_id":"{release_id}"}}'''

        return self.__request({'method': 'POST', 'url': '/link', 'data': data})

    @block_logout
    def refresh_cdn(self, release_id):
        """
        刷新 cdn
        :param release_id:
        :return:
        """
        if not release_id:
            return None

        data = f'''{{"release_id":"{release_id}"}}'''

        return self.__request({'method': 'POST', 'url': '/link', 'data': data})

    @block_logout
    def release(self, data):
        """
        发布新tag
        :param data:
        :return:
        """
        if not data.get('release_category') or not data.get('release_tag'):
            return None

        create_result = self.create_release_tag(data)
        if create_result['code'] == 201:
            release_id = create_result['data']['id']
            release_result = self.release_dump(release_id)
            sync_result = self.sync_cdn(data.get('release_category'))
            refresh_result = self.refresh_cdn(release_id)
            return {'release_result': release_result, 'sync_result': sync_result, 'refresh_result': refresh_result}
        else:
            return '创建tag失败'

    @block_logout
    def get_release_list(self, param=None):
        """
        获取 release list
        :param param:
        :return:
        """
        if param is None:
            param = {}

        params = {
            'search': param.get('search', ''),
            'page': param.get('page', '1'),
            'page_size': param.get('page_size', '25'),
            'release_category': param.get('release_category', 'common')
        }

        return self.__request({'method': 'GET', 'url': '/link', 'params': params})
