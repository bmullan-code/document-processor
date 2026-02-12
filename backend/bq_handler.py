import datetime
import json
import os
from google.cloud import bigquery

class BigQueryHandler:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.dataset_id = os.getenv("BQ_DATASET_ID", "document_processing")
        self.table_id = os.getenv("BQ_TABLE_ID", "processed_documents")
        self.client = bigquery.Client(project=self.project_id)
        self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    def insert_record(self, record):
        """
        Inserts a single record into the BigQuery table.
        Record should be a dict matching the schema.
        """
        try:
            # Ensure extracted_data is a JSON string if it's a dict
            if isinstance(record.get("extracted_data"), dict):
                record["extracted_data"] = json.dumps(record["extracted_data"])
            
            # Add timestamp if not present
            if "processed_at" not in record:
                record["processed_at"] = datetime.datetime.utcnow().isoformat()

            errors = self.client.insert_rows_json(self.table_ref, [record])
            if errors:
                print(f"BigQuery insertion errors: {errors}")
                return False, str(errors)
            return True, None
        except Exception as e:
            print(f"BigQuery exception: {str(e)}")
            return False, str(e)

    def list_records(self, limit: int = 100, date_filter: str = None):
        """
        Lists records from the BigQuery table.
        date_filter should be in YYYY-MM-DD format.
        """
        try:
            query = f"SELECT * FROM `{self.table_ref}`"
            if date_filter:
                query += f" WHERE DATE(processed_at) = '{date_filter}'"
            query += f" ORDER BY processed_at DESC LIMIT {limit}"
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            records = []
            for row in results:
                record = dict(row)
                # Convert timestamp and json to serializable formats
                if record.get("processed_at"):
                    record["processed_at"] = record["processed_at"].isoformat()
                records.append(record)
            
            return records, None
        except Exception as e:
            print(f"BigQuery list exception: {str(e)}")
            return None, str(e)
