from .history import BiliHistory
from .space import BiliSpace

class BiliAPI(BiliHistory, BiliSpace):
    pass

__all__ = ['BiliAPI']
