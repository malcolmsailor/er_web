# TODO make or githook to rebuild this

import ast
import os

out_path = os.path.join(
    os.path.dirname((os.path.realpath(__file__))), "../er_web/constants.py"
)

outf = open(out_path, "w")

in_path = os.path.join(
    os.environ["EFFRHY_DIR"], "efficient_rhythms/er_constants.py"
)

with open(
    in_path,
    "r",
) as inf:
    contents = inf.read()

outf.write("ER_CONSTANTS = {")

tree = ast.parse(contents)
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            outf.write(f"'{target.id}',")
outf.write("}")
outf.close()
