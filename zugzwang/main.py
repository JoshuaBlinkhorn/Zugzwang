import os

from zugzwang.display import ZugDisplay
from zugzwang.menu_scene import ZugInitialScene
from zugzwang.training_scene import ZugTrainingScene
from zugzwang.group import ZugUserData

if __name__ == '__main__':
    collections_dir_path = os.path.join(os.getcwd(),'../Collections')
    user_data = ZugUserData(collections_dir_path)
    display = ZugDisplay()
    #fen = ZugFenCreator(display)
    #display.push_scene(fen)

    # to start from the beginning
    scene = ZugInitialScene(display, user_data)

    # to start from a position training scene
    collection = user_data._get_children()[1]
    category = collection._get_children()[1]
    chapter = category._get_children()[1]
    # scene = ZugTrainingScene(display, chapter)
    
    display.push_scene(scene)
    display.main()
