from pathlib import Path
from typing import List
import configparser
import httpx
from rich.console import Console
from rich.prompt import Prompt
import PyPDF2  # pylint: disable=import-error

console = Console()
data_folder = "data"


class U:  # Utilities

    @staticmethod
    def get_files_in_folder(folder: str) -> List[Path]:
        """List all files in the given folder."""
        try:
            return [file for file in Path(folder).iterdir() if file.is_file()]
        except FileNotFoundError:
            console.print(f"Folder '{folder}' not found.")
            return []
        except PermissionError:
            console.print(f"Permission denied to access folder '{folder}'.")
            return []
        except Exception as inner_exception:
            console.print(f"Error: {inner_exception}")
            return []

    @staticmethod
    def display_files(files: List[Path]) -> None:
        """Display the files in the given list."""
        if not files:
            console.print("No files available in the folder.")
        else:
            console.print("Files in the folder:")
            for i, file in enumerate(files):
                console.print(f"{i + 1}. {file.name}")

    @staticmethod
    def select_file(files: List[Path]) -> Path:
        """Prompt the user to select a file from the list."""
        while True:
            try:
                selected_index = int(Prompt.ask("Enter the file number")) - 1
                if 0 <= selected_index < len(files):
                    return files[selected_index]
                else:
                    console.print("Invalid file number. Please try again.")
            except ValueError:
                console.print("Please enter a valid number.")

    @staticmethod
    def read_pdf(file_path: Path):
        """Open a PDF file and return a PdfReader object."""
        try:
            return PyPDF2.PdfReader(file_path, strict=False)
        except FileNotFoundError:
            console.print(f"File '{file_path.name}' not found.")
        except PermissionError:
            console.print(f"Permission denied to access file '{file_path.name}'.")
        except Exception as inner_exception:
            console.print(f"Error: {inner_exception}")

    @staticmethod
    def save_text_to_file(savetext, base_filename, start_page=None, end_page=None) -> None:
        try:
            filename_suffix = f"_{start_page}-{end_page}" if start_page is not None and end_page is not None else ""
            filename = Path(base_filename).stem + filename_suffix + ".txt"
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(savetext)
            console.print(f"Text saved to {filename}")
        except Exception as err:
            console.print(f"Error saving text: {err}")


def extract_text_from_pdf(reader: PyPDF2.PdfReader, start_page: int = 0, end_page: int = 999) -> str:
    """Extract text from specified range of pages in a PDF file.
    Args:reader (PyPDF2.PdfReader): PDF reader object.
    start_page (int, optional): Start page number. Defaults to first page.
    end_page (int, optional): End page number. Defaults to last page.
    Returns:str: Concatenated text from the specified pages."""
    if reader is None:
        return ""

    total_pages = len(reader.pages)
    end_page = min(end_page if end_page is not None else total_pages, total_pages)
    text = ""
    for i in range(start_page, end_page):
        try:
            page_text = reader.pages[i].extract_text() or ""
            text += page_text
        except Exception as inner_exception:
            console.print(f"Error extracting text from page {i+1}: {inner_exception}")
    return text


class summarizeAPI:

    @staticmethod
    def summarize_text(selected_text: str, focusinput: str) -> str:
        """Summarize the selected text using an API call.
        Args:selected_text (str): The text to be summarized.
        Returns:str: The summarized text."""
        configfile = r'F:\_ai\_scripts\TextSummarizer\config\config.ini'
        config = configparser.ConfigParser()
        try:
            config.read(configfile)
            api_key = config['KEY']['API_KEY']
        except KeyError:
            console.print("API key not found in config.ini.")
            return ""
        api_url = "https://api.ai21.com/studio/v1/summarize"
        payload = {"sourceType": "TEXT", "source": selected_text, "focus": focusinput}
        headers = {"accept": "application/json", "content-type": "application/json", "Authorization": f"Bearer {api_key}"}
        try:
            response = httpx.post(api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            summary_data = response.json()  # Parse the response as JSON
            summary = summary_data.get("summary", "No summary provided.")  # Extract the summary from the JSON
            console.print("\nSummary: ", summary)
            return summary
        except httpx.RequestError as request_error:
            console.print(f"Request error: {request_error}")
        except httpx.HTTPStatusError as http_error:
            console.print(f"HTTP error: {http_error}")
        return ""


class contextualAPI:

    @staticmethod
    def get_contextual_answer(context: str, question: str) -> str:
        """Get answer to a question based on the provided context using AI21 API."""
        config = configparser.ConfigParser()
        try:
            config.read('config.ini')
            api_key = config['KEY']['APIKEY']
        except KeyError:
            console.print("API key not found in config.ini.")
            return ""

        api_url = "https://api.ai21.com/studio/v1/answer"
        payload = {"context": context, "question": question}
        headers = {"accept": "application/json", "content-type": "application/json", "Authorization": f"Bearer {api_key}"}

        try:
            response = httpx.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            answer_data = response.json()
            answer = answer_data.get("answer", "Answer not found.")
            console.print("\nAnswer: ", answer)
            return answer
        except httpx.RequestError as request_error:
            console.print(f"Request error: {request_error}")
        except httpx.HTTPStatusError as http_error:
            console.print(f"HTTP error: {http_error}")
        return ""


def main() -> None:
    api_option = Prompt.ask("Select API option:\n 1. Summarize Text\n 2. Get Contextual Answer")
    if api_option == "1":
        files = U.get_files_in_folder(data_folder)
        if not files:
            return

        U.display_files(files)
        selected_file = U.select_file(files)
        if not selected_file:
            console.print("File selection cancelled.")
            return

        console.print(f"Selected file: {selected_file.name}")
        pdf_reader = U.read_pdf(selected_file)
        if not pdf_reader:
            return
        total_pages = len(pdf_reader.pages)
        console.print(f"Total number of pages: {total_pages}")

        option = Prompt.ask("Options:\n 1. Use entire PDF as source\n 2. Select specific pages as source")

        if option == "1":
            try:
                all_text = extract_text_from_pdf(pdf_reader)
                focusinput = input("Enter what should AI focus on from the source: ")
                summarized_text = summarizeAPI.summarize_text(all_text, focusinput)
                U.save_text_to_file(summarized_text, selected_file.stem)
            except Exception as er:
                console.print(f"Error: {er}")
                return
        elif option == "2":
            try:
                start_page = int(Prompt.ask("Enter the start page number:"))
                end_page = int(Prompt.ask("Enter the end page number:"))
                all_text = extract_text_from_pdf(pdf_reader, start_page - 1, end_page)
                focusinput = input("Enter what should AI focus on from the source: ")
                summarized_text = summarizeAPI.summarize_text(all_text, focusinput)
                U.save_text_to_file(summarized_text, f"{selected_file.stem}_{start_page}-{end_page}")
            except Exception as err:
                console.print(f"Error: {err}")
                return
        else:
            console.print("Invalid option selected.")
            return
    elif api_option == "2":
        try:
            all_text = extract_text_from_pdf(pdf_reader)
            question = input("Enter your question: ")
            get_contextual_answer(all_text, question)
        except Exception as err:
            console.print(f"Error: {err}")
            return
    else:
        console.print("Invalid API option selected.")
        return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"Error: {e}")
