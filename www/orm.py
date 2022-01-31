import asyncio,aiohttp,aiomysql
from email.policy import default
from unittest import result
from operator import ge
from email import charset
from webbrowser import get
import logging

logging.basicConfig(level=logging.INFO)

# 打印日志的函数
def log(sql,args=()):
    if args:
        logging.info(sql % args)
        # print(sql % args)
    else:
        logging.info(sql)
        # print(sql)

def create_args_string(num):
    return ','.join(['?']*num)

async def create_pool(loop,**kw):
    log('创建连接池...')
    global __pool
    # create_pool的用法？
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port','3306'),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('cahrset','utf8'),
        autocommit = True,
        loop=loop
    )

#封装SQL的select语句
async def select(sql,args,size=None):
    log(sql.replace('?','%'),args)
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?','%s'),args)
        if size:
            res = cur.fetchmany(size)
        else:
            res = cur.fetchall()
        await cur.close()
        log(f'SELECT操作返回了{len(res)}行数据')
        return res

# 封装insert、update和delete语句
async def execute(sql,args):
    log(sql.replace('?','%'),args)
    with (await __pool) as conn:
        # 修改操作可能会报错
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            await cur.close()
            log(f'修改操作影响了{affected}行数据')
        except BaseException:
            log('修改数据库失败')
            raise
        return affected

# 定义字段值的类型及其子类
class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return f'<{self.__class__.__name__}:{self.name},{self.column_type}>'

class StringField(Field):
    def __init__(self, name, column_type='VARCHAR(100)', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)

class IntegerField(Field):
    def __init__(self, name, column_type='BIGINT', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)

class FloatField(Field):
    def __init__(self, name, column_type = 'DOUBLE', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)

class BooleanField(Field):
    def __init__(self, name, column_type = 'BOOLEAN', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)
    
class DateTimeField(Field):
    def __init__(self, name, column_type = 'DATETIME', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)


# 定义Model元类

class ModelMetaClass(type):
    def __new__(cls,name,bases,attrs):
        # Model基类不进行处理
        if name == 'Model':
            return super().__new__(cls,name,bases,attrs)
        # 获得类名到表名的映射
        tableName = attrs.get('__table__',None) or name
        log(f'发现ORM模型: 类{name} ==> 表{tableName}')
        # 获取所有字段名和主键名
        mappings = dict()
        # ------------------------------
        # Fields 和 primaryKey中存的是类的属性值，而不是表的字段值
        # 因此正常使用时，一定要设置字段值名称等于对应的属性值
        fields = [] # 除了主键以外的字段
        primaryKey = None # 主键字段
        for k,v in attrs.items():
            if isinstance(v,Field):
                log(f'发现映射: 属性{k} ==> 字段{v}')
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError(f'重复的主键: {k}')
                    primaryKey = k
                else:
                    fields.append(k) ###为什么append(k)???
        if not primaryKey:
            raise RuntimeError('表缺少主键')
        for k in mappings.keys():
            attrs.pop(k)
        # 以下代码添加属性，但还不太清楚具体是要干啥
        attrs['__table__'] = tableName
        attrs['__mappings__'] = mappings 
        attrs['__primaryKey__'] = primaryKey
        attrs['__fields__'] = fields
        # 构造默认的SQL语句,先放一下。。。
        attrs['__select__'] = 'select %s, %s, from %s' % (primaryKey,','.join(fields),tableName)
        attrs['__insert__'] = 'insert into %s, (%s, %s) values (%s)' % (tableName, ','.join(fields),primaryKey,create_args_string(len(fields)+1))
        attrs['__update__'] = 'update %s set %s where %s = ?' % (tableName,','.join(map(lambda f:f'{mappings[f].name}=?' ,fields)),primaryKey)
        attrs['__delete__'] = 'delete from %s where %s = ?' % (tableName,primaryKey)
        return super().__new__(cls,name,bases,attrs)

class Model(dict,metaclass=ModelMetaClass):
    # 初始化，因为继承了dict，所以有没有不太重要的样子
    def __init__(self,**kw):
        return super().__init__(self,**kw)
    
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f'{self.__class__.__name__}中不存在属性{key}')

    def __setattr__(self,key,value):
        self[key] = value
    
    # 获取属性的值
    def getValue(self,key):
        return getattr(self,key,None)
    
    # 获取属性的值，有表的字段默认值，就填充，没有就返回None
    # 用于处理实例初始化缺少字段的情况
    def getValueOrDefault(self,key):
        value = self.getValue(self,key)
        if not value:
            field = self.__mappings__[key]
            if not field.default:
                value = field.default() if callable(field.default) else field.default
                log(f'为{key}填充了默认值{value}')
                setattr(self,key,value)
        return value

    # 查询操作
    # 根据子类主键的值查找记录
    @classmethod
    async def find(cls,pk):
        sql = cls.__select__ + f' where {cls.__primaryKey__} = ?'
        res = await select(sql,pk,1)
        if len(res) == 0:
            return None
        return cls(**res[0])
        # 实现了user = await User.find('123')这样根据id查找用户信息的功能

    @classmethod
    async def findAll(cls,where=None,args=None,**kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        
        if not args:
            args = []

        orderBy = kw.get('order by',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        
        groupBy = kw.get('group by',None)
        if groupBy:
            sql.append('group by')
            sql.append(groupBy)
        
        limit = kw.get('limit',None)
        if limit:
            sql.append('limit')
            if isinstance(limit,int):
                args.append(limit)
                sql.append('?')
            elif isinstance(limit,tuple) and len(limit)==2:
                args.extend(limit)
                sql.append('?,?')
            else:
                raise ValueError(f'错误的limit值: {limit}')
        res = await select(' '.join(sql),args)
        return [cls(**r) for r in res] # 这一行没看明白为啥行
    


    @classmethod
    async def findNumber(cls,selectField,alias=None,where=None,args=None):
        if alias:
            sql = [f'select {selectField} {alias} from {cls.__table__}']
        else:
            sql = [f'select {selectField} from {cls.__table__}']
        if where:
            sql.append('where')
            sql.append(where)
        res = await select(sql,args,1)
        if len(res) == 0:
            return None
        else:
            return res[0]

    # 插入操作
    # 将实例存储到数据库
    # user = User(id=123, name='Michael')
    # yield from user.save()  
    async def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primaryKey__))
        sql = self.__insert__
        rows = await execute(sql,args)
        if rows != 1:
            logging.warn(f'插入数据失败；影响数据库行数: {rows}')
        else:
            log('插入数据库成功！')

    async def update(self):
        args = list(map(self.getValue,self.__fields__))
        args.append(self.getValue(self.__primaryKey__))
        # primaryKey = self.__primaryKey__
        sql = self.__update__
        rows = await execute(sql,args)
        if rows != 1:
            logging.warn(f'更新数据失败；影响数据库行数: {rows}')
        else:
            log(f'更新数据成功！影响数据库行数: {rows}')


    async def remove(self):
        args = self.getValue(self.__primaryKey__)
        sql = self.__delete__
        rows = await execute(sql,args)
        if rows != 1:
            logging.warn(f'删除数据失败；影响数据库行数: {rows}')
        else:
            log(f'删除数据成功！影响数据库行数: {rows}')









