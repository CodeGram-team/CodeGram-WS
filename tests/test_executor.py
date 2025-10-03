import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from executor import run_code_in_docker

SUCCESS_TEST_CASES = [
    ("python", "print('Hello from Python!')", "Hello from Python!"),
    ("nodejs", "console.log('Hello from Node.js!');", "Hello from Node.js!"),
    ("java", "public class Hello { public static void main(String[] args) { System.out.println(\"Hello from Java!\"); } }", "Hello from Java!"),
    ("c", '#include <stdio.h>\nint main() { printf("Hello from C!\\n"); return 0; }', "Hello from C!"),
    ("cpp", '#include <iostream>\nint main() { std::cout << "Hello from C++!" << std::endl; return 0; }', "Hello from C++!"),
]

@pytest.mark.parametrize("language, code, expected_output", SUCCESS_TEST_CASES)
@pytest.mark.asyncio
async def test_run_code_in_docker_success(language, code, expected_output):

    result = await run_code_in_docker(language=language, code=code)

    
    if result['status'] != 'success':
        print(f"\nDEBUG INFO for language '{language}':")
        print(result)

    error_message = f"'{language}' failed with stderr: {result['stderr']}"
    assert result['status'] == 'success', error_message
    
    assert result['stderr'] == '', f"'{language}' produced an unexpected error: {result['stderr']}"
    assert expected_output in result['stdout'], f"'{language}' did not produce the expected output."
    assert result['execution_time'] > 0

@pytest.mark.asyncio
async def test_run_code_in_docker_error():
    
    error_code = "print(undefined_variable)"
    
    result = await run_code_in_docker(language="python", code=error_code)

    assert result['status'] == 'error'
    assert result['stdout'] == ''
    assert "NameError" in result['stderr']

@pytest.mark.asyncio
async def test_run_code_in_docker_unsupported_language():

    result = await run_code_in_docker(language="rust", code="fn main() { println!(\"Hello, Rust!\"); }")

    assert result['status'] == 'error'
    assert "Unsupported language: rust" in result['stderr']