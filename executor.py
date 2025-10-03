import docker
import time
import os
import tempfile
from docker.errors import ContainerError, DockerException, APIError, NotFound
from config import LANGUAGE_CONFIG, EXECUTION_TIME_LIMIT
import asyncio
from typing import Dict, Any
import logging
from utils.extract import extract_java_main_class

async def run_code_in_docker(language:str, code:str)->Dict[str,Any]:
    """
    Code execution sandbox 
    execute code and return result to message queue.
    params:
    - langauge: programming language from message queue
    - code: user's code for execution
    result:
    - dict: status, stdout, stderr, execution_time
    """
    start_time = time.time()
    
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        execution_time = time.time() - start_time
        return {
            "status" : "error",
            "stdout" : "",
            "stderr" : f"Unsupported language: {language}",
            "execution_time" : execution_time
    }
    
    # make temporary directory and save code in 'main' file
    temp_dir = tempfile.TemporaryDirectory() 
    container = None
    
    try:
        # Execute docker container
        client = docker.from_env()
        
        filename = config["filename"]
        exec_command = config["command"](filename)
        
        # Extract class name if name is not 'Main'
        if language == 'java':
            main_class_name = extract_java_main_class(code=code)
            if not main_class_name:
                raise ValueError("Could not find a public class with a main method")
            filename = f"{main_class_name}.java"
            command = f"javac {filename} && java {main_class_name}"
            exec_command = ["sh", "-c", command]
        
        file_path = os.path.join(temp_dir.name, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
                
        container = await asyncio.to_thread(
                client.containers.run,
                image=config["image"],
                command=exec_command,
                volumes={temp_dir.name : {'bind' : '/app'}},
                working_dir="/app",
                detach=True, # run on background
                mem_limit="128m", # memory limit(128mb)
                nano_cpus=int(0.5*10**9), # CPU Core limit(0.5 cpu core) 
                network_disabled=True
        )
        try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait),
                    timeout=EXECUTION_TIME_LIMIT
                )
                stdout = (await asyncio.to_thread(container.logs, stdout=True, stderr=False)).decode('utf-8')
                stderr = (await asyncio.to_thread(container.logs, stdout=False, stderr=True)).decode('utf-8')
                    
                status = "success" if result['StatusCode'] == 0 else "error"
                
        except asyncio.TimeoutError:
                logging.warning("Execution timed out. Stopping container")
                await asyncio.to_thread(container.stop)
                status = "timeout"
                stdout = ""
                stderr = f"Execution exceeded the time limit of {EXECUTION_TIME_LIMIT} seconds"
    except (DockerException, APIError, ContainerError) as e:
        status = "error"
        stdout = ""
        stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
    except Exception as e:
        status = "error"
        stdout = ""
        stderr = f"An unexpected error occured: {e}"
    finally:
        if container:
            try:
                await asyncio.to_thread(container.remove, force=True)
            except NotFound:
                pass
        temp_dir.cleanup()
        print("Temporary directory and container clean up(remove)")
    execution_time = time.time() - start_time
    
    return {
        "status" : status,
        "stdout" : stdout,
        "stderr" : stderr,
        "execution_time" : round(execution_time,4)
    }