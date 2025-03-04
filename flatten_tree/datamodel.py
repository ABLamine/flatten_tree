from dataclasses import dataclass
from typing import Optional

@dataclass
class Condition:
    variable: str
    operator: str  # "=" or "!="
    value: str

@dataclass
class OrCondition:
    left: Condition
    right: Condition

@dataclass
class TreeNode:
    node_id: int
    or_condition: Optional[OrCondition]       # None if it’s a leaf or a single condition node
    single_condition: Optional[Condition]       # None if it’s an OR condition node or a leaf
    yes_branch: Optional[int]
    no_branch: Optional[int]
    leaf_value: Optional[float]                 # Set only for leaf nodes
