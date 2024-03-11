"""
Entry point of ZugZwang.
"""

from typing import List, Optional
import os
import pathlib

from zugzwang.group import Group, Tabia, Item, DefaultIOManager
from zugzwang.menu import GroupMenu
from zugzwang.gui import ZugGUI

def is_excluded(filename: str):
    return "." in filename and not filename.endswith(".pgn")

def search_dir(
        path: pathlib.Path,
        parent: Group,
) -> List[Item]:
    
    names: List[str] = [
        name
        for name in sorted(os.listdir(path))
        if not is_excluded(name)
    ]
    items: List[Item] = []

    for name in names:
        if name.endswith('.pgn'):
            tabia = Tabia(
                name=name[:-4],
                parent=parent,
                io_manager=io_manager,
            )
            items.append(tabia)
        else:
            group = initialise_group(
                name=name,
                path=path / name,
                io_manager=io_manager,
                parent=parent,
            )
            items.append(group)
    
    return items

def initialise_group(
        name: str,
        path: pathlib.Path,
        io_manager: DefaultIOManager,
        parent: Optional[Group]=None      
) -> Group:
    group = Group(
        name=name,
        parent=parent,
    )
    io_manager.register_group(group, path)
    for item in search_dir(path, group):
        group.add_child(item)

    return group

if __name__ == '__main__':
    data_path = pathlib.Path(
        #'/Users/joshuablinkhorn/Training/Tabias'        
        #'/Users/joshuablinkhorn/Training/Collections-Tabia-Trial'
        '/Users/joshuablinkhorn/Training/Collections'        
    )
    io_manager = DefaultIOManager()
    user_data = initialise_group("UserData", data_path, io_manager)
    user_data.update_stats()
    GroupMenu(user_data).display()
