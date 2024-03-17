class ColourScheme:
    def __init__(
        self,
        white,
        black,
        white_highlight,
        black_highlight,
        white_move_highlight,
        black_move_highlight,
    ):
        self.white = white
        self.black = black
        self.white_highlight = white_highlight
        self.black_highlight = black_highlight
        self.white_move_highlight = white_move_highlight
        self.black_move_highlight = black_move_highlight


DEFAULT_THEME = ColourScheme(
    white=(237, 220, 180),
    black=(180, 134, 100),
    white_highlight=(113, 143, 101),
    black_highlight=(99, 117, 81),
    white_move_highlight=(190, 198, 100),
    black_move_highlight=(158, 156, 40),
)
