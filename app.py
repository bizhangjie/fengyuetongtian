from flask import Flask, jsonify, abort
import json
from api.fengyuetongtian import WebScraper

app = Flask(__name__)

# 使用示例
webdriver_path = "I://Chrome/chromedriver.exe"  # 替换为你的WebDriver路径
scraper = WebScraper(webdriver_path)

# 获取所有任务
@app.route('/api/home', methods=['GET'])
def get_index():
    json_data = scraper.get_home()
    data = json.loads(json_data)
    return jsonify(data)

# 获取单个任务
@app.route('/api/m3u8/<path:url>', methods=['GET'])
def get_m3u8(url):
    json_data = scraper.get_url(url)
    data = json.loads(json_data)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Task not found'}), 404

# 创建任务
@app.route('/api/search/<string:wd>/<int:pg>', methods=['GET'])
def search(wd, pg):
    if not wd or not pg:
        abort(400, '关键字和页数不能为空')
    json_data = scraper.get_search(wd, pg)
    data = json.loads(json_data)
    return jsonify(data)

# 错误处理
@app.errorhandler(400)
def bad_request(error):
    response = jsonify({'error': error.description})
    response.status_code = 400
    return response

if __name__ == '__main__':
    app.run()