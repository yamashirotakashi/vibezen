"""
Simple vector implementation for semantic cache without numpy.
"""

import math
from typing import List


class SimpleVector:
    """Simple vector implementation without numpy."""
    
    def __init__(self, values: List[float]):
        self.values = values
        self.dimension = len(values)
    
    def dot(self, other: 'SimpleVector') -> float:
        """Calculate dot product."""
        if self.dimension != other.dimension:
            raise ValueError("Vectors must have same dimension")
        
        return sum(a * b for a, b in zip(self.values, other.values))
    
    def norm(self) -> float:
        """Calculate vector norm."""
        return math.sqrt(sum(x * x for x in self.values))
    
    def normalize(self) -> 'SimpleVector':
        """Return normalized vector."""
        norm = self.norm()
        if norm == 0:
            return SimpleVector(self.values)
        
        return SimpleVector([x / norm for x in self.values])
    
    def cosine_similarity(self, other: 'SimpleVector') -> float:
        """Calculate cosine similarity."""
        dot_product = self.dot(other)
        norm_product = self.norm() * other.norm()
        
        if norm_product == 0:
            return 0.0
        
        return dot_product / norm_product
    
    def __getitem__(self, index: int) -> float:
        return self.values[index]
    
    def __setitem__(self, index: int, value: float):
        self.values[index] = value
    
    def __len__(self) -> int:
        return self.dimension
    
    @property
    def shape(self) -> tuple:
        return (self.dimension,)