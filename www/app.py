import logging

from flask import app;logging.basicConfig(level=logging.INFO)
from aiohttp import web

async def index(request):
    return web.Response(body=b'<h1>Hello</h1>',content_type='text/html')

def init():
    app = web.Application()
    app.add_routes([web.get('/',index)])
    web.run_app(app,host='localhost',port=9000)

if __name__ == '__main__':
    init()
