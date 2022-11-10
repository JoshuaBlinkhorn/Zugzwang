"""
Entry point of ZugZwang.
"""

import os

from zugzwang.group import ZugUserData
from zugzwang.menu import ZugMainMenu

if __name__ == '__main__':
    collections_dir_path = os.path.join(os.getcwd(),'../Collections')
    user_data = ZugUserData(collections_dir_path)
    ZugMainMenu(user_data).display()
