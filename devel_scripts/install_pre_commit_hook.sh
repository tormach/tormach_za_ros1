#!/bin/bash -e
# Set up environment
WANT_ENV=docker-run
source "$(dirname $0)/../install_scripts/env.sh"
cd "${REPO_DIR}"

# install pre-commit hook
if test -d .git/hooks; then
    pre-commit install -f
    pre-commit install-hooks
    mv .git/hooks/pre-commit .git/hooks/pre-commit-run
    cp -v devel_scripts/include/pre-commit .git/hooks/pre-commit
fi
