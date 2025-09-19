import os
import re
import string
import pytesseract
from PIL import Image
from pathlib import Path

# --- CONFIGURATION ---

# 1. Set the path to your Tesseract executable if it's not in your system's PATH.
#    For Windows, it might be: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#    For Linux/macOS, this is often not needed if installed correctly.
#    Uncomment the line below and set the correct path if you get a "Tesseract not found" error.
# pytesseract.pytesseract.tesseract_cmd = r'<your_tesseract_path>'

# Import config paths
from config import DOCUMENT_RAW_DIR, DOCUMENT_DATASET_DIR

# 2. Define the input and output directories.
INPUT_DIRECTORY = str(DOCUMENT_RAW_DIR / "property_deeds")
OUTPUT_DIRECTORY = str(DOCUMENT_DATASET_DIR / "property_deeds")

# 3. Specify the language for OCR.
OCR_LANGUAGE = 'spa'  # Spanish

# 4. List of image extensions to process.
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp','.webp']


def process_image(image_path, output_path):
    """
    Performs OCR on a single image file and saves the text output.

    Args:
        image_path (str): The full path to the input image.
        output_path (str): The full path where the output .txt file will be saved.
    """
    try:
        # Open the image file using Pillow
        with Image.open(image_path) as img:
            # Step 1: Perform OCR using pytesseract
            # This is equivalent to `tesseract your_image.png stdout -l spa+eng`
            # The 'lang' argument handles both Spanish and English.
            raw_text = pytesseract.image_to_string(Image.open(image_path), lang=OCR_LANGUAGE)

            # --- Text Processing Steps ---

            # Make text lowercase to ensure case-insensitive uniqueness (like `sort -u`)
            text = raw_text.lower()

            # Step 2: Replace all punctuation with a space
            # This is equivalent to `tr '[:punct:]' ' '`
            # We use a regular expression for a robust replacement.
            text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)

            # Step 3: Split the text into words
            # This is equivalent to `tr -s ' ' '\n'`
            # The .split() method naturally handles multiple spaces between words.
            #words = text.split()

            # Step 4: Get a unique, sorted list of words
            # This is equivalent to `sort -u`
            # A `set` stores only unique items, and `sorted()` sorts them.
            #unique_sorted_words = sorted(list(set(words)))

            # Write the extracted text to the output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

        print(f"  [SUCCESS] Processed '{image_path.name}' -> '{output_path.name}'")

    except pytesseract.TesseractNotFoundError:
        print("\n--- TESSERACT NOT FOUND ---")
        print("Error: 'tesseract' is not installed or not in your system's PATH.")
        print("Please install Tesseract OCR from the official repository and try again.")
        print("If installed, you may need to set the `pytesseract.pytesseract.tesseract_cmd` path in the script.")
        # Stop the script if Tesseract is not found.
        exit()
    except Exception as e:
        print(f"  [ERROR] Could not process '{image_path.name}': {e}")


def main():
    """
    Main function to walk through the input directory, perform OCR,
    and save results in the output directory, preserving the structure.
    """
    input_path = Path(INPUT_DIRECTORY)
    output_path = Path(OUTPUT_DIRECTORY)

    if not input_path.is_dir():
        print(f"Error: Input directory '{INPUT_DIRECTORY}' not found.")
        print("Please create it and place your document images inside.")
        return

    print(f"Starting OCR process for directory: '{input_path}'")
    print(f"Output will be saved to: '{output_path}'")
    print("-" * 30)

    # Walk through the input directory, including all subdirectories
    for dirpath, _, filenames in os.walk(input_path):
        # Determine the corresponding output directory
        relative_path = Path(dirpath).relative_to(input_path)
        current_output_dir = output_path / relative_path

        # Create the subdirectory in the output folder if it doesn't exist
        current_output_dir.mkdir(parents=True, exist_ok=True)

        if relative_path != Path('document_raw'):
            print(f"\nProcessing category: '{relative_path}'...")

        for filename in filenames:
            file_path = Path(dirpath) / filename

            # Check if the file has a supported image extension
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Define the output .txt file path
                output_txt_path = current_output_dir / f"{file_path.stem}.txt"

                # Process the image
                process_image(file_path, output_txt_path)

    print("-" * 30)
    print("OCR processing complete.")


if __name__ == "__main__":
    main()