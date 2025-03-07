from typing import Dict, Generator, List, Optional
from .datamodel import TreeNode, Condition, OrCondition

def add_simple_constraint(constraints: Dict[str, tuple], var: str, op: str, val: str) -> Optional[Dict[str, tuple]]:
    """
    Returns a new copy of constraints with the new simple condition added.
    constraints: dict mapping variable -> (equality: Optional[str], inequalities: Set[str])
    op: "=" or "!=".
    If the new condition causes a contradiction, returns None.
    """
    # Create a deep copy of constraints for the current path.
    new_constraints = {k: (v[0], set(v[1])) for k, v in constraints.items()}
    if var in new_constraints:
        eq, ineq = new_constraints[var]
        if op == "=":
            # Adding an equality condition.
            if eq is None:
                new_constraints[var] = (val, ineq)
                if val in ineq:
                    # Contradiction: cannot equal a disallowed value.
                    return None
            else:
                if eq != val:
                    return None  # Conflict with existing equality.
                # If eq is already val, no change needed.
        elif op == "!=":
            if eq is not None:
                if eq == val:
                    return None  # Contradiction: value equals its disallowed value.
                # Otherwise, inequality is redundant.
            else:
                new_constraints[var][1].add(val)
    else:
        if op == "=":
            new_constraints[var] = (val, set())
        else:
            new_constraints[var] = (None, {val})
    return new_constraints

class TreeFlattener:
    def __init__(self, nodes: Dict[int, TreeNode]):
        self.nodes = nodes

    def flatten(self, root_id: int = 0) -> Generator[str, None, None]:
        """
        Flattens the tree into strategies. Yields one strategy at a time.
        Each strategy is a string of the form:
        
           condition1 & condition2 & ... : leaf_value
        
        An empty strategy will yield simply ": leaf_value".
        """
        yield from self._dfs_collect_strategies(root_id, constraints={}, extra_conditions=[])

    def _dfs_collect_strategies(
        self, node_id: int, 
        constraints: Dict[str, tuple],
        extra_conditions: List[str]
    ) -> Generator[str, None, None]:
        node = self.nodes[node_id]

        # If we reached a leaf, build and yield the strategy.
        if node.leaf_value is not None:
            cond_list = []
            for var, (eq, ineq) in constraints.items():
                if eq is not None:
                    cond_list.append(f"{var}={eq}")
                else:
                    for disallowed in sorted(ineq):
                        cond_list.append(f"{var}!={disallowed}")
            cond_list.extend(extra_conditions)
            cond_str = " & ".join(cond_list)
            yield f"{cond_str} : {node.leaf_value}" if cond_str else f": {node.leaf_value}"
            return

        # Process non-leaf nodes.
        if node.or_condition is not None:
            or_cond = node.or_condition

            # Branch YES: split into two DFS paths, one for each alternative.
            if node.yes_branch is not None:
                # Option 1: assume left condition is true.
                constraints_left = add_simple_constraint(constraints.copy(), or_cond.left.variable, or_cond.left.operator, or_cond.left.value)
                if constraints_left is not None:
                    yield from self._dfs_collect_strategies(node.yes_branch, constraints_left, extra_conditions.copy())
                # Option 2: assume right condition is true.
                constraints_right = add_simple_constraint(constraints.copy(), or_cond.right.variable, or_cond.right.operator, or_cond.right.value)
                if constraints_right is not None:
                    yield from self._dfs_collect_strategies(node.yes_branch, constraints_right, extra_conditions.copy())

            # Branch NO: the OR condition is false, meaning both parts are false.
            if node.no_branch is not None:
                new_constraints = constraints.copy()
                # For left: if originally "=" then now "!=" and vice versa.
                left_neg_op = "!=" if or_cond.left.operator == "=" else "="
                new_constraints = add_simple_constraint(new_constraints, or_cond.left.variable, left_neg_op, or_cond.left.value)
                if new_constraints is None:
                    return  # Branch impossible.
                right_neg_op = "!=" if or_cond.right.operator == "=" else "="
                new_constraints = add_simple_constraint(new_constraints, or_cond.right.variable, right_neg_op, or_cond.right.value)
                if new_constraints is None:
                    return  # Branch impossible.
                yield from self._dfs_collect_strategies(node.no_branch, new_constraints, extra_conditions.copy())

        elif node.single_condition is not None:
            cond = node.single_condition

            # YES branch: add the condition as is.
            new_constraints_yes = add_simple_constraint(constraints, cond.variable, cond.operator, cond.value)
            if new_constraints_yes is not None and node.yes_branch is not None:
                yield from self._dfs_collect_strategies(node.yes_branch, new_constraints_yes, extra_conditions.copy())

            # NO branch: add the negation of the condition.
            neg_op = "!=" if cond.operator == "=" else "="
            new_constraints_no = add_simple_constraint(constraints, cond.variable, neg_op, cond.value)
            if new_constraints_no is not None and node.no_branch is not None:
                yield from self._dfs_collect_strategies(node.no_branch, new_constraints_no, extra_conditions.copy())
