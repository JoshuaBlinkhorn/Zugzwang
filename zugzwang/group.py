from __future__ import annotations

import os
import itertools
from typing import List, Callable
import chess

from zugzwang.stats import ZugStats
from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.tools import ZugChessTools
from zugzwang.training import Line

class Group:
    def __init__(self, path: str, parent: Group, child_type: Callable):
        self._path = path
        self._name = os.path.basename(path)
        self._parent = parent
        # TODO: we should work towards child type not being a thing
        # just allow the user to create an arbitrary structure of folders
        # and chapters
        #
        # This will require a GUI feature as well need to distinguish
        # between them
        #
        # But I think it's the way to go
        self._child_type = child_type        

        self._children = self._get_children()
        self._stats = self._get_stats()

    @property
    def name(self):
        return self._name
        
    @property
    def stats(self):
        return self._stats

    @property
    def children(self):
        return self._children

    @property
    def chapters(self):
        return self._get_chapters()
    
    def _get_children(self):
        # TODO: I wonder whether we can just replace the child type below
        # with Group when it's a folder, and Chapter when it's a file?
        # We should try that out when we're stable
        #
        # It might allow us to do away with Collection and Category, and just have
        # UserData, Directory, and Chapter.
        # Then we can put everything in one module user_data.py        
        children = []
        for child_name in self._filter_children(sorted(os.listdir(self._path))):
            child_path = os.path.join(self._path, child_name)
            children.append(self._child_type(child_path, self))
                
        return children

    def _get_chapters(self):
        if self._child_type == Chapter:
            return [child for child in self._children]  # just a copy
        else:
            return [chapter for child in self._children for chapter in child.chapters]

    def _filter_children(self, children: List[str]) -> List[str]:
        """
        The base implementation here ignores filenames that start with a dot.

        Override in derived class for different or additional specific filtering
        of children.
        """
        return [child for child in children if not child.startswith('.')]

    def _get_stats(self):
        stats = ZugStats()
        for child in self.children:
            stats = stats + child.stats
        return stats

    def update_stats(self):
        self._stats = self._get_stats()
        if self._parent is not None:
            self._parent.update_stats()


class UserData(Group):
    def __init__(self, path: str):
        super().__init__(path=path, parent=None, child_type=Collection)


class Collection(Group):
    def __init__(self, path: str, parent: UserData):
        super().__init__(path=path, parent=parent, child_type=Category)


class Category(Group):
    def __init__(self, path: str, parent: Collection):
        super().__init__(path=path, parent=parent, child_type=Chapter)

    def _filter_children(self, children: List[str]) -> List[str]:
        children = super()._filter_children(children)
        return [
            child for child in children
            # TODO:
            # temporary filtering for recognising STUB files in the dir
            # I use stub files to allow use of PGNs generation in other UIs
            #
            # Probably we should go back to our own file type that extends the PGN
            # And reinstate the .chp extension
            # But perhaps not, keeping the .pgn means our files can be recognised
            # by other editors
            if child.endswith('.pgn') and 'STUB' not in child
        ]


class Chapter():

    def __init__(self, path: str, parent: Category):
        # The constructor here may take some time to execute - it's basically
        # down to the generation of the statistics, which necessitates the
        # creation of Solutions.
        # I can't think of a scenario where the Chapter is created, but the owner
        # doesn't want the statistics.

        # parse filepath
        self._path = path                
        self._name = os.path.basename(path)[:-4]
        self._parent = parent
        
        # collect roots
        self._roots = []    
        with open(path) as pgn_file:
            game = chess.pgn.read_game(pgn_file)
            while game is not None:
                self._roots.append(ZugRoot(game))
                game = chess.pgn.read_game(pgn_file)                
                
        # form the solution set
        self._solutions = []
        for root in self._roots:
            nodes = ZugChessTools.get_solution_nodes(
                root.game_node,
                root.data.perspective
            )
            # Solutions are linked to the 'primary root', which keeps the chapter's
            # metadata
            self._solutions.extend([ZugSolution(node, self._roots[0]) for node in nodes])

        # update the metadata on the primary root
        self._roots[0].update()
            
        # update the root and the stats
        self._stats = self._generate_stats()

    @property
    def name(self):
        return self._name

    @property
    def root(self):
        return self._roots[0]

    @property
    def stats(self):
        return self._stats

    @property
    def solutions(self):
        return self._solutions

    def build_lines(self):
        """Build all of lines playable in the current chapter."""
        return [
            Line(line, self._roots[0])
            for root in self._roots
            for line in ZugChessTools.get_lines(root.game_node, root.data.perspective)
        ]

    def write_to_disk(self):
        with open(self._path, 'w') as pgn_file:
            for root in self._roots:
                print(root.game_node, file=pgn_file, end='\n\n')

    def update_stats(self):
        self._roots[0].update()        
        self._stats = self._generate_stats()
        self._parent.update_stats()

    def _generate_stats(self):
        stats = ZugStats()
        for solution in self._solutions:
            if not solution.is_learned():
                stats.new += 1
            if solution.is_due():
                stats.due += 1
            if solution.is_learned():
                stats.learned += 1
            stats.total += 1
        stats.new = min(stats.new, self._roots[0].data.learning_remaining)
        return stats


class ZugGroup:

    def __init__(self, path, child_type):
        self._path = path
        self._child_type = child_type
        self._children = self._get_children()
        self.stats = self._get_stats()
        self.name = os.path.basename(path)
        self.menu_type = None

    def _get_children(self):
        children = []
        for child_name in self._filter_children(sorted(os.listdir(self._path))):
            child_path = os.path.join(self._path, child_name)
            children.append(self._child_type(child_path))
        return children

    def get_chapters(self):
        if self._child_type == ZugChapter:
            return self.children
        else:
            chapter_lists = [child.get_chapters() for child in self.children]
            return list(itertools.chain(*chapter_lists))

    def _filter_children(self, children: List[str]) -> List[str]:
        """
        The base implementation here ignores filenames that start with a dot.

        Override in derived class for different or additional specific filtering
        of children.
        """
        return [child for child in children if not child.startswith('.')]

    def _get_stats(self):
        stats = ZugStats()
        for child in self.children:
            stats = stats + child.stats
        return stats

    def update_stats(self):
        self.stats = self._get_stats()


class ZugUserData(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugCollection)


class ZugCollection(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugCategory)


class ZugCategory(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugChapter)

    def _filter_children(self, children: List[str]) -> List[str]:
        children = super()._filter_children(children)
        return [
            child for child in children
            if child.endswith('.pgn') and 'STUB' not in child
        ]


