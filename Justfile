set windows-powershell := true

# Show this help
@help:
  just --list --list-submodules

# Set up dev environments
install:
  poetry install
  pre-commit install

# Run the pre-commit hooks
hooks:
  pre-commit run --all-files

# Run the tests
test *ARGS:
  poetry run pytest {{ARGS}}

# Clean up stuff
clean:
  just docs/clean
  poetry env remove --all
  rm -r .*_cache

mod docs
