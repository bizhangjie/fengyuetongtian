import json
import re
import execjs
import redis
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class WebScraper:
    def __init__(self, webdriver_path):
        self.webdriver_path = webdriver_path
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    # 获取首页内容
    def get_home(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 启用无头模式
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")

        service = Service(self.webdriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        host_url = "https://www.fengyuetongtian.com"  # 页面的URL
        driver.get(host_url)

        html_content = driver.page_source

        driver.quit()

        soup = BeautifulSoup(html_content, 'lxml')

        data = []
        for div_box in soup.find_all(class_='stui-vodlist__box'):
            title = div_box.find('h4', class_='title').text.strip()
            link = div_box.find('a')['href']
            image_url = div_box.find('a', class_='stui-vodlist__thumb')['data-original']
            view_count = div_box.find(class_='pic-text').text

            item = {
                "title": title,
                "link": host_url + link,
                "url": image_url,
                "view": view_count
            }
            data.append(item)

        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        return json_data

    # 根据js中的解密，进行解密
    def get_m3u8(self, url):
        # 获取适合系统环境的 JavaScript 执行器
        ctx = execjs.get()

        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 构造 JavaScript 文件的完整路径
        js_file_path = os.path.join(script_dir, 'play.js')

        # 加载外部的 JavaScript 文件，播放地址的解密
        with open(js_file_path, 'r', encoding='utf-8') as file:
            js_code = file.read()

        # 编译 JavaScript 代码
        compiled = ctx.compile(js_code)

        # 调用 JavaScript 函数
        result = compiled.call('decodeURLString', url)
        return result

    # 从网页中获取加密的url内容
    def get_url(self, host_url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 启用无头模式
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")

        service = Service(self.webdriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        if self.redis_client.exists(host_url):
            # 缓存存在，从Redis中获取数据
            print('缓存存在，从Redis中获取数据')
            json_data = self.redis_client.get(host_url).decode('utf-8')
        else:
            # 缓存不存在，执行下面的操作获取数据
            print('缓存不存在，执行下面的操作获取数据')
            driver.get(host_url)

            # 获取页面内容
            html_content = driver.page_source

            # 关闭浏览器
            driver.quit()

            soup = BeautifulSoup(html_content, 'lxml')

            title = soup.find('h1').text
            jpg = soup.find(class_='stui-vodlist__thumb').attrs['data-original']
            enstr = re.findall('},"url":"(.*?)","url_next"', str(soup))[0]

            json_data = {'title': title, 'jpg': jpg, 'm3u8': self.get_m3u8(enstr)}

            # 将数据保存到Redis缓存
            json_data = json.dumps(json_data, ensure_ascii=False, indent=4)
            self.redis_client.set(host_url, json_data)
        return json_data

    # 根据关键字搜索
    def get_search(self, wd, pg):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 启用无头模式
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")

        service = Service(self.webdriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        host_url = f"https://www.fengyuetongtian.com/vodsearch/{wd}----------{pg}---.html"  # 页面的URL

        if self.redis_client.exists(host_url):
            # 缓存存在，从Redis中获取数据
            print('缓存存在，从Redis中获取数据')
            json_data = self.redis_client.get(host_url).decode('utf-8')
        else:
            # 缓存不存在，执行下面的操作获取数据
            print('缓存不存在，执行下面的操作获取数据')

            driver.get(host_url)
            parsed_url = urlparse(host_url)
            host = parsed_url.netloc

            html_content = driver.page_source
            driver.quit()

            soup = BeautifulSoup(html_content, 'lxml')

            data = []
            for div_box in soup.find_all(class_='stui-vodlist__box'):
                title = div_box.find('h4', class_='title').text.strip()
                link = div_box.find('a')['href']
                image_url = div_box.find('a', class_='stui-vodlist__thumb')['data-original']
                view_count = div_box.find(class_='pic-text').text

                item = {
                    "title": title,
                    "link": host + link,
                    "url": image_url,
                    "view": view_count
                }
                data.append(item)

            json_data = json.dumps(data, ensure_ascii=False, indent=4)
            self.redis_client.setex(host_url, 86400, json_data)

        return json_data

# # 使用示例
# webdriver_path = "I://Chrome/chromedriver.exe"  # 替换为你的WebDriver路径
# scraper = WebScraper(webdriver_path)
# json_data = scraper.get_home()
# print(json_data)


# # 使用示例
# webdriver_path = "I://Chrome/chromedriver.exe"  # 替换为你的WebDriver路径
# scraper = WebScraper(webdriver_path)
# json_data = scraper.get_url("https://www.fengyuetongtian.com/vodplay/345902-1-1.html")
# print(json_data)

# # 使用示例
# webdriver_path = "I://Chrome/chromedriver.exe"  # 替换为你的WebDriver路径
# scraper = WebScraper(webdriver_path)
# json_data = scraper.get_search("学生", 1)
# print(json_data)