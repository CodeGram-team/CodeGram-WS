"""
Output:
> python example.py
Starting Docker code execution tests...

--- Testing language: PYTHON ---
Temporary directory and container clean up(remove)
Execution Result:
{
  "status": "success",
  "stdout": "Hello from Python!\nPython Version: 3.12.11\n",
  "stderr": "",
  "execution_time": 2.2698
}
-------------------------------------

--- Testing language: NODEJS ---
Temporary directory and container clean up(remove)
Execution Result:
{
  "status": "success",
  "stdout": "Hello from Node.js!\nNode.js Version: v18.20.8\n",
  "stderr": "",
  "execution_time": 1.8762
}
-------------------------------------

--- Testing language: JAVA ---
Temporary directory and container clean up(remove)
Execution Result:
{
  "status": "success",
  "stdout": "Hello from Java!\nJava Version: 17-ea\n",
  "stderr": "",
  "execution_time": 4.6854
}
-------------------------------------

--- Testing language: C ---
Temporary directory and container clean up(remove)
Execution Result:
{
  "status": "success",
  "stdout": "Hello from C!\nCompiler: GCC 15.2.0\n",
  "stderr": "",
  "execution_time": 1.9449
}
-------------------------------------

--- Testing language: CPP ---
Temporary directory and container clean up(remove)
Execution Result:
{
  "status": "success",
  "stdout": "Hello from C++!\nCompiler: G++ 15.2.0\n",
  "stderr": "",
  "execution_time": 3.0376
}
-------------------------------------

All tests completed
"""

import asyncio
import json
from typing import Dict
from executor import run_code_in_docker


# Example Code for execution
TEST_CODES: Dict[str, str] = {
    "python": """
import sys
print("Hello from Python!")
print(f"Python Version: {sys.version.split()[0]}")
""",
    
    "nodejs": """
console.log("Hello from Node.js!");
console.log(`Node.js Version: ${process.version}`);
""",
    
    "java": """
public class Circle {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
        System.out.println("Java Version: " + System.getProperty("java.version"));
    }
}
""",

    "c": """
#include <stdio.h>

int main() {
    printf("Hello from C!\\n");
    printf("Compiler: GCC %s\\n", __VERSION__);
    return 0;
}
""",

    "cpp": """
#include <iostream>

int main() {
    std::cout << "Hello from C++!" << std::endl;
    std::cout << "Compiler: G++ " << __VERSION__ << std::endl;
    return 0;
}
"""
}

async def main():
    """
    Test code execution for all defined languages and print result
    """
    print("Starting Docker code execution tests...\n")
    
    for language, code in TEST_CODES.items():
        print(f"--- Testing language: {language.upper()} ---")
        
        result = await run_code_in_docker(language=language, code=code)
        
        print("Execution Result:")
        print(json.dumps(result, indent=2))
        print("-------------------------------------\n")
        
    print("All tests completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred during the test run: {e}")
        print("required Docker images (python, node, openjdk, gcc) available locally")
