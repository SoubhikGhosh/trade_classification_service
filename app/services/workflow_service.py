import logging
import os
from typing import Dict, List

from .ai_provider_interface import AIProviderInterface
from .document_processor import DocumentProcessor
from ..utils.file_utils import create_random_to_original_filename_lookup, read_mapping_file
from ..schemas import ClassifiedDocumentsResponse, ProcessFolderRequest
from .. import prompts

logger = logging.getLogger(__name__)

class WorkflowService:
    def __init__(self, ai_provider: AIProviderInterface):
        self.ai_provider = ai_provider
        self.doc_processor = DocumentProcessor()

    def process_folder(self, request: ProcessFolderRequest, request_id: str) -> ClassifiedDocumentsResponse:
        log_extra = {'request_id': request_id, 'folder_path': request.folder_path}
        
        logger.info("Starting document preprocessing.", extra=log_extra)
        preprocessed_output = self.doc_processor.preprocess_folder(request.folder_path)
        
        if not preprocessed_output:
            logger.warning("No processable files found in the folder.", extra=log_extra)
            return ClassifiedDocumentsResponse(request_id=request_id, documents=[], processing_metadata={"notes": "No files were found to process."})

        logger.info(f"Preprocessing complete. Found {len(preprocessed_output)} pages.", extra=log_extra)
        
        # Prepare parts for the model prompt
        manifest = [{"document_page_image_filename": item["filename"]} for item in preprocessed_output]
        manifest_part = [{"type": "text", "text": f'<image_manifest>{json.dumps(manifest)}</image_manifest>'}]
        
        image_parts = [{"type": "image_url", "image_url": f'data:{item["mime_type"]};base64,{item["base64_data"]}'} for item in preprocessed_output]
        
        input_parts = manifest_part + image_parts

        logger.info("Invoking AI provider for clustering, classification, and sequencing.", extra=log_extra)
        prompt_to_use = prompts.document_clustering_sequencing_classification_si_prompt_multi_pages_3
        
        ai_response = self.ai_provider.cluster_classify_and_sequence(
            image_parts=input_parts,
            prompt=prompt_to_use,
            request_id=request_id
        )
        logger.info(f"AI provider returned {len(ai_response.documents)} documents.", extra=log_extra)

        if request.mapping_file_path:
            logger.info("Mapping filenames to originals.", extra=log_extra)
            mapping_data = read_mapping_file(request.mapping_file_path)
            lookup = create_random_to_original_filename_lookup(mapping_data)
            
            for document in ai_response.documents:
                original_pages = []
                for page_id in document.pages:
                    original_filename = "NOT_FOUND"
                    # Match base filename (e.g., "5elPNY" in "5elPNY.pdf") against page_id
                    for random_key, original_value in lookup.items():
                        base_random_key = os.path.splitext(random_key)[0]
                        if base_random_key in page_id:
                            original_filename = original_value
                            break
                    original_pages.append(original_filename)
                document.pages = original_pages
        
        return ai_response