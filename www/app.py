# 编写web骨架
# 网站通过http://localhost:9000 访问，主页返回Hello标题

from calendar import month
import logging
from tkinter.messagebox import RETRYCANCEL
from unittest import runner
from warnings import filters;logging.basicConfig(level=logging.INFO)
from aiohttp import request, web
import asyncio,os,json,time
from datetime import datetime 
from jinja2 import Environment,FileSystemLoader

import orm
from config import configs
from coroweb import add_routes,add_static

async def index(request):
    return web.Response(body=b'<h1>Hello</h1>',content_type='text/html')

def init_jinja2(app,**kw):
    logging.info('初始化jinja2...')
    options = dict(
        autoescape = kw.get('autoescape',True),
        block_start_string = kw.get('block_start_string','{%'),
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),
        variable_end_string = kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if not path:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'tamplates')
    logging.info(f'设置jinja2模版路径：{path}')
    env = Environment(loader=FileSystemLoader(path),**options)
    # 在调用处传入了一个字典
    filters = kw.get('filters',None) # 过滤器是个什么概念呢？
    if filters:
        for name,f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env # jinja2的配置都在env中，将其设置为app的一个属性，方便调用

# 用于jinja2模版上，便于显示时间
def datetime_filter(t):
    time.time() # 时间戳以秒为单位
    delta = int(time.time()-t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta <86400:
        return u'%s小时前' % (delta // 3600)
    if delta <604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s-%s-%s %s:%s:%s' % (dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)


# 打印http请求的信息的中间件
async def logger_factory(app,handler):
    async def logger(request):
        logging.info(f'请求: {request.method} {request.path}')
        return (await handler(request))
    return logger


async def auth_factory(app,handler):
    pass

# 数据处理工厂（不是中间件？）
async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startwith('application/json'):
                request.__data__ = await request.json()
                logging.info(f'request json: {str(request.__data__)}')
            elif request.content_type.startwith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info(f'request form: {str(request.__data__)}')
        return (await handler(request))
    return parse_data


# 响应处理中间件，将服务器返回的响应处理成aiohttp的web.response格式
# 这里的得到的r到底是个啥？？？
# handler返回的响应？？？
async def response_factory(app,handler):
    async def response(request):
        logging.info('Responde handler...')
        r = await handler(request)
        # 在网络中传输的响应得是bytes的形式
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template = r.get('__template__')
            # 不存在模版就是一个json数据
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            # 有模版，就加载模版
            else:
                # r['__user__'] = request.__user__
                tp = app['__templating__'].get_template(template).render(**r) #render后是个啥？
                resp = web.Response(tp.encode('utf-8'))
                resp.content_type = 'text/htmlc;charset=utf-8'
                return resp
        if isinstance(r,int) and (r>=100 and r<600):
            return web.Response(r)
        if isinstance(r,tuple) and len(r) == 2:
            t,m = r
            if isinstance(t,int) and t>=100 and t<600:
                return web.Response(t,str(m))
        # 默认情况不处理直接当成明文返回
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response



async def init(loop):
    await orm.create_pool(loop=loop,**configs.db)
    app = web.Application(middlewares=[logger_factory,response_factory])
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    add_routes(app,'handlers')
    add_static(app)
    # 引入runner是否是因为要使用协程？
    runner = web.AppRunner(app)
    await runner.setup()
    server = web.TCPSite(runner,'localhost',9000)
    logging.info('服务器启动在 http://127.0.0.1:9000')
    await server.start()


# def init():
#     app = web.Application()
#     # 增加路径到处理函数的路由
#     app.add_routes([web.get('/',index)])
#     web.run_app(app,host='localhost',port=9000)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

