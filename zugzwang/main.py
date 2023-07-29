import os

from zugzwang.display import ZugDisplay
from zugzwang.menu_scene import InitialScene
from zugzwang.training_scene import PositionTrainingScene, LineTrainingScene
from zugzwang.editor_scene import FenCreatorScene
from zugzwang.group import UserData

if __name__ == '__main__':
    collections_dir_path = os.path.join(os.getcwd(),'../Collections')
    user_data = UserData(collections_dir_path)
    display = ZugDisplay()
    #fen = ZugFenCreator(display)
    #display.push_scene(fen)

    # to start from the beginning
    scene = InitialScene(display, user_data)

    # to start from a position training scene
    collection = user_data._get_children()[1]
    category = collection._get_children()[0]
    chapter = category._get_children()[0]
    scene = FenCreatorScene(display, category)
    
    display.push_scene(scene)
    display.main()
