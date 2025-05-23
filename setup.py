import glob
import os
import pathlib
import re
import sys

from setuptools import setup  # type: ignore[import-untyped]

# Get the directory where setup.py is located
here = pathlib.Path(__file__).parent.resolve()


# Function to read requirements from a file
def read_requirements(filename):
    requirements = []
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Skip recursive includes to avoid duplication
                    if line.startswith("-r "):
                        continue
                    requirements.append(line)
    return requirements


# Read main requirements
main_requirements = read_requirements(os.path.join(here, "requirements.txt"))

# Get all requirement files from the requirements directory
req_dir = os.path.join(here, "requirements")
req_files = glob.glob(os.path.join(req_dir, "requirements-*.txt"))

# Check if requirements-all.txt exists (it shouldn't)
all_req_file = os.path.join(req_dir, "requirements-all.txt")
if os.path.exists(all_req_file):
    sys.stderr.write(
        "ERROR: requirements-all.txt should not exist as 'all' is a special key "
        "that is dynamically generated from all other requirement files.\n"
        "Please remove this file and use the dynamically generated "
        "'all' option instead.\n"
    )
    sys.exit(1)

# Dictionary to store all extra requirements
extras_require = {}

# Process each requirements file
for req_file in req_files:
    # Extract the group name from the filename
    # e.g., 'requirements-dev.txt' -> 'dev'
    basename = os.path.basename(req_file)
    match = re.match(r"requirements-(.+)\.txt", basename)
    if match:
        group_name = match.group(1)
        # Skip the 'all' group as we'll build it dynamically
        if group_name != "all":
            group_requirements = read_requirements(req_file)
            extras_require[group_name] = group_requirements

# Build the 'all' group dynamically by combining all other groups
all_requirements = list(main_requirements)  # Start with main requirements
for group, reqs in extras_require.items():
    all_requirements.extend(reqs)
# Remove duplicates while preserving order
all_requirements = list(dict.fromkeys(all_requirements))
extras_require["all"] = all_requirements

# Print available extras for information
print("Available installation options:")
print("  Core: pip install .")
sorted_extras = sorted(extras_require.keys())
sorted_extras.append("all")
for extra in sorted_extras:
    print(f"  {extra.capitalize()}: pip install .[{extra}]")

# Setup the package
setup(
    # Basic package information is read from setup.cfg and pyproject.toml
    # Here we just add the dynamic dependencies
    install_requires=main_requirements,
    extras_require=extras_require,
)
