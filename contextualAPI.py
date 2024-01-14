import requests
import configparser
from pathlib import Path
from typing import List, Optional


class contextualAPI:
    API_URL = "https://api.ai21.com/studio/v1/library/answer"

    @staticmethod
    def get_api_key() -> str:
        config = configparser.ConfigParser()
        try:
            config.read('config.ini')
            return config['KEY']['APIKEY']
        except KeyError:
            console.print("API key not found in config.ini.")
            return ""

    @staticmethod
    def get_contextual_answer_from_library(question: str,
                                           path: Optional[str] = None,
                                           labels: Optional[List[str]] = None,
                                           file_ids: Optional[List[str]] = None) -> str:
        """Get answer to a question based on the content in the document library."""
        api_key = contextualAPI.get_api_key()
        if not api_key:
            return ""

        headers = {"accept": "application/json", "content-type": "application/json", "Authorization": f"Bearer {api_key}"}

        payload = {"question": question, "path": path, "labels": labels, "fileIds": file_ids}

        try:
            response = requests.post(contextualAPI.API_URL, json=payload, headers=headers)
            response.raise_for_status()
            answer_data = response.json()
            answer = answer_data.get("answer", "Answer not found.")
            console.print("\nAnswer: ", answer)
            return answer
        except requests.RequestError as request_error:
            console.print(f"Request error: {request_error}")
        except requests.HTTPStatusError as http_error:
            console.print(f"HTTP error: {http_error}")
        return ""


# Example usage in main function:
def main() -> None:
    question = input("Enter your question: ")
    path = input("Enter path (optional, press enter to skip): ")
    labels_input = input("Enter labels separated by commas (optional, press enter to skip): ")
    file_ids_input = input("Enter file IDs separated by commas (optional, press enter to skip): ")

    labels = labels_input.split(",") if labels_input else None
    file_ids = file_ids_input.split(",") if file_ids_input else None

    contextualAPI.get_contextual_answer_from_library(question, path=path, labels=labels, file_ids=file_ids)


if __name__ == "__main__":
    main()
