from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging
from rich.logging import RichHandler
from rich.prompt import Prompt
import PyPDF2

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RichHandler(tracebacks_word_wrap=False, locals_max_string=140)
logger.addHandler(handler)


def get_pdf_files_in_folder(folder: str) -> List[Path]:
    return [file for file in Path(folder).glob('*.pdf')]


def display_pdf_information(pdf_reader):
    try:
        info = pdf_reader.metadata
        logger.info("PDF Document Information:")

        for attr, value in info.items():
            # Check if the value is a datetime object and format it
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            # If the value is None, indicate that it's not available
            elif value is None:
                value = "Not available"

            # Log the attribute and its value
            logger.info("%s: %s", attr.title().replace('_', ' '), value)

    except PyPDF2.utils.PdfReadError:
        logger.error("Error reading PDF metadata.")
    except Exception as e:
        logger.error("Error: %s", e)


def select_pdf_file(files: List[Path]) -> Optional[Path]:
    logger.info("Available PDF Files:")
    for i, file in enumerate(files):
        logger.info(f"{i + 1}. {file.name}")
    while True:
        try:
            choice = int(Prompt.ask("Select a PDF file by number"))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                logger.info("Invalid selection. Please try again.")
        except ValueError:
            logger.info("Please enter a number.")


def split_pdf(pdf_reader: PyPDF2.PdfReader, output_folder: Path, base_filename: str):
    """Split the given PDF into multiple files based on user input for page ranges."""
    logger.info("Enter page ranges to split (e.g., 1-3, 4-5). Leave empty to skip.")
    ranges = input().split(',')
    for page_range in ranges:
        try:
            start, end = map(int, page_range.split('-'))

            output_filename = f"{base_filename}_{start}-{end}.pdf"
            output_filepath = output_folder / output_filename
            pdf_writer = PyPDF2.PdfWriter()

            for page in range(start - 1, end):
                pdf_writer.add_page(pdf_reader.pages[page])

            with open(output_filepath, "wb") as output_file:
                pdf_writer.write(output_file)

            logger.info(f"PDF split: {output_filename} created.")
        except Exception as e:
            logger.info(f"Error processing range {page_range}: {e}")


def display_table_of_contents(pdf_reader):
    toc = pdf_reader.outline

    logger.info("Table of Contents:\n")

    def print_toc(entries, level=0):
        for entry in entries:
            if isinstance(entry, dict):
                title = entry.get("/Title")
                page_num = pdf_reader.get_destination_page_number(entry) + 1  # Fix page number offset
                indent = '    ' * level  # Indentation for sub-levels
                logger.info(f"{indent}- {title}, Page {page_num}")
            elif isinstance(entry, list):
                print_toc(entry, level + 1)
            else:
                print_toc([entry], level)

    print_toc(toc)


def main():
    current_file_path = Path(__file__).resolve()
    folder = Prompt.ask("Enter the path of the folder containing PDFs", default=str(current_file_path.parent))
    pdf_files = get_pdf_files_in_folder(folder)
    if not pdf_files:
        logger.info("No PDF files found in the directory.")
        return

    selected_pdf = select_pdf_file(pdf_files)
    if not selected_pdf:
        return

    logger.info(f"Selected: {selected_pdf}")
    pdf_reader = None
    try:
        pdf_reader = PyPDF2.PdfReader(selected_pdf)
        display_pdf_information(pdf_reader)
        display_table_of_contents(pdf_reader)
        # with open(selected_pdf, 'rb') as pdf_file:
        #     pdf_reader = PyPDF2.PdfReader(pdf_file)
        #     display_pdf_information(pdf_reader)
        #     display_table_of_contents(pdf_reader)
        split_option = Prompt.ask("Do you want to split this PDF?", default="N")
        if split_option.lower() == 'y':
            output_folder = Path(folder)  # Convert output_folder to a Path object
            if not output_folder.exists():
                logger.info(f"Output folder '{output_folder}' does not exist.")
                return
            split_pdf(pdf_reader, output_folder, selected_pdf.stem)
    except Exception as e:
        logger.info(f"Error: {e}")


if __name__ == "__main__":
    main()
