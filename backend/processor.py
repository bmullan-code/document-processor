import os
import json
import base64
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

class DocumentProcessor:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel("gemini-3-flash-preview")
        self.storage_client = storage.Client()

    def process_document(self, gcs_uri):
        """
        Main logic to process a document:
        1. Download (or use GCS URI directly if supported/efficient)
        2. Classify and extract data using Gemini
        """
        prompt = """
        Analyze the attached document and perform two tasks:
        1. Classify the document type (e.g., Mortgage Application, Appraisal Disclosure, Loan Submission Sheet, etc.).
        2. Extract all form fields and their values into a structured JSON format.

        Return ONLY a JSON object with the following structure:
        {
            "document_type": "string",
            "extracted_data": {
                "field_1": "value_1",
                ...
            }
        }
        """

        try:
            # Use Gemini with GCS URI
            document_part = Part.from_uri(gcs_uri, mime_type="application/pdf")
            
            response = self.model.generate_content(
                [document_part, prompt],
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                ),
            )

            # Parse the JSON response
            result = json.loads(response.text)
            return result, None
        except Exception as e:
            print(f"Gemini processing error: {str(e)}")
            return None, str(e)
