"""
Entry point of ZugZwang.
"""

import os
from pathlib import Path

from zugzwang.group import Group
from zugzwang.menu import GroupMenu
from zugzwang.gui import ZugGUI

if __name__ == '__main__':
    top_level_group_path = Path(
        '/Users/joshuablinkhorn/Training/Tabias'        
        #'/Users/joshuablinkhorn/Training/Collections-Tabia-Trial'
    )
    user_data = Group(top_level_group_path)
    GroupMenu(user_data).display()
