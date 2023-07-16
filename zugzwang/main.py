import os

from zugzwang.display import ZugDisplay
from zugzwang.menu_scene import ZugInitialScene
from zugzwang.group import ZugUserData

if __name__ == '__main__':
    collections_dir_path = os.path.join(os.getcwd(),'../Collections')
    user_data = ZugUserData(collections_dir_path)
    display = ZugDisplay()
    #fen = ZugFenCreator(display)
    #display.push_scene(fen)
    scene = ZugInitialScene(display, user_data)
    display.push_scene(scene)
    display.main()
