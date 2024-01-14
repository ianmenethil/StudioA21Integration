import httpx
import asyncio
from configparser import ConfigParser
from rich.console import Console
from rich.table import Table

console = Console()


class AI21LibraryAPI:
    BASE_URL = "https://api.ai21.com/studio/v1/library/files"

    def __init__(self, api_key):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.console = Console()

    async def upload_document(self, file_path, path=None, labels=None, public_url=None):
        async with httpx.AsyncClient() as client:
            try:
                with open(file_path, 'rb') as file:
                    files = {"file": (file_path, file, "text/plain")}
                    data = {"path": path, "labels": labels, "publicUrl": public_url}
                    response = await client.post(self.BASE_URL, headers=self.headers, data=data, files=files)
                return response.json()
            except Exception as e:
                self.console.log(f"Error during upload: {e}")
                return None

    async def retrieve_documents_list(self, offset=0, limit=100):
        async with httpx.AsyncClient() as client:
            params = {"offset": offset, "limit": limit}
            response = await client.get(self.BASE_URL, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                self.console.log(f"Error retrieving document list: {response.text}")
                return None

    async def retrieve_document_by_id(self, file_id):
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{file_id}"
            response = await client.get(url, headers=self.headers)
            return response.json()

    async def update_document(self, file_id, labels=None, public_url=None):
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{file_id}"
            data = {"labels": labels, "publicUrl": public_url}
            response = await client.put(url, headers=self.headers, json=data)
            if response.status_code == 200:
                return "Update successful"
            else:
                self.console.log(f"Error updating document: {response.text}")
                return None

    async def delete_document(self, file_id):
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{file_id}"
            response = await client.delete(url, headers=self.headers)
            return response.status_code


def print_document_list(documents):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File ID", style="dim")
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("File Type")
    table.add_column("Size (Bytes)")
    table.add_column("Labels")
    table.add_column("Public URL")
    table.add_column("Created By")
    table.add_column("Creation Date")
    table.add_column("Last Updated")
    table.add_column("Status")

    for doc in documents:
        labels = ", ".join(doc['labels']) if doc['labels'] else "None"
        table.add_row(doc['fileId'], doc['name'], doc.get('path', 'None'), doc['fileType'], str(doc['sizeBytes']), labels,
                      doc.get('publicUrl', 'None'), doc['createdBy'], doc['creationDate'], doc['lastUpdated'], doc['status'])

    console.print(table)


def get_api_key(config_path):
    config = ConfigParser()
    config.read(config_path)
    return config['DEFAULT']['API_KEY']


def user_choice():
    choices = ["Upload Document", "Retrieve Document List", "Retrieve Document by ID", "Update Document", "Delete Document"]
    for i, choice in enumerate(choices):
        print(f"{i}. {choice}")
    choice = input("Choose an action by number: ")
    return int(choice) if choice.isdigit() and int(choice) < len(choices) else None


CONFIGFILE = 'config/config.ini'


async def main():
    try:
        config_path = CONFIGFILE
        api_key = get_api_key(config_path)
        ai21_api = AI21LibraryAPI(api_key)

        action = user_choice()
        if action is None:
            print("Invalid choice. Exiting.")
            return
        print(f"Selected action: {action}")

        if action == 0:
            file_to_upload = input("Enter the full path of the file to upload: ")
            if file_to_upload:
                path = input("Enter the path (optional): ")
                labels_str = input("Enter labels separated by commas (optional): ")
                labels = labels_str.split(',') if labels_str else None
                public_url = input("Enter the public URL (optional): ")
                upload_response = await ai21_api.upload_document(file_to_upload, path=path, labels=labels, public_url=public_url)
                print(upload_response)

        elif action == 1:
            offset = input("Enter the offset (optional, default 0): ")
            limit = input("Enter the limit (optional, default 100): ")
            documents_list = await ai21_api.retrieve_documents_list(offset=int(offset) if offset else 0, limit=int(limit) if limit else 100)
            if documents_list is not None:
                print_document_list(documents_list)
                # Print FileID and Name
                print("FileID\t\tName")
                for doc in documents_list:
                    print(f"{doc['fileId']}\t{doc['name']}")
        elif action == 2:
            file_id = input("Enter the file ID to retrieve: ")
            if file_id:
                document_details = await ai21_api.retrieve_document_by_id(file_id)
                console.print(document_details)

        elif action == 3:
            file_id = input("Enter the file ID to update: ")
            if file_id:
                labels_str = input("Enter updated labels separated by commas (optional): ")
                labels = labels_str.split(',') if labels_str else None
                public_url = input("Enter the updated public URL (optional): ")
                update_status = await ai21_api.update_document(file_id, labels=labels, public_url=public_url)
                console.print(f"Update status: {update_status}")

        elif action == 4:
            file_id = input("Enter the file ID to delete: ")
            if file_id:
                delete_status = await ai21_api.delete_document(file_id)
                console.print(f"Delete status: {delete_status}")

    except Exception as e:
        console.print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
