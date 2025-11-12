# Test Commands

## Run all tests
```bash
python -m pytest tests/ -v
```

## Run tests with coverage
```bash
python -m coverage run -m pytest tests/
python -m coverage report --include="src/*"
```

## Run tests with HTML coverage report
```bash
python -m coverage run -m pytest tests/
python -m coverage html --include="src/*"
```

## Run specific test file
```bash
python -m pytest tests/test_api.py -v
python -m pytest tests/test_edge_cases.py -v
```

## Run specific test class
```bash
python -m pytest tests/test_api.py::TestSignupEndpoint -v
```

## Run specific test method
```bash
python -m pytest tests/test_api.py::TestSignupEndpoint::test_signup_success -v
```