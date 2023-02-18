import os
import asyncio
from fastapi import FastAPI

app = FastAPI()

def load_config():
    with open("config.json") as f:
        config = json.load(f)
    return config

async def run_script(script):
    proc = await asyncio.create_subprocess_shell(f"./{script}")
    await proc.wait()

@app.post("/run_scripts")
async def run_scripts(filepath: str):
    config = load_config()
    scripts = []
    for script in config["archiving_scripts"]:
        scripts = script["filepath"] 
    os.chdir(filepath)
    tasks = []
    for script in scripts:
        task = asyncio.create_task(run_script(script))
        tasks.append(task)
    await asyncio.gather(*tasks)
    return {"message": "Scripts have been run successfully."}
