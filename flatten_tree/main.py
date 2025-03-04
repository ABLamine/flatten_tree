import argparse
from flatten_tree.parser import TreeParser
from flatten_tree.flattener import TreeFlattener

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-path",
        default="tree_to_convert.txt",
        help="Path to the input tree file"
    )
    parser.add_argument(
        "--output-path",
        default="strategies.txt",
        help="Path to the output strategies file"
    )
    parser.add_argument(
        "--root-id",
        type=int,
        default=0,
        help="Root node ID (defaults to 0)"
    )
    args = parser.parse_args()

    # Parse the input tree file.
    tree_parser = TreeParser(args.input_path)
    nodes = tree_parser.parse()

    # Flatten the tree into strategies.
    flattener = TreeFlattener(nodes)
    with open(args.output_path, "w", encoding="utf-8") as out_f:
        for strategy in flattener.flatten(args.root_id):
            out_f.write(strategy + "\n")

if __name__ == "__main__":
    main()
