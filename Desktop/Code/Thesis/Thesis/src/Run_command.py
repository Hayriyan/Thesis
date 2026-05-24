
# Run_command.py

import asyncio
import json
import subprocess
import websockets

async def run_command_and_stream_output(websocket, command):
    """
    Executes a shell command and streams its output to the WebSocket.
    
    Args:
        websocket: The WebSocket connection to stream output to
        command: The shell command to execute
    """
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Stream STDOUT
    while True:
        line = process.stdout.readline()
        if line:
            await websocket.send(json.dumps({
                "type": "output",
                "message": line.rstrip("\n")
            }))
        else:
            if process.poll() is not None:
                break
            await asyncio.sleep(0.1)

    # Stream any remaining STDERR
    error_output = process.stderr.read()
    if error_output:
        for err_line in error_output.strip().split("\n"):
            await websocket.send(json.dumps({
                "type": "error",
                "message": err_line
            }))

    # Final return code
    return_code = process.wait()
    await websocket.send(json.dumps({
        "type": "info",
        "message": f"Command exited with return code: {return_code}"
    }))
    
    return return_code

async def socket_handler(websocket):
    """
    This handler runs for each client connection, accepting commands and executing them.
    """
    try:
        await websocket.send(json.dumps({
            "type": "info",
            "message": "Connected to command execution service"
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                if data["type"] == "execute":
                    command = data["command"]
                    await websocket.send(json.dumps({
                        "type": "info",
                        "message": f"Executing: {command}"
                    }))
                    await run_command_and_stream_output(websocket, command)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))
    except websockets.ConnectionClosed:
        print("Client disconnected")

async def start_server(host="localhost", port=4444):
    """Start a WebSocket server to handle command execution"""
    async with websockets.serve(socket_handler, host, port):
        print(f"Command execution service running on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    import json
    asyncio.run(start_server())


def run_command(command):
    """
    Run a terminal command using subprocess.run() and return the output.
    Simple approach but doesn't handle all edge cases.
    
    Args:
        command (str): The command to execute
        
    Returns:
        str: Command output (stdout)
    """
    try:
        # For simple commands without complex shell features
        result = subprocess.run(command, text=True, capture_output=True)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error (code {result.returncode}): {result.stderr}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"
