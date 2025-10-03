import asyncio
from typing import Dict, Any
from rmq import RabbitMQClient
from dotenv import load_dotenv
import os
from executor import run_code_in_docker

load_dotenv()

async def process_execution_job(job_data:Dict[str,Any]):
    """
    processing job received from message queue 
    """
    job_id = job_data.get("job_id")
    result = run_code_in_docker(language=job_data.get("language"),
                                code=job_data.get("code"))
    result_message = {
        "job_id" : job_id,
        "result" : result
    }
    await rmq.publish_message("execution_result_queue", result_message)

async def main():
    """
    Connect RabbitMQ and consume message 
    """
    await rmq.connect()
    
    await rmq.start_consuming(
        queue_name="code_execution_queue",
        on_message_callback=process_execution_job
    )

if __name__ == "__main__":
    rmq = RabbitMQClient(os.getenv("RABBITMQ_URL"))
    try:
        print("Server start")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[!] KeybordInterrupt detected Worker Server closed.")
    finally:
        asyncio.run(rmq.close())
    