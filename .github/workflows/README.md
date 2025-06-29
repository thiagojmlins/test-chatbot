# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated testing and CI/CD.

## Workflows

### `tests.yml`

Runs automated tests for both frontend and backend components.

#### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

#### Jobs

##### Frontend Tests
- **Runner**: Ubuntu Latest
- **Node.js**: Version 20
- **Cache**: npm dependencies
- **Commands**: `npm install` → `npm test`

##### Backend Tests
- **Runner**: Ubuntu Latest
- **Python**: Version 3.11
- **Cache**: pip dependencies
- **Environment Variables**:
  - `TESTING=1` - Enables testing mode
  - `SECRET_KEY=test-secret-key-for-ci` - Test secret key
  - `API_KEY=test-api-key-for-ci` - Test API key
  - `ALGORITHM=HS256` - JWT algorithm
  - `ACCESS_TOKEN_EXPIRE_MINUTES=30` - Token expiration

#### Steps
1. **Checkout**: Clone the repository
2. **Setup Python**: Install Python 3.11 with pip caching
3. **Install Dependencies**: Install requirements from `requirements.txt`
4. **Verify Configuration**: Test that configuration loads correctly
5. **Run Tests**: Execute pytest with verbose output

## Configuration

The backend tests use a testing configuration that:
- Uses SQLite instead of PostgreSQL for faster CI execution
- Skips configuration validation when `TESTING=1`
- Uses dummy API keys and secrets for testing

## Troubleshooting

If tests fail in CI:
1. Check that all required environment variables are set
2. Verify that `TESTING=1` is set for backend tests
3. Ensure all dependencies are properly listed in `requirements.txt`
4. Check that the database configuration works in testing mode 