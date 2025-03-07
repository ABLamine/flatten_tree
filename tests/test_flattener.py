import pytest
from flatten_tree.datamodel import TreeNode, OrCondition, Condition
from flatten_tree.flattener import TreeFlattener

def test_flattener_single_condition_streaming():
    """
    A simple tree:
      Node 0: [browser=8] yes->1, no->2
      Node 1: leaf=0.1
      Node 2: leaf=0.2
    Expected strategies:
      - "browser=8 : 0.1" for YES branch
      - "browser!=8 : 0.2" for NO branch
    """
    nodes = {
        0: TreeNode(
            node_id=0,
            or_condition=None,
            single_condition=Condition("browser", "=", "8"),
            yes_branch=1,
            no_branch=2,
            leaf_value=None
        ),
        1: TreeNode(
            node_id=1,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.1
        ),
        2: TreeNode(
            node_id=2,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.2
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    assert len(strategies) == 2
    assert "browser=8 : 0.1" in strategies
    assert "browser!=8 : 0.2" in strategies

def test_flattener_or_condition():
    """
    Tree with an OR condition:
      Node 0: [device_type=pc||or||browser=7] yes->1, no->2
      Node 1: leaf=0.111
      Node 2: leaf=0.222
      
    Revised expectations (no OR in final output):
      - YES branch produces two strategies:
           "device_type=pc : 0.111" and "browser=7 : 0.111"
      - NO branch produces one strategy:
           "device_type!=pc & browser!=7 : 0.222"
    Total: 3 strategies.
    """
    or_cond = OrCondition(
        left=Condition("device_type", "=", "pc"),
        right=Condition("browser", "=", "7")
    )
    nodes = {
        0: TreeNode(
            node_id=0,
            or_condition=or_cond,
            single_condition=None,
            yes_branch=1,
            no_branch=2,
            leaf_value=None
        ),
        1: TreeNode(
            node_id=1,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.111
        ),
        2: TreeNode(
            node_id=2,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.222
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    # Expect 3 strategies in total:
    #  - "device_type=pc : 0.111"
    #  - "browser=7 : 0.111"
    #  - "device_type!=pc & browser!=7 : 0.222"
    assert len(strategies) == 3
    assert "device_type=pc : 0.111" in strategies
    assert "browser=7 : 0.111" in strategies
    assert "device_type!=pc & browser!=7 : 0.222" in strategies

    # Ensure that no strategy contains an "OR" string.
    for strat in strategies:
        assert "OR" not in strat

def test_flattener_impossible_branch():
    """
    Test a tree where a branch becomes impossible due to contradictory constraints.
    
    Scenario:
      Node 0: [x=4] yes->1, no->2
      Node 1: leaf=0.1
      Node 2: [x=4] yes->3, no->4
      
    For Node 0 NO branch, the constraint becomes x!=4.
    Then at Node 2 YES branch, attempting to add x=4 causes a contradiction, so that branch is pruned.
    
    Expected strategies:
      - "x=4 : 0.1" from Node 0 YES branch
      - "x!=4 : 0.9" from Node 0 NO branch
    """
    nodes = {
        0: TreeNode(
            node_id=0,
            or_condition=None,
            single_condition=Condition("x", "=", "4"),
            yes_branch=1,
            no_branch=2,
            leaf_value=None
        ),
        1: TreeNode(
            node_id=1,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.1
        ),
        2: TreeNode(
            node_id=2,
            or_condition=None,
            single_condition=Condition("x", "=", "4"),
            yes_branch=3,
            no_branch=4,
            leaf_value=None
        ),
        3: TreeNode(
            node_id=3,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.111  # This branch is pruned due to contradiction
        ),
        4: TreeNode(
            node_id=4,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.9
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    # Expect only 2 valid strategies:
    #  - "x=4 : 0.1" from Node 0 YES branch
    #  - "x!=4 : 0.9" from Node 0 NO branch (Node 2 YES branch is pruned)
    assert len(strategies) == 2
    assert "x=4 : 0.1" in strategies
    assert "x!=4 : 0.9" in strategies

def test_flattener_redundant_inequality():
    """
    Test that redundant inequalities are simplified and impossible branches pruned.
    
    Scenario:
      Node 0: [x=4] yes->1, no->2
      Node 1: [x!=3] yes->3, no->4
      
    Explanation:
      - For Node 0 YES branch, constraint "x=4" is applied.
      - At Node 1 YES branch, adding "x!=3" is redundant since x is already 4,
         yielding "x=4 : 0.111".
      - For Node 1 NO branch, the negation would yield "x=3", conflicting with "x=4", so it's pruned.
      - For Node 0 NO branch, constraint becomes "x!=4", yielding "x!=4 : 0.9".
    Expected strategies: 2 strategies.
    """
    nodes = {
        0: TreeNode(
            node_id=0,
            or_condition=None,
            single_condition=Condition("x", "=", "4"),
            yes_branch=1,
            no_branch=2,
            leaf_value=None
        ),
        1: TreeNode(
            node_id=1,
            or_condition=None,
            single_condition=Condition("x", "!=", "3"),
            yes_branch=3,
            no_branch=4,
            leaf_value=None
        ),
        2: TreeNode(
            node_id=2,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.9
        ),
        3: TreeNode(
            node_id=3,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.111
        ),
        4: TreeNode(
            node_id=4,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.222  # This branch is pruned
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    # Expect 2 valid strategies:
    #  - "x=4 : 0.111" (redundant "x!=3" omitted)
    #  - "x!=4 : 0.9"
    assert len(strategies) == 2
    assert "x=4 : 0.111" in strategies
    assert "x!=4 : 0.9" in strategies
    for strat in strategies:
        assert "OR" not in strat

def test_flattener_generator_streaming():
    """
    Verify that flatten() returns a generator that yields strategies one by one.
    """
    nodes = {
        0: TreeNode(
            node_id=0,
            or_condition=None,
            single_condition=Condition("a", "=", "1"),
            yes_branch=1,
            no_branch=2,
            leaf_value=None
        ),
        1: TreeNode(
            node_id=1,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.111
        ),
        2: TreeNode(
            node_id=2,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.222
        ),
    }
    flattener = TreeFlattener(nodes)
    strategy_gen = flattener.flatten(root_id=0)
    
    # Check that strategy_gen is a generator
    assert hasattr(strategy_gen, "__iter__")
    first = next(strategy_gen)
    assert isinstance(first, str)
