import os
import random
import shutil
from pathlib import Path
from typing import Optional

class PoemManager:
    def __init__(self, poem_dir: str, poem_used_dir: str):
        self.poem_dir = Path(poem_dir)
        self.poem_used_dir = Path(poem_used_dir)
        
        self.poem_dir.mkdir(parents=True, exist_ok=True)
        self.poem_used_dir.mkdir(parents=True, exist_ok=True)
    
    def get_random_poem(self) -> Optional[str]:
        poem_files = [f for f in self.poem_dir.glob("*.txt") if f.is_file()]
        
        if not poem_files:
            return None
        
        selected_poem = random.choice(poem_files)
        return str(selected_poem)
    
    def mark_as_used(self, poem_path: str) -> None:
        source = Path(poem_path)
        if source.exists():
            destination = self.poem_used_dir / source.name
            shutil.move(str(source), str(destination))
    
    def count_available_poems(self) -> int:
        return len(list(self.poem_dir.glob("*.txt")))
    
    def count_used_poems(self) -> int:
        return len(list(self.poem_used_dir.glob("*.txt")))
