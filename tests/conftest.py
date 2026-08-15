import os
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.db.database import Base


@pytest.fixture
def tmp_buggy_repo():
    """
    Creates a temporary workspace with intentional bugs and a unit test file.
    """
    tmp_dir = tempfile.mkdtemp()
    
    # 1. Create a buggy module
    buggy_code = (
        "def compute_ratio(a, b):\n"
        "    # Intentional division by zero bug\n"
        "    return a / 0\n\n"
        "def greet(name):\n"
        "    return f'Hello {name}'\n"
    )
    with open(os.path.join(tmp_dir, "calculator.py"), "w", encoding="utf-8") as f:
        f.write(buggy_code)

    # 2. Create test suite
    tests_dir = os.path.join(tmp_dir, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    test_code = (
        "import unittest\n"
        "from calculator import compute_ratio\n\n"
        "class TestCalculator(unittest.TestCase):\n"
        "    def test_ratio(self):\n"
        "        self.assertEqual(compute_ratio(10, 2), 5)\n"
    )
    with open(os.path.join(tests_dir, "test_calculator.py"), "w", encoding="utf-8") as f:
        f.write(test_code)

    yield tmp_dir

    shutil.rmtree(tmp_dir)


@pytest.fixture
def db_session():
    """
    In-memory SQLite database session for isolated testing.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
