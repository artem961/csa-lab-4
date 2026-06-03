def pytest_addoption(parser):
    parser.addoption(
        "--update-gold",
        action="store_true",
        default=False,
        help="update golden test expectation files",
    )
