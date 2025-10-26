from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Path
import asyncio, json
from executor import run_code_in_docker

app = FastAPI(description="Code Executor Worker Server")

@app.websocket("/ws/worker/{language}")
async def websocket_execute(websocket:WebSocket, 
                            language:str=Path(...),
                            job_id:str=Query(...)):
    
    await websocket.accept()
    print(f"New execution session {job_id}")
    
    try:
        init_msg = await websocket.receive_text()
        data = json.loads(init_msg)
        code = data.get("code")
        if not code:
            await websocket.send_json({"type" : "error", "message" : "No code provided"})
            await websocket.close()
            return
    except Exception:
        await websocket.send_json({"type" : "error", "message" : "Invalid initial message"})

    input_queue = asyncio.Queue()
    
    async def output_callback(type_:str, data_:str):
        await websocket.send_json({"type" : type_, "data" : data_})
    
    async def read_client_input():
        try:
            while True:
                msg = await websocket.receive_text()
                await input_queue.put(msg + "\n")
        except WebSocketDisconnect:
            print(f"Client disconnected: {job_id}")
            await input_queue.put(None)
    
    worker_task = asyncio.create_task(
        run_code_in_docker(language=language, code=code, job_id=job_id, input_queue=input_queue, output_callback=output_callback)
    )
    input_task = asyncio.create_task(read_client_input())
    
    done, pending = await asyncio.wait(
        [worker_task, input_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    print(f"Session {job_id} closed")
    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
