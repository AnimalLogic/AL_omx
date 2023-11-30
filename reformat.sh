#!/bin/sh

# Ensure the copyright header comment for each source code file and black format for source code.

set -e

python -m reformat

black AL