import easyocr
import re
from PIL import Image
import numpy as np

class OCREngine:
    def __init__(self):
        # Initialize the reader (this will download models on first run)
        self.reader = easyocr.Reader(['en'])

    def extract_text(self, image_input):
        """Extract text from PIL Image or file path."""
        # Convert PIL to numpy array if necessary
        if isinstance(image_input, Image.Image):
            image_input = np.array(image_input)
            
        results = self.reader.readtext(image_input)
        # Combine all extracted text into one string
        extracted_text = " ".join([res[1] for res in results])
        return extracted_text

    def verify_amount(self, text, target_amount):
        """
        Verify if the target_amount exists in the text.
        Handles common OCR issues like commas or decimals.
        """
        # Convert to string and clean target_amount for searching
        target_str = str(int(target_amount))
        
        # Clean extracted text: remove commas, keep only numbers
        clean_text = re.sub(r'[^0-9]', '', text)
        
        if target_str in clean_text:
            return True
        return False
