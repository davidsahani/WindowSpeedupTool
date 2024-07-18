import os
import sys

# append parent dir to python import path
parent_dir: str = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)
)
source_dir = os.path.join(parent_dir, "source")

sys.path.append(parent_dir)
sys.path.append(source_dir)

os.chdir(source_dir)
