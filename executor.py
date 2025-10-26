import docker
import time
import os
import tempfile
from docker.errors import APIError, NotFound
from config import LANGUAGE_CONFIG, EXECUTION_TIME_LIMIT
import asyncio
from typing import Callable, Coroutine
import logging
from utils.extract import extract_java_main_class

async def run_code_in_docker(
    language: str,
    code: str,
    job_id: str,
    input_queue: asyncio.Queue,
    output_callback: Callable[[str, str], Coroutine]
):
    """
    Docker 컨테이너와 실시간 양방향(stdin/stdout) 통신을 수행
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        await output_callback("stderr", f"Unsupported language: {language}")
        return

    temp_dir = tempfile.TemporaryDirectory()
    container: docker.models.containers.Container = None
    try:
        client = docker.from_env()
        
        filename = config["filename"]
        exec_command = config["command"](filename)
        
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
            volumes={temp_dir.name: {'bind': '/app'}},
            working_dir="/app",
            detach=True,
            stdin_open=True,
            tty=True,
            mem_limit="128m",
            nano_cpus=int(0.5 * 10**9),
            network_disabled=True
        )

        sock = await asyncio.to_thread(
            container.attach_socket,
            params={'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream': 1}
        )
        reader, writer = await asyncio.open_connection(sock=sock._sock)

        async def forward_container_output():
            """컨테이너의 출력을 WebSocket으로 전달"""
            try:
                while not reader.at_eof():
                    data = await reader.read(4096)
                    if not data:
                        break
                    await output_callback("stdout", data.decode('utf-8', errors='ignore'))
            except Exception as e:
                logging.warning(f"Output streaming error for {job_id}: {e}")
            finally:
                pass

        async def forward_client_input():
            """WebSocket의 입력을 컨테이너로 전달"""
            try:
                while True:
                    data_to_write = await input_queue.get()
                    if data_to_write is None:
                        break
                    writer.write(data_to_write.encode('utf-8'))
                    await writer.drain()
            except Exception as e:
                logging.warning(f"Input streaming error for {job_id}: {e}")

        output_task = asyncio.create_task(forward_container_output())
        input_task = asyncio.create_task(forward_client_input())
        
        try:
            done, pending = await asyncio.wait_for(
                asyncio.wait([output_task, input_task], return_when=asyncio.FIRST_COMPLETED),
                timeout=EXECUTION_TIME_LIMIT
            )
            for task in pending: task.cancel()
        except asyncio.TimeoutError:
            logging.warning(f"Execution time out for {job_id}")
            await output_callback("stderr", f"\nExecution exceeded the time limit of {EXECUTION_TIME_LIMIT} seconds")
            for task in [output_task, input_task]: task.cancel()
            
    except Exception as e:
        await output_callback("stderr", f"\nAn unexpected error occurred: {str(e)}")
    finally:
        await input_queue.put(None) # 입력 작업 종료
        if container:
            try:
                await asyncio.to_thread(container.stop, timeout=2)
                await asyncio.to_thread(container.remove)
            except (NotFound, APIError) as e:
                logging.warning(f"Failed to stop/remove container {job_id}: {str(e)}")
        temp_dir.cleanup()
        print(f"Temporary directory and container cleaned up for {job_id}")
        await output_callback("status", "END_OF_STREAM")