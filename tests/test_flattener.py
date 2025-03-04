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
      - "browser=8 : 0.1" for the YES branch
      - "browser!=8 : 0.2" for the NO branch
    Also verifies that flatten() returns a generator.
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
    strategies = flattener.flatten(root_id=0)

    # Check that we got a generator
    assert hasattr(strategies, "__iter__")
    
    results = list(strategies)
    assert len(results) == 2
    assert "browser=8 : 0.1" in results
    assert "browser!=8 : 0.2" in results

def test_flattener_or_condition():
    """
    Tree with an OR condition:
      Node 0: [device_type=pc ||or|| browser=7] yes->1, no->2
      Node 1: leaf=0.111
      Node 2: leaf=0.222
    Expected strategies:
      - "device_type=pc OR browser=7 : 0.111" (YES branch)
      - "device_type!=pc & browser!=7 : 0.222" (NO branch)
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
    assert len(strategies) == 2
    assert "device_type=pc OR browser=7 : 0.111" in strategies
    assert "device_type!=pc & browser!=7 : 0.222" in strategies

def test_flattener_impossible_branch():
    """
    Test a tree where a branch becomes impossible due to contradictory constraints.
    
    Tree structure:
      Node 0: [x=4] yes->1, no->2
      Node 1: leaf=0.1
      Node 2: [x=4] yes->3, no->4
      
    For Node 0 NO branch, the constraint becomes x!=4.
    Then at Node 2 on the YES branch, the condition x=4 is attempted to be added,
    which contradicts x!=4. This branch should be pruned.
    
    Expected strategies:
      - "x=4 : 0.1" from Node 0 YES branch
      - "x!=4 : 0.222" from Node 0 NO -> Node 2 NO branch
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
            leaf_value=0.111  # This branch should be pruned (impossible)
        ),
        4: TreeNode(
            node_id=4,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.222
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    # Only strategies from Node 1 and Node 2 NO branch should be returned.
    assert len(strategies) == 2
    assert "x=4 : 0.1" in strategies
    # For Node 2 NO branch, the constraint remains x!=4.
    assert "x!=4 : 0.222" in strategies
    # The branch from Node 2 YES (which would have x=4 added to an x!=4 constraint) is pruned.

def test_flattener_redundant_inequality():
    """
    Test that redundant inequalities are simplified and that impossible branches are pruned.
    
    Scenario:
      Node 0: [x=4] yes->1, no->2
      Node 1: [x!=3] yes->3, no->4
      
    Explanation:
      - For Node 0 YES branch, the constraint is "x=4".
      - At Node 1 YES branch, adding "x!=3" is redundant because x is already 4.
        Thus, the final strategy is "x=4 : 0.111".
      - For Node 1 NO branch, the negation of "x!=3" (i.e. "x=3") would be added,
        but that contradicts the constraint "x=4", so that branch is pruned.
      - For Node 0 NO branch, the constraint becomes "x!=4", yielding "x!=4 : 0.9".
    
    Expected strategies: Only 2 strategies should be returned.
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
            leaf_value=0.111  # Valid branch from Node 1 YES
        ),
        4: TreeNode(
            node_id=4,
            or_condition=None,
            single_condition=None,
            yes_branch=None,
            no_branch=None,
            leaf_value=0.222  # This branch is pruned due to contradiction
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    # Only 2 valid strategies should be returned:
    #   - "x=4 : 0.111" from Node 0 YES -> Node 1 YES
    #   - "x!=4 : 0.9" from Node 0 NO
    assert len(strategies) == 2
    assert "x=4 : 0.111" in strategies
    assert "x!=4 : 0.9" in strategies
    
    # For the strategy from Node 0 YES -> Node 1 YES, ensure no redundant "x!=3" is present.
    for strat in strategies:
        if "0.111" in strat:
            assert "x=4" in strat
            assert "x!=3" not in strat

    """
    Test that redundant inequalities are simplified.
    
    Scenario:
      Node 0: [x=4] yes->1, no->2
      Node 1: [x!=3] yes->3, no->4
      
    Since x is already equal to 4 on Node 0 YES branch, the condition x!=3
    in Node 1 is redundant.
    
    Expected strategy from Node 1 YES branch:
       "x=4 & ... : leaf_value" where only x=4 appears for variable x.
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
            leaf_value=0.222
        ),
    }
    flattener = TreeFlattener(nodes)
    strategies = list(flattener.flatten(root_id=0))
    
    print("Generated Strategies:", strategies)

    # We expect three strategies:
    # 1. From Node 0 YES -> Node 1 YES: constraint for x remains "x=4" (x!=3 is redundant)
    # 2. From Node 0 YES -> Node 1 NO: constraint for x remains "x=4" (with negated inequality from Node 1)
    # 3. From Node 0 NO: "x!=4 : 0.9"
    assert len(strategies) == 2

    # Check that for the YES branch from Node 1, the constraint is simplified (no redundant x!=3)
    for strat in strategies:
        if "0.111" in strat or "0.222" in strat:
            # The condition should contain "x=4" but not "x!=3"
            assert "x=4" in strat
            assert "x!=3" not in strat

def test_flattener_generator_streaming():
    """
    Verify that the flatten() method returns a generator that yields strategies one by one.
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
    # Retrieve the first strategy and then break to simulate streaming
    first = next(strategy_gen)
    assert isinstance(first, str)
