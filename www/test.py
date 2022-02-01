import asyncio
import orm
from models import User,Blog,Comment


async def test(loop):
    await orm.create_pool(loop=loop,user='root',password='1095391058ly',db='myblog')
    # 测试insert语句是否有效
    # u = User(name='test1',email='test1@qq.com',password='123456',image='about:blank')
    # await u.save() 
    # 注意: 不执行u.save()是没办法进行update和remove的（因为没初始化好）
    # 测试update语句
    # u.name = 'Test1'
    # u.password = '123ascsa'
    # await u.update()

    # 测试u.remove()语句
    u1 = User(name='u1',email='u1@qq.com',password='123456',image='about:blank')
    await u1.save()
    await u1.remove()

    # 测试select语句
    # print(await User.find('000001643693378f2562fadbd9146b7a9a01a74c3df45e8000'))
    # print(await User.findAll(where="name=?",args=['Test']))
    # print(await User.findNumber(selectField='count(*)',where='name=?',args=['Test']))

    orm.__pool.close()
    await orm.__pool.wait_closed()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
