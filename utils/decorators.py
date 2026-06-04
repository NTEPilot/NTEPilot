from typing import Callable, Generic, TypeVar

T = TypeVar("T")

class cached_property(Generic[T]):
    """带类型支持的缓存属性装饰器。

    来源: https://github.com/pydanny/cached-property
    原始实现: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76

    每个实例只计算一次属性值，之后替换为普通属性。
    删除该属性后会重置缓存。
    """

    def __init__(self, func: Callable[..., T]):
        self.func = func

    def __get__(self, obj, cls) -> T:
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def del_cached_property(obj, name):
    """安全地删除缓存属性。

    Args:
        obj: 目标对象。
        name: 属性名称。
    """
    try:
        del obj.__dict__[name]
    except KeyError:
        pass


def has_cached_property(obj, name):
    """检查属性是否已被缓存。

    Args:
        obj: 目标对象。
        name: 属性名称。

    Returns:
        如果属性已缓存则返回 True，否则返回 False。
    """
    return name in obj.__dict__


def set_cached_property(obj, name, value):
    """设置缓存属性。

    Args:
        obj: 目标对象。
        name: 属性名称。
        value: 属性值。
    """
    obj.__dict__[name] = value

def run_once(f):
    """确保函数只执行一次，无论被调用多少次。

    Examples:
        @run_once
        def my_function(foo, bar):
            return foo + bar

        while 1:
            my_function()

    Examples:
        def my_function(foo, bar):
            return foo + bar

        action = run_once(my_function)
        while 1:
            action()
    """

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper