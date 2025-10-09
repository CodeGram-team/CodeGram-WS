import asyncio
from typing import Dict, Any
from redis.asyncio import Redis
from rmq import RabbitMQClient
from dotenv import load_dotenv
import os
import json
from executor import run_code_in_docker

load_dotenv()
rmq = RabbitMQClient(os.getenv("RABBITMQ_URL"))
redis_client = Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

async def process_execution_job(job_data:Dict[str,Any]):
    """
    processing job received from message queue 
    """
    job_id = job_data.get("job_id")
    response_channel = job_data.get("response_channel")
    if not response_channel:
    	print(f"Warning: Skip response channel not fixed job{job_id}")
    	return 
    	
    result = await run_code_in_docker(language=job_data.get("language"),
                                code=job_data.get("code"))
    result_message = {
        "job_id" : job_id,
        "result" : result
    }
    print(f"Redis Channel: Publish to {response_channel}")
    await redis_client.publish(response_channel, json.dumps(result))
    
    #await rmq.publish_message("execution_result_queue", result_message)

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
    try:
        print("Server start.. Waiting for job")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeybordInterrupt detected. Worker Server closed.")
    finally:
    	loop = asyncio.get_event_loop()
    	loop.run_until_complete(rmq.close())
    	loop.run_until_complete(redis_client.close())
    
