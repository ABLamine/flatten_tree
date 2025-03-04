import pytest
from pathlib import Path
from flatten_tree.parser import TreeParser
from flatten_tree.datamodel import OrCondition, Condition

def test_parser_single_condition(tmp_path):
    content = """\
0:[browser=8] yes=1,no=2
1:leaf=0.1
2:leaf=0.2
"""
    file_path = tmp_path / "tree_to_convert.txt"
    file_path.write_text(content)
    parser = TreeParser(str(file_path))
    nodes = parser.parse()
    assert len(nodes) == 3
    node0 = nodes[0]
    assert node0.single_condition is not None
    assert node0.single_condition.variable == "browser"
    assert node0.single_condition.operator == "="
    assert node0.single_condition.value == "8"

def test_parser_or_condition(tmp_path):
    content = """\
0:[device_type=pc||or||browser=7] yes=1,no=2
1:leaf=0.111
2:leaf=0.222
"""
    file_path = tmp_path / "tree_to_convert.txt"
    file_path.write_text(content)
    parser = TreeParser(str(file_path))
    nodes = parser.parse()
    node0 = nodes[0]
    assert node0.or_condition is not None
    assert node0.or_condition.left == Condition("device_type", "=", "pc")
    assert node0.or_condition.right == Condition("browser", "=", "7")
