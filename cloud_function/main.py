import os
import requests
import functions_framework

# Environment variable for the FastAPI service URL
API_URL = os.environ.get("API_URL")

@functions_framework.cloud_event
def process_gcs_upload(cloud_event):
    """
    Triggered by a change to a Cloud Storage bucket.
    """
    data = cloud_event.data

    bucket = data["bucket"]
    name = data["name"]
    size = int(data["size"])
    content_type = data.get("contentType")
    time_created = data["timeCreated"]

    gcs_uri = f"gs://{bucket}/{name}"
    
    print(f"File uploaded: {gcs_uri}")

    if not API_URL:
        print("API_URL environment variable not set.")
        return

    payload = {
        "gcs_uri": gcs_uri,
        "name": name,
        "size": size,
        "content_type": content_type
    }

    try:
        response = requests.post(f"{API_URL}/process", json=payload)
        response.raise_for_status()
        print(f"Successfully called API: {response.json()}")
    except Exception as e:
        print(f"Error calling API: {str(e)}")
