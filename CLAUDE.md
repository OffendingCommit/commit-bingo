# BINGO Project Guide

## Build Commands
```bash
# Quick setup for development
./setup.sh

# Install dependencies
poetry install

# Run application (old monolithic structure)
poetry run python main.py

# Run application (new modular structure)
poetry run python app.py

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# Lint code
poetry run flake8
poetry run black --check .
poetry run isort --check .

# Format code
poetry run black .
poetry run isort .

# Build Docker container
docker build -t bingo .

# Run Docker container
docker run -p 8080:8080 bingo

# Helm deployment
cd helm && ./package.sh && helm install bingo ./bingo

# Using Makefile
make install  # Install dependencies
make run      # Run application
make test     # Run tests
make lint     # Run linters
make format   # Format code
make build    # Build package
```

## Code Style Guidelines
- **Imports**: Standard library first, third-party second, local modules last
- **Formatting**: Use f-strings for string formatting
- **Constants**: Defined at top of file in UPPER_CASE
- **Naming**: snake_case for functions/variables, UPPER_CASE for constants
- **Error Handling**: Use try/except blocks with proper logging
- **UI Elements**: Define class constants for styling
- **Logging**: Use Python's logging module with descriptive messages
- **Comments**: Use docstrings for functions and descriptive comments
- **Line Length**: Max 88 characters (Black's default)
- **Code Formatting**: Use Black for code formatting and isort for import sorting

## Project Structure
- `app.py`: Main entry point for modular application
- `src/`: Source code directory
  - `config/`: Configuration and constants
  - `core/`: Core game logic
  - `ui/`: User interface components
  - `utils/`: Utility functions
- `phrases.txt`: Contains customizable bingo phrases
- `static/`: Static assets for fonts and styles
- `tests/`: Unit and integration tests
- `helm/`: Kubernetes deployment configuration
- `.github/workflows/`: CI pipeline configuration
- `CHANGELOG.md`: Release history tracking

## Git Workflow

### Branch Naming
- Use feature branches for each change: `feature/description-of-change`
- Use bugfix branches for bug fixes: `fix/description-of-bug`
- Use chore branches for maintenance: `chore/description-of-task`

### Commit Guidelines
Follow conventional changelog format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

1. **Types**:
   - `feat`: A new feature
   - `fix`: A bug fix
   - `docs`: Documentation only changes
   - `style`: Changes that do not affect meaning (white-space, formatting)
   - `refactor`: Code change that neither fixes a bug nor adds a feature
   - `perf`: Change that improves performance
   - `test`: Adding missing tests or correcting existing tests
   - `chore`: Changes to the build process or auxiliary tools

2. **Scope** (optional): The module/component affected, e.g., `core`, `ui`, `board`

3. **Subject**: Short description in imperative, present tense (not past tense)
   - Good: "add feature X" (not "added feature X")
   - Use lowercase
   - No period at the end

4. **Body** (optional): Detailed explanation of changes
   - Use present tense
   - Include motivation and context
   - Explain "what" and "why" (not "how")

5. **Footer** (optional): Reference issues, PRs, breaking changes

### Example Commits:
```
feat(board): add color theme selector 

Add ability for users to choose color themes for the bingo board

Resolves #123
```

```
fix(ui): resolve client disconnection issues

Handle race conditions during client disconnects to prevent 
server exceptions and ensure smooth reconnection

Fixes #456
```

## Semantic Versioning

This project follows semantic versioning (SEMVER) principles:

- **MAJOR** version when making incompatible API changes (X.0.0)
- **MINOR** version when adding functionality in a backwards compatible manner (0.X.0)
- **PATCH** version when making backwards compatible bug fixes (0.0.X)

Version numbers are automatically updated by the CI/CD pipeline based on commit messages.
The project uses python-semantic-release to analyze commit messages and determine the appropriate 
version bump according to the conventional commit format.

## CI/CD Pipeline

The project utilizes GitHub Actions for continuous integration and deployment:

1. **CI Job**:
   - Runs on each push to main and pull request
   - Installs dependencies
   - Runs linters (flake8, black, isort)
   - Runs all tests with pytest
   - Uploads coverage reports

2. **Release Job**:
   - Runs after successful CI job on the main branch
   - Determines new version based on commit messages
   - Updates CHANGELOG.md
   - Creates Git tag for the release
   - Publishes release on GitHub

## Pre-Push Checklist

Before pushing changes to the repository, run these checks locally to ensure the CI pipeline will pass:

```bash
# 1. Run linters to ensure code quality and style
poetry run flake8 main.py src/ tests/
poetry run black --check .
poetry run isort --check .

# 2. Run tests to ensure functionality works
poetry run pytest

# 3. Check test coverage to ensure sufficient testing
poetry run pytest --cov=main --cov-report=term-missing

# 4. Fix any linting issues
poetry run black .
poetry run isort .

# 5. Run tests again after fixing linting issues
poetry run pytest

# 6. Verify application starts without errors
poetry run python main.py  # (Ctrl+C to exit after confirming it starts)
```

### Common CI Failure Points to Check:

1. **Code Style Issues**:
   - Inconsistent indentation
   - Line length exceeding 88 characters
   - Missing docstrings
   - Improper import ordering

2. **Test Failures**:
   - Broken functionality due to recent changes
   - Missing tests for new features
   - Incorrectly mocked dependencies in tests
   - Race conditions in async tests

3. **Coverage Thresholds**:
   - Insufficient test coverage on new code
   - Missing edge case tests
   - Uncovered exception handling paths

### Quick Fix Command Sequence

If you encounter CI failures, this sequence often resolves common issues:

```bash
# Fix style issues
poetry run black .
poetry run isort .

# Run tests with coverage to identify untested code
poetry run pytest --cov=main --cov-report=term-missing

# Add tests for any uncovered code sections then run again
poetry run pytest
```

## Testing Game State Synchronization

Special attention should be paid to testing game state synchronization between the main view and the stream view:

```bash
# Run specific tests for state synchronization
poetry run pytest -v tests/test_ui_functions.py::TestUIFunctions::test_header_updates_on_both_paths
poetry run pytest -v tests/test_ui_functions.py::TestUIFunctions::test_stream_header_update_when_game_closed
```

When making changes to game state management, especially related to:
- Game closing/reopening
- Header text updates
- Board visibility
- Broadcast mechanisms

Verify both these scenarios:
1. Changes made on main view are reflected in stream view
2. Changes persist across page refreshes
3. New connections to stream page see the correct state

Common issues:
- Missing ui.broadcast() calls
- Not handling header updates across different views
- Not checking if game is closed in sync_board_state
- Ignoring exception handling for disconnected clients