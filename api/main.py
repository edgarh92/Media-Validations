from fastapi import FastAPI, File, UploadFile
from pathlib import Path
import json
from kafka import KafkaProducer
import os
import asyncio
import json

KAFKA_TOPIC = "media_validation_results"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_PRODUCER = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

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


from fastapi import FastAPI, File, UploadFile
from pathlib import Path
import json

app = FastAPI()

with open("youtube_upload_standards.json", "r") as f:
    UPLOAD_STANDARDS = json.load(f)


def validate_video(file_path):
    # Extract information about the video file using mediainfo
    media_info = mediainfo.MediaInfo.parse(file_path.as_posix())
    general_info = media_info.to_data()["tracks"][0]
    
    # Validate the video file against the standards in UPLOAD_STANDARDS
    valid = True
    details = []
    
    # Check video duration
    duration = float(general_info["duration"])
    max_duration = UPLOAD_STANDARDS["max_duration_seconds"]
    if duration > max_duration:
        valid = False
        details.append(f"Video duration {duration} seconds is longer than the maximum allowed duration of {max_duration} seconds.")
    
    # Check video resolution
    width = int(general_info["width"])
    height = int(general_info["height"])
    max_width = UPLOAD_STANDARDS["max_resolution"]["width"]
    max_height = UPLOAD_STANDARDS["max_resolution"]["height"]
    if width > max_width or height > max_height:
        valid = False
        details.append(f"Video resolution {width}x{height} is higher than the maximum allowed resolution of {max_width}x{max_height}.")
    
    return {"valid": valid, "details": details}

@app.post("/validate_media")
async def validate_media(file: UploadFile = File(...)):
    # Save the uploaded file to disk
    file_path = Path(file.filename)
    with file_path.open("wb") as buffer:
        buffer.write(await file.read())
    
    # Validate the uploaded file
    validation_result = validate_video(file_path)
    
    # Send the validation result to a Kafka topic
    KAFKA_PRODUCER.send(KAFKA_TOPIC, validation_result)
    
    # Delete the uploaded file
    file_path.unlink(missing_ok=True)
    
    # Return the validation result
    if validation_result["valid"]:
        return {"message": "Media validation successful"}
    else:
        return {"error": "Media validation failed", "details": validation_result["details"]}
