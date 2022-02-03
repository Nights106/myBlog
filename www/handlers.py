import re,time,json,logging,hashlib,base64,asyncio
import markdown
from models import User,Comment,Blog,next_id
from coroweb import get,post
from aiohttp import web
from config import configs
from apis import Page,APIValueError,APIResourceNotFoundError


@get('/')
async def index(request):
    users = await User.findAll()
    return{
        '__template__': 'test.html',
        'users': users
    }
    # return web.Response(b'<h1>Hello World</h1>')

@get('/api/users')
async def api_get_users(request):
    users = await User.findAll(orderBy='created_at desc',limit=(0,8))
    for u in users:
        u.password = '******'
    return dict(users=users)