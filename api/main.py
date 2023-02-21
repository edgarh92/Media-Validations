import os
import asyncio
from fastapi import FastAPI
import json

app = FastAPI()

def load_config():
    """Load the config.json file."""
    with open("/Users/ehernand/Projects/Media-Validations/config.json") as f:
        config = json.load(f)
    return config

async def run_script(script):
    """Run a shell script asynchronously.

    Args:
        script (str): The name of the shell script to run.

    Returns:
        str: A message indicating that the script has completed.
    """
    proc = await asyncio.create_subprocess_shell(f"./{script}")
    await proc.wait()

@app.post("/run_scripts")
async def run_scripts(filepath: str):
    """Run a series of shell scripts asynchronously on a specified filepath.

    Args:
        filepath (str): The filepath to run the shell scripts on.

    Returns:
        dict: A dictionary containing the results of the script executions.
    """
    config = load_config()
    scripts = []
    for key, value in config["Social Media Platforms"].items():
        scripts.append(value['filepath'])
    os.chdir(filepath)
    tasks = []
    for script in scripts:
        task = asyncio.create_task(run_script(script))
        tasks.append(task)
    await asyncio.gather(*tasks)
    return {"message": "Scripts have been run successfully."}
