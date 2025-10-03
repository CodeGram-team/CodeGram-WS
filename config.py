LANGUAGE_CONFIG = {
    "python": {
        "image" : "python:3.12-slim",
        "command" : lambda filename : ["python", filename],
        "filename" : "main.py"
    },
    "nodejs" : {
        "image" : "node:18-alpine",
        "command" : lambda filename : ["node" , filename],
        "filename" : "main.js"
    },
    "java" : {
        "image" : "openjdk:17-alpine",
        "command" : lambda filename : [
            "sh", "-c",
            f"javac {filename} && java {filename.replace('.java', '')}"
        ],
        "filename" : "Main.java"
    },
    "c" : {
        "image" : "gcc:latest",
        "command" : lambda filename : [
            "sh", "-c",
            f"gcc {filename} -o main.out && ./main.out"
        ],
        "filename" : "main.c"
    },
    "cpp" : {
        "image" : "gcc:latest",
        "command" : lambda filename : [
            "sh", "-c",
            f"g++ {filename} -o main.out && ./main.out"
        ],
        "filename" : "main.cpp"
    },
    
}
EXECUTION_TIME_LIMIT=5 # Maximum execution time limit