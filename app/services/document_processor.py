import os
import io
import base64
import logging
import magic
import pymupdf
import cv2
import numpy
from PIL import Image
from typing import List, Dict

from ..config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles all document preprocessing tasks, including PDF-to-image conversion
    and image enhancement.
    """

    def _get_file_mime_type(self, file_path: str) -> str:
        """Get the MIME type of a file using python-magic for reliability."""
        try:
            return magic.from_file(file_path, mime=True)
        except Exception as e:
            logger.warning(f"Could not determine MIME type for {file_path} using python-magic: {e}. Falling back to mimetypes.")
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'


    def _classify_pdf_page(self, page: pymupdf.Page) -> str:
        """Classify a PDF page as 'digital' or 'scanned' based on text content."""
        return "digital" if page.get_text("text").strip() else "scanned"

    def _image_to_np_array(self, image: Image.Image) -> numpy.ndarray:
        """Convert PIL.Image to OpenCV BGR numpy array."""
        return cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)

    def _np_array_to_image(self, arr: numpy.ndarray) -> Image.Image:
        """Convert a numpy array (BGR or Grayscale) to a PIL RGB Image."""
        if arr.ndim == 2: # Grayscale
            return Image.fromarray(arr).convert("RGB")
        # BGR to RGB
        return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

    def image_enhancement_pipeline(self, image: Image.Image) -> Image.Image:
        """Run a PIL image through a series of CV2 enhancements."""
        img_np = self._image_to_np_array(image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10.0, templateWindowSize=7, searchWindowSize=21)

        # Deskew logic
        inv = cv2.bitwise_not(denoised)
        thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        coords = numpy.column_stack(numpy.where(thresh > 0))
        
        deskewed = denoised
        if coords.shape[0] > 10: # Only process if there are enough points
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            if abs(angle) > settings.SMALL_ANGLE_THRESHOLD:
                (h, w) = denoised.shape
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                deskewed = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Sharpen & Contrast
        kernel = numpy.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(src=deskewed, ddepth=-1, kernel=kernel)
        adjusted = cv2.convertScaleAbs(sharpened, alpha=settings.SHARPEN_CONTRAST_ALPHA, beta=settings.SHARPEN_CONTRAST_BETA)
        
        return self._np_array_to_image(adjusted)

    def _process_pdf_to_images(self, pdf_bytes: bytes) -> List[Dict]:
        """Convert each page of a PDF to an enhanced image."""
        images_data = []
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        scaling_factor = settings.TARGET_DPI / settings.DEFAULT_DPI
        matrix = pymupdf.Matrix(scaling_factor, scaling_factor)

        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            enhanced_img = self.image_enhancement_pipeline(img)
            
            buffer = io.BytesIO()
            enhanced_img.save(buffer, format=settings.DEFAULT_IMAGE_FORMAT)
            
            images_data.append({
                "page_number": page_num + 1,
                "classification": self._classify_pdf_page(page),
                "base64_data": base64.b64encode(buffer.getvalue()).decode("utf-8"),
                "mime_type": f"image/{settings.DEFAULT_IMAGE_FORMAT}"
            })
        return images_data

    def _process_image(self, file_path: str) -> List[Dict]:
        """Process a single image file."""
        img = Image.open(file_path).convert("RGB")
        enhanced_img = self.image_enhancement_pipeline(img)
        
        buffer = io.BytesIO()
        enhanced_img.save(buffer, format=settings.DEFAULT_IMAGE_FORMAT)
        
        return [{
            "page_number": 1,
            "classification": "scanned",
            "base64_data": base64.b64encode(buffer.getvalue()).decode("utf-8"),
            "mime_type": f"image/{settings.DEFAULT_IMAGE_FORMAT}"
        }]

    def preprocess_folder(self, data_folder: str) -> List[Dict]:
        """Iterate through a folder, preprocess all files, and return image data."""
        processed_pages = []
        if not os.path.isdir(data_folder):
            raise FileNotFoundError(f"The specified folder does not exist: {data_folder}")

        for filename in sorted(os.listdir(data_folder)):
            filepath = os.path.join(data_folder, filename)
            if not os.path.isfile(filepath):
                continue
            
            try:
                mime_type = self._get_file_mime_type(filepath)
                logger.info(f"Processing file: {filename} (MIME: {mime_type})")

                pages_data = []
                if mime_type == "application/pdf":
                    with open(filepath, "rb") as f:
                        pages_data = self._process_pdf_to_images(f.read())
                elif mime_type.startswith("image/"):
                    pages_data = self._process_image(filepath)
                else:
                    logger.warning(f"Skipping unsupported file type: {filename}")
                    continue
                
                # Add original filename to each page for tracing
                for page in pages_data:
                    page['filename'] = f"{filename}_page_{page['page_number']}"
                processed_pages.extend(pages_data)

            except Exception as e:
                logger.error(f"Failed to process file {filename}", exc_info=True)
                # Decide whether to raise the error or just log and continue
        
        return processed_pages