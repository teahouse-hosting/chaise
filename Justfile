# Show this help
@help:
  just --list

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
