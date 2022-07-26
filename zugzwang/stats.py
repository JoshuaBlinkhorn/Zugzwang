import dataclasses

@dataclasses.dataclass
class ZugStats:
    new: int = 0
    due: int = 0
    learned: int = 0
    total: int = 0            

    def __add__(self, other):
        return ZugStats(
            new = self.new + other.new,
            due = self.due + other.due,
            learned = self.learned + other.learned,
            total = self.total + other.total
        )
    
