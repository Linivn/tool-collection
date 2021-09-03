# -*- coding = utf-8 -*-
import os
import re
import time
import requests

from lxml import etree
from browsermobproxy import Server
from selenium import webdriver


class Monitor(object):
    def __init__(self, config):
        # browsermob-proxy的存放路径，请自行下载并替换路径
        # 下载地址：https://github.com/lightbody/browsermob-proxy
        self.proxy_path = config.get('proxy_path',
                                     'E:/dev/software/webdriver/browsermob-proxy-2.1.4/bin/browsermob-proxy.bat')
        # chromedriver的存放路径，请自行下载与当前chrome浏览器版本对应的版本，并替换路径
        # 下载地址：http://npm.taobao.org/mirrors/chromedriver
        self.driver_path = config.get('driver_path', 'E:/dev/software/webdriver/chromedriver.exe')
        self.driver_prefs = config.get('driver_prefs', {})
        self.driver_argument = config.get('driver_argument', [])
        # 启动
        self.start()

    def __init_proxy(self):
        self.server = Server(self.proxy_path)
        self.server.start()
        self.proxy = self.server.create_proxy()
        self.proxy.blacklist(
            ['*css*', '*jpg*', '*png*', '*gif*', '*baidu*', '*google*'], 200)

    def __init_webdriver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'''--proxy-server={'localhost'}:{self.proxy.port}''')
        chrome_options.add_argument('--ignore-certificate-errors')
        # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--disable-gpu')

        for argument in self.driver_argument:
            chrome_options.add_argument(argument)

        chrome_options.add_experimental_option('prefs', {
            **{'profile.managed_default_content_settings.images': 2},
            **self.driver_prefs
        })
        self.driver = webdriver.Chrome(executable_path=self.driver_path, options=chrome_options)

    def __create_capture(self, name='monitor', options=None):
        if options is None:
            options = {'captureContent': True}
        self.proxy.new_har(name, options=options)

    def get_log_entries(self):
        try:
            if self.proxy.har['log']['entries']:
                return self.proxy.har['log']['entries']
            return []
        except Exception as err:
            print(err)
            return []

    def start(self):
        try:
            self.__init_proxy()
            self.__init_webdriver()
            self.__create_capture()
        except Exception as err:
            print(err)

    def quit(self):
        self.driver.close()
        self.driver.quit()
        try:
            self.proxy.close()
            self.server.process.terminate()
            self.server.process.wait()
            self.server.process.kill()
        except OSError:
            pass


def get_page_content(url):
    """
    获取播放页面的源代码
    :param url:
    :return:
    """
    response = requests.get(url, headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51'})
    response.encoding = 'utf-8'
    return response.text


def get_play_list(url, xpath=None, selected=False):
    """
    获取播放列表链接
    :param url: 播放页面链接
    :param xpath: 剧集名称、播放列表、集数名称的xpath配置
    :param selected: 是否仅获取传入的url一个播放链接
    :return:
    """
    if xpath is None:
        xpath = {}

    res = get_page_content(url)
    res_tree = etree.HTML(res)
    result = {}
    domain = re.findall(re.compile(r'[a-zA-Z]+://[^\s/]*\.[a-zA-Z0-9]+'), url)[0]
    video_title = res_tree.xpath(xpath.get('video_title'))[0]
    video_title = video_title.replace(' ', '')
    play_nodes = res_tree.xpath(xpath.get('play'))

    for item in play_nodes:
        title = f'''{video_title}-{item.xpath(xpath.get('episode_title'))[0]}'''
        play_url = f'''{domain}{item.xpath('./@href')[0]}'''
        if selected and item.get('class') == 'selected':
            return {title: play_url}
        result[title] = play_url

    return result


def get_m3u8_url(url_list):
    """
    获取m3u8链接
    :param url_list: 播放列表
    :return:
    """
    result = {}

    for k, v in url_list.items():
        print('加载页面:', k, v, end='')
        monitor.driver.get(v)
        time.sleep(1)
        logs = monitor.get_log_entries()
        for log in logs:
            # print(log['request']['url'])
            if re.match(r'.+m3u8$', log['request']['url']):
                result[k] = log['request']['url']
        print(' =>', result.get(k, '获取m3u8失败'), '\n')
    return result


def download_video(url_list, config):
    """
    借助N_m3u8DL-CLI下载m3u8资源，并最终合成视频
    :param url_list:
    :param config:
    :return:
    """
    with open('./download_video.bat', mode='w+', encoding='gbk') as file:
        index = 0
        for k, v in url_list.items():
            if index != 0:
                # 延时3秒，避免N_m3u8DL生成的日志文件名称相同导致下载报错
                file.write(f'timeout /t 3')
                file.write('\n')
            title_list = k.split('-')
            file.write(
                f'''start cmd /k""{config['m3u8dl_path']}" "{v}" --enableDelAfterDone --workDir "{config['work_path']}/{title_list[0]}" --saveName "{title_list[1]}""\n''')
            index += 1
    # 执行批处理文件 download_video.bat
    os.system('download_video.bat')


if __name__ == '__main__':
    """
    Selenium + Browsermob-Proxy获取浏览器Network请求和响应，从而获取得到m3u8链接
    需要先安装依赖：requests、browsermob-proxy、selenium
    """
    # xpath => video_title：剧集名称、episode_title：集数名称、play：播放列表
    # 获取播放链接
    play_list = get_play_list('http://dianying.im/paly-61255-1-1/', xpath={
        'video_title': '//*[@class="video-info-header"]/h1/a/text()',
        'episode_title': './span/text()',
        'play': '//*[@id="main"]/div[1]/div/div[3]/div[2]/div/div/a'
    })
    print('play_list:', play_list, '\n')

    if play_list:
        # 初始化 Monitor
        monitor = Monitor({
            # browsermob-proxy的存放路径，请自行下载并替换路径
            # 下载地址：https://github.com/lightbody/browsermob-proxy
            # 'proxy_path': '',
            # chromedriver的存放路径，请自行下载与当前chrome浏览器版本对应的版本，并替换路径
            # 下载地址：http://npm.taobao.org/mirrors/chromedriver
            # 'driver_path': '',
            # chromedriver相关配置
            'driver_argument': [
                "user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51'",
                '--disable-blink-features=AutomationControlled',
                '--headless',
                # 'window-size=1920x1000',
                'blink-settings=imagesEnabled=false',
                'disable-infobars',
                '--disable-extensions'
            ]
        })

        # 获取m3u8链接
        m3u8_list = get_m3u8_url(play_list)
        print('m3u8_list:', m3u8_list, '\n')

        # 关闭 Monitor
        monitor.quit()

        if m3u8_list:
            print('开始下载', '\n')
            download_video(m3u8_list, {
                # N_m3u8DL的存放路径，请自行下载并替换路径
                # 下载地址：https://github.com/nilaoda/N_m3u8DL-CLI/releases
                'm3u8dl_path': 'E:/Program Files (x86)/N_m3u8DL/N_m3u8DL-CLI_v2.9.7.exe',
                # 下载保存目录
                'work_path': 'D:/111222'
            })
        else:
            print('爬取失败')
    else:
        print('爬取失败')
