# 配置文件可以直接用python的字典来实现
# 更专业的配置配置文件可以使用.properties和.yaml实现

# config_default文件作为本地开发的标准配置
configs = {
    'debug': True,
    'db': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '1095391058ly',
        'db': 'myblog'
    },
    'session': {
        'secret': 'Awesome'
    }
}