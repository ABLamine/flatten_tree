import re
from typing import Dict
from .datamodel import TreeNode, Condition, OrCondition

class TreeParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> Dict[int, TreeNode]:
        """
        Reads the input file and returns a dictionary mapping node IDs to TreeNode objects.
        """
        nodes: Dict[int, TreeNode] = {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                node_id_str, rest = line.split(":", 1)
                node_id = int(node_id_str)
                node = self._parse_line(node_id, rest)
                nodes[node_id] = node
        return nodes

    def _parse_line(self, node_id: int, raw_line: str) -> TreeNode:
        """
        Parses a single line (node) from the file.
        """
        if raw_line.startswith("leaf="):
            leaf_value = float(raw_line.split("=")[1])
            return TreeNode(
                node_id=node_id,
                or_condition=None,
                single_condition=None,
                yes_branch=None,
                no_branch=None,
                leaf_value=leaf_value
            )
        # Expecting a condition line like: [condition] yes=... ,no=...
        match = re.match(r"\[(.*?)\]\s*yes=(\d+),no=(\d+)", raw_line)
        if not match:
            raise ValueError(f"Node {node_id}: unexpected format '{raw_line}'")
        condition_part = match.group(1)
        yes_branch = int(match.group(2))
        no_branch = int(match.group(3))
        if "||or||" in condition_part:
            left_str, right_str = condition_part.split("||or||")
            left_cond = self._parse_single_condition(left_str.strip())
            right_cond = self._parse_single_condition(right_str.strip())
            or_cond = OrCondition(left=left_cond, right=right_cond)
            return TreeNode(
                node_id=node_id,
                or_condition=or_cond,
                single_condition=None,
                yes_branch=yes_branch,
                no_branch=no_branch,
                leaf_value=None
            )
        else:
            single_cond = self._parse_single_condition(condition_part.strip())
            return TreeNode(
                node_id=node_id,
                or_condition=None,
                single_condition=single_cond,
                yes_branch=yes_branch,
                no_branch=no_branch,
                leaf_value=None
            )

    def _parse_single_condition(self, cond_str: str) -> Condition:
        """
        Parses a string such as 'browser=8' or 'os_family!=5' into a Condition.
        """
        if "!=" in cond_str:
            variable, value = cond_str.split("!=")
            return Condition(variable=variable.strip(),
                             operator="!=",
                             value=value.strip())
        elif "=" in cond_str:
            variable, value = cond_str.split("=")
            return Condition(variable=variable.strip(),
                             operator="=",
                             value=value.strip())
        else:
            raise ValueError(f"Unexpected condition format: '{cond_str}'")