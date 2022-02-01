import time, uuid
from orm import Model,StringField,BooleanField,FloatField
from orm import TextField
# from datetime import datetime

def next_id():
    # 50位的user_id号
    return f'{int(time.time()):015d}{uuid.uuid4().hex}000'

# def get_time():
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     return now

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True,default=next_id)
    email = StringField()
    password = StringField()
    admin = BooleanField(default=False)
    name = StringField()
    image = StringField(column_type='VARCHAR(500)')
    # create_at = DateTimeField(default=get_time)
    created_at = FloatField(default=time.time())

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True,default=next_id)
    user_id = StringField()
    user_name = StringField()
    user_image = StringField(column_type='VARCHAR(500)')
    name = StringField()
    summary = StringField(column_type='VARCHAR(200)')
    content = TextField()
    # create_at = DateTimeField(default=get_time)
    created_at = FloatField(default=time.time())

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True,default=next_id)
    blog_id = StringField()
    user_id = StringField()
    user_name = StringField()
    user_image = StringField(column_type='VARCHAR(500)')
    content = TextField()
    created_at = FloatField(default=time.time())