import asyncio,os,inspect,logging
import functools

from urllib import parse
from aiohttp import web
from apis import APIError



# 装饰器，给被装饰的函数
def get(path):
    def decorator(func):
        @functools.wraps(func) # 函数的名字还是func
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__ = 'GET' # 方法是get，路径是path
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

# 使用RequestHandler()封装一个URL处理函数
# 处理request，从中获取URL参数

# 一些RequestHandler用来获取函数参数的函数

# 关于inspect.Parameter 的  kind 类型有5种：
# POSITIONAL_ONLY		只能是位置参数
# POSITIONAL_OR_KEYWORD	可以是位置参数也可以是关键字参数
# VAR_POSITIONAL			相当于是 *args
# KEYWORD_ONLY			关键字参数且提供了key
# VAR_KEYWORD			相当于是 **kw

# 获取函数fn无默认值的命名关键字参数
def get_required_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args) # 为什么返回一个tuple？？？

# 获取fn的命名关键字参数
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

# 判断函数fn是否含有命名关键字参数
def has_named_kw_args(fn):
    # args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

# 判断函数fn是否含有可变关键字参数
def has_var_kw_arg(fn):
    # args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

# 判断函数fn是否含有request这个位置参数
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name,param in params.items():
        if(name == 'request'):
            found = True
            continue
        if found and (param.kind!=inspect.Parameter.VAR_KEYWORD and param.kind!=inspect.Parameter.VAR_POSITIONAL and param.kind!=inspect.Parameter.KEYWORD_ONLY):
            raise ValueError(f'request参数必须是最后一个位置参数，在函数{fn.__name__}{str(sig)}中')
    return found 

# RequestHandler的目的：分析URL处理函数需要接收的参数，并从web.request对象中获取必要的参数
# 调用URL处理函数，将结果转换为web.response对象
# 相当于是封装了一个比aiohttp更高级的web框架

# 一个实例只能分析一个函数？？？
class RequestHandler(object):
    def __init__(self,app,fn):
        self._app = app
        # self._func = fn
        self._func = asyncio.coroutine(fn)
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)
    
    # 实例u, u(request)即可处理请求request并返回响应？
    # call(fn)的作用就是把request中的参数提取出来，组装成一个字典kw
    # 将提取出来的request中的参数，组装成kw后喂给函数fn（所以需要使用inspect分析fn的参数结构）
    # 函数fn的参数来源有：
    #   request路径中/{param}/...形式的参数
    #   post请求，根据请求的content_type，有request.json()和request.post()两种形式
    #   request参数
    async def __call__(self,request):
        kw = None 
        # 如果函数fn有关键字参数（命名+可变），在request请求中把这些参数提取出来
        if self._has_named_kw_args or self._has_var_kw_arg or self._required_kw_args:
            # 根据方法的不同去提取参数  ？
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest(text='POST请求遗漏了content_type字段')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest(text='JSON格式错误')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startwith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params) # 这里为什么不检查一下form的格式呢？
                else:
                    return web.HTTPBadRequest(text=f'不支持的content_type类型：{request.content_type}')

            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k,v in parse.parse_qs(qs,True).items():
                        kw[k] = v[0]
        # 没有关键字参数或者没在请求中
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._has_named_kw_args:
                # 函数fn没有可变关键字参数，除去request中提供的不合法参数
                copy = dict()
                for k in kw:
                    if k in self._named_kw_args:
                        copy[k] = kw[k]
                kw = copy
            # 添加路径中的参数
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning(f'位置参数和关键字参数重复：{k}')
                kw[k] = v
        
        # 加入request参数
        if self._has_request_arg:
            kw['request'] = request

        # 检查无默认值的关键字参数是否提供
        if self._required_kw_args:
            for k in self._required_kw_args:
                if not k in kw:
                    return web.HTTPBadRequest(text=f'缺少参数：{k}')
        
        
        logging.info(f'调用参数：{str(kw)}')
        try:
            r = await self._func(**kw)
            logging.info(f'返回处理结果：{r}')
            return r
        except APIError as e:
            return dict(error=e.error,data=e.data,message=e.message)

# 接下来几个函数没看太懂在干啥。。。
# 定义add_static函数，注册static文件夹下的文件
def add_static(app):
    # __file__ = '.'? 看意思好像是这样
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info(f"添加静态页面路径{'/static/'} ==> {path}")

# 自定义的add_route函数，用来注册一个URL处理函数
def add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)

    if not path or not method:
        # s = '函数%s需要被@get或者@post装饰' % fn.__name__
        # raise ValueError(s) 
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info(f"添加路由{method} {path} => {fn.__name__}({','.join(inspect.signature(fn).parameters.keys())})")
    app.router.add_route(method,path,RequestHandler(app,fn))

# 使用add_route函数自动注册
def add_routes(app,module_name):
    logging.info(f'根据模块{module_name}构建路由表...')
    n = module_name.rfind('.')
    if n == -1:
        mod = __import__(module_name,globals(),locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name,globals(),locals(),[name]),name)
    # logging.info(f'模块的所有属性：{dir(mod)}')
    for attr in dir(mod): # 查看mod模块里的所有属性
        if attr.startswith('_'): # 排除私有属性
            continue
        fn = getattr(mod,attr) # 非私有属性属性
        if callable(fn): # 是函数
            # if fn.__name__ == 'index':
            #     logging.info(f'index函数的属性：{dir(fn)}')
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__route__',None)
            # logging.info(f'{fn} ==> {method} {path}')
            if method and path: # 是函数且被装饰过
                # logging.info(f'添加路由：{method} {path} ==> {fn}')
                add_route(app,fn) # 添加到路由表




