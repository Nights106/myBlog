import json,logging,inspect,functools
from math import ceil

# Page类用于处理分页，改变page_size可以改变每页项目的个数
class Page(object):
    def __init__(self,item_count,page_index=1,page_size=8):
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = ceil(item_count/page_size)
        if (item_count==0) or (page_index>self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else: 
            self.page_index = page_index
            self.offset = self.page_count*(page_index-1)
            self.limit = page_size
        self.has_next = self.page_count>self.page_index
        self.has_previous = self.page_index>1
    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)
    
    __repr__ = __str__

class APIError(Exception):
    def __init__(self,error,data='',message=''):
        super().__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    def __init__(self,field,message=''):
        super().__init__('value:invalid',field,message)

class APIResourceNotFoundError(APIError):
    def __init__(self,field,message=''):
        super().__init__('value:notfound',field,message)

class APIPermissionError(APIError):
    def __init__(self,message=''):
        super().__init__('permission:forbidden','permission',message)

