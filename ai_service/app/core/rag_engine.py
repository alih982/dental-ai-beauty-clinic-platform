# import logging
# from typing import List
# from pypdf import PdfReader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from sentence_transformers import SentenceTransformer
# from app.config import settings

# logger = logging.getLogger(__name__)

# class RagEngine:
#     """Core engine for document processing and embedding generation"""
    
#     def __init__(self):
#         logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL}")
#         self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=settings.CHUNK_SIZE,
#             chunk_overlap=settings.CHUNK_OVERLAP,
#             separators=["\n\n", "\n", ".", " ", ""]
#         )

#     def extract_text_from_pdf(self, pdf_path: str) -> str:
#         """Extract all text from a PDF file"""
#         try:
#             reader = PdfReader(pdf_path)
#             text = ""
#             for page in reader.pages:
#                 text += page.extract_text() + "\n"
#             return text
#         except Exception as e:
#             logger.error(f"Error extracting PDF text: {e}")
#             raise

#     def get_chunks(self, text: str) -> List[str]:
#         """Split text into chunks based on configuration"""
#         return self.text_splitter.split_text(text)

#     def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
#         """Generate vector embeddings for a list of texts"""
#         embeddings = self.model.encode(texts)
#         return embeddings.tolist()

#     def generate_single_embedding(self, text: str) -> List[float]:
#         """Generate a single vector embedding"""
#         return self.model.encode(text).tolist()

# rag_engine = RagEngine()
