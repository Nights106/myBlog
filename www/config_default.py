# 配置文件可以直接用python的字典来实现
# 更专业的配置配置文件可以使用.properties和.yaml实现

configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'www-data',
        'password': 'www-data',
        'db': 'awesome'
    },
    'session': {
        'secret': 'Awesome'
    }
}