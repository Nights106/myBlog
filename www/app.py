# 编写web骨架
# 网站通过http://localhost:9000 访问，主页返回Hello标题

import logging;logging.basicConfig(level=logging.INFO)
from aiohttp import web

async def index(request):
    return web.Response(body=b'<h1>Hello</h1>',content_type='text/html')

def init():
    app = web.Application()
    # 增加路径到处理函数的路由
    app.add_routes([web.get('/',index)])
    web.run_app(app,host='localhost',port=9000)

if __name__ == '__main__':
    init()
