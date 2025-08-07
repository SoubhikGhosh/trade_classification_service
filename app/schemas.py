from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# =============================================================================
# --- Schemas for this Microservice's API I/O ---
# =============================================================================

class ProcessFolderRequest(BaseModel):
    folder_path: str = Field(..., description="The absolute path to the folder containing documents to process.")
    mapping_file_path: Optional[str] = Field(None, description="Optional path to the JSON file mapping random to original filenames.")

class ClassifiedDocument(BaseModel):
    document_id: Optional[str] = Field(None, description="A unique identifier for the processed document.")
    document_type: Optional[str] = Field(None, description="The final classified type of the entire document.")
    document_summary: Optional[str] = Field(None, description="A summary of the overall document.")
    pages: List[str] = Field(description="The sequenced list of page filenames.")
    reasoning: Optional[str] = Field(None, description="The model's reasoning for the classification and sequencing.")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="The model's confidence in its analysis (0.0 to 1.0).")

class ClassifiedDocumentsResponse(BaseModel):
    request_id: str = Field(description="The unique identifier for this processing request.")
    documents: List[ClassifiedDocument] = Field(description="The list of documents clustered, sequenced, and classified from the input files.")
    processing_metadata: Optional[dict] = Field(None, description="Metadata about the processing job, e.g., latency, token usage.")

# =============================================================================
# --- Schemas from Original `prompts.py` (For potential future use) ---
# Note: These are not used in the current classification workflow but are
# retained as they define the data structure for potential future extraction tasks.
# =============================================================================

class KeyField(BaseModel):
    """Represents field name(s) and respective value(s) extracted from the document page."""
    field_name: Optional[str] = Field(
        default=None,
        description="The name of the extracted field, e.g., 'Invoice Number' or 'Start Date'."
    )
    field_value: Optional[str] = Field(
        default=None,
        description="The value corresponding to the field_name, e.g., 'INV-12345' or '2023-10-27'."
    )

class Table(BaseModel):
    """Represents table data and respective value(s) extracted from the document page."""
    table_title: Optional[str] = Field(
        default=None,
        description="The title or caption of the table, if any is detected."
    )
    columns: Optional[List[str]] = Field(
        default=None,
        description="A list of strings representing the column headers of the table."
    )
    rows: Optional[List[List[str]]] = Field(
        default=None,
        description="A list of lists, where each inner list represents a row of data in the table."
    )
    approx_position_on_page: Optional[str] = Field(
        default=None,
        description="A general description of the table's location on the page (e.g., 'top-right', 'bottom-half')."
    )

class VisualElements(BaseModel):
    """Any visual elements extracted from the page."""
    charts_present: Optional[bool] = Field(
        default=None,
        description="A boolean flag indicating if any charts or graphs were detected on the page."
    )
    images_or_logos: Optional[List[str]] = Field(
        default=None,
        description="A list of descriptions or identifiers for detected images or logos."
    )
    large_headers: Optional[List[str]] = Field(
        default=None,
        description="A list of text content from prominent headers or titles on the page."
    )
    footnotes_present: Optional[bool] = Field(
        default=None,
        description="A boolean flag indicating if footnotes were detected on the page."
    )

class DocumentAnalysis(BaseModel):
    """A composite document analysis objects consisting of attributes, and markers extracted from the document."""
    document_types_guess: Optional[List[str]] = Field(
        default=None,
        description="A list of potential document types based on the page's content (e.g., ['invoice', 'receipt', 'report'])."
    )
    overall_summary: Optional[str] = Field(
        default=None,
        description="A concise summary of the document page's content."
    )
    document_tags: Optional[List[str]] = Field(
        default=None,
        description="A list of keywords or tags that categorize the page's content (e.g., ['financial', 'legal', 'confidential'])."
    )
    language: Optional[str] = Field(
        default=None,
        description="The detected language of the text on the page, preferably as an ISO 639-1 code (e.g., 'en', 'es')."
    )
    contains_handwritten_content: Optional[bool] = Field(
        default=None,
        description="Boolean flag indicating if handwritten text is present on the page."
    )
    contains_signature_like_elements: Optional[bool] = Field(
        default=None,
        description="Boolean flag for the presence of elements that resemble signatures."
    )
    contains_stamp_or_seal_like_elements: Optional[bool] = Field(
        default=None,
        description="Boolean flag for the presence of elements that resemble stamps or seals."
    )
    has_watermark: Optional[bool] = Field(
        default=None,
        description="Boolean flag indicating if a watermark is detected on the page."
    )
    possible_page_number: Optional[int] = Field(
        default=None,
        description="The detected page number, if any is found printed on the page."
    )

class Signature(BaseModel):
    """Represents a detected signature on a page, including its location."""
    bounding_box: List[int] = Field(
        description="The coordinates of the signature's bounding box in [x1, y1, x2, y2] format."
    )
    signature_metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="A dictionary of additional metadata, e.g., {'confidence': '0.92', 'type': 'Handwritten'}."
    )

class Stamp(BaseModel):
    """Represents a detected stamp or seal on a page, including its location and content."""
    bounding_box: List[int] = Field(
        description="The coordinates of the stamp's bounding box in [x1, y1, x2, y2] format."
    )
    stamp_text: Optional[str] = Field(
        default=None,
        description="The text content extracted from the stamp or seal."
    )
    stamp_metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="A dictionary of additional metadata, e.g., {'color': 'blue', 'shape': 'round'}."
    )

class DocumentPageSummary(BaseModel):
    """A comprehensive summary of a single page within a document."""
    filename: str = Field(
        description="The original filename of the document page."
    )
    document_analysis: Optional[DocumentAnalysis] = Field(
        default=None,
        description="A composite object containing the overall analysis of the page."
    )
    key_fields: Optional[List[KeyField]] = Field(
        default=None,
        description="A list of key-value pairs extracted from the page."
    )
    tables: Optional[List[Table]] = Field(
        default=None,
        description="A list of tables extracted from the page."
    )
    visual_elements: Optional[VisualElements] = Field(
        default=None,
        description="An object detailing any visual elements found on the page."
    )
    signatures: Optional[List[Signature]] = Field(
        default=None,
        description="A list of detected signature objects found on the page."
    )
    stamps: Optional[List[Stamp]] = Field(
        default=None,
        description="A list of detected stamp or seal objects found on the page."
    )
    potential_anomalies: Optional[List[str]] = Field(
        default=None,
        description="Any detectable anomalies found on the page, such as 'blurry_section', 'torn_edge', or 'unusual_marking'."
    )
    page_notes: Optional[str] = Field(
        default=None,
        description="Any additional notes about the document page that have not been captured in other fields."
    )

class DocumentPageSummaries (BaseModel):
    document_page_summaries: Optional[List[DocumentPageSummary]] = Field (
        default=None,
        description="This field is a consolidated list of document page summaries created based on the document page images provided to the model."
    )

class NonExtractedDocument(BaseModel):
    """
    Represents an entire document as a sequenced collection of its pages.
    The "pages" attribute holds the list of DocumentPageSummary objects,
    where the order in the list corresponds to the page number (index 0 is page 1, etc.).

    Note that that pages here is a list of strings representing the file names.
    This document will not contain any extracted data, but only classification and sequencing.
    """
    document_id: Optional[str] = Field(
        default=None,
        description="A unique identifier for the processed document."
    )
    document_type: Optional[str] = Field(
        default=None,
        description="The final classified type of the entire document after analyzing all its pages."
    )
    document_summary: Optional[str] = Field(
        default=None,
        description="A summary of the overall document, generated after analyzing all pages in sequence."
    )
    pages: List[str] = Field(
        description="The sequenced list of page-by-page filenames."
    )

class NonExtractedDocumentWithRationale(BaseModel):
    """
    Represents an entire document as a sequenced collection of its pages, with rationale.
    The "pages" attribute holds the list of DocumentPageSummary objects,
    where the order in the list corresponds to the page number (index 0 is page 1, etc.).

    Note that that pages here is a list of strings representing the file names.
    This document will not contain any extracted data, but only classification and sequencing.
    """
    document_id: Optional[str] = Field(
        default=None,
        description="A unique identifier for the processed document."
    )
    document_type: Optional[str] = Field(
        default=None,
        description="The final classified type of the entire document after analyzing all its pages."
    )
    document_summary: Optional[str] = Field(
        default=None,
        description="A summary of the overall document, generated after analyzing all pages in sequence."
    )
    document_type_rationale: Optional[str] = Field(
        default=None,
        description="An articulate justification of why the pages in this document cluster belong together."
    )
    pages: List[str] = Field(
        description="The sequenced list of page-by-page filenames."
    )

class NonExtractedDocuments(BaseModel):
    """A top-level container for a list of sequenced and classified documents."""
    documents: List[NonExtractedDocument] = Field(
        description="The list of documents clustered, sequenced, and classified from all the input files."
    )

class NonExtractedDocumentsWithRationale(BaseModel):
    """A top-level container for a list of sequenced and classified documents, with rationale."""
    documents: List[NonExtractedDocumentWithRationale] = Field(
        description="The list of documents clustered, sequenced, and classified from all the input files."
    )

class Document(BaseModel):
    """
    Represents an entire document as a sequenced collection of its pages.
    The 'pages' attribute holds the list of DocumentPageSummary objects,
    where the order in the list corresponds to the page number (index 0 is page 1, etc.).
    """
    document_id: Optional[str] = Field(
        default=None,
        description="A unique identifier for the processed document."
    )
    document_type: Optional[List[str]] = Field(
        default=None,
        description="The final classified type(s) of the entire document after analyzing all its pages."
    )
    document_summary: Optional[str] = Field(
        default=None,
        description="A summary of the overall document, generated after analyzing all pages in sequence."
    )
    pages: List[DocumentPageSummary] = Field(
        description="The sequenced list of page-by-page summaries."
    )

class Documents(BaseModel):
    """A top-level container for a list of processed documents."""
    documents: List[Document] = Field(
        description="The list of documents identified, clustered, sequenced, and classified from all the input files."
    )