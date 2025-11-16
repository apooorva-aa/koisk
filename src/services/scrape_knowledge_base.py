#!/usr/bin/env python3
"""Web scraping script for kiosk knowledge base.

This script scrapes security sources, processes content, and ingests it into
PostgreSQL with pgvector for RAG-based IAM policy analysis.
"""

import asyncio
import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from services.settings import get_settings
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from schemas.knowledge_base import DocumentMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common headers to use for requests
COMMON_HEADERS = {
    'User-Agent': (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

SOURCES = [
    {
        'url': 'https://iiitm.ac.in/',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/academics-final/academic-programs',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/component/content/category/97-admissions?Itemid=437',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/admissions-final/ms-admission',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://iiitm.ac.in/index.php/en/111-administration',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/administration/director-s-message',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://iiitm.ac.in/index.php/en/administration/history/1030-self-appraisal-form-rti-act-02-10-2023',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://iiitm.ac.in/index.php/en/119-location',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/academics-final/academic-programs#campus-life',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://iiitm.ac.in/index.php/en/administration/campus-life/overview#students-hostels',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/research-publications/88-books-published-by-abv-iiitm-gwalior-faculty',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/component/content/article/79-latest-news/574-rules-for-change-of-branch-abv-iiitm-gwalior',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://www.iiitm.ac.in/index.php/en/component/content/category/98-recruitment?Itemid=437',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
    {
        'url': 'https://iiitm.ac.in/index.php/en/166-faq-general',
        'headers': COMMON_HEADERS,
        'timeout': 30,
    },
]


class KnowledgeBaseScraper:
    """Scrapes web pages, creates embeddings, and stores them in PostgreSQL with pgvector."""

    def __init__(self):
        """Initialize the scraper with settings and models."""
        self.settings = get_settings()
        
        # Initialize text processing components
        self.embedding_model = SentenceTransformer(self.settings.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP,
        )
        
        # Initialize repository
        self.repository = KnowledgeBaseRepository()
        
        # Create scraped data directory
        self.scraped_data_dir = Path(self.settings.SCRAPED_DATA_DIR)
        self.scraped_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Knowledge Base Scraper initialized")

    async def scrape_and_ingest(self) -> Dict[str, int]:
        """Main function to scrape all sources and ingest their content."""
        logger.info(f"Starting scrape for {len(SOURCES)} sources...")
        
        # Initialize repository
        await self.repository.initialize()
        
        total_documents, total_chunks = 0, 0
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = [self._process_url(session, source['url'], source.get('headers', {}), source.get('timeout', 30)) 
                        for source in SOURCES]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Task failed: {result}")
                    elif isinstance(result, dict):
                        total_documents += result.get('documents', 0)
                        total_chunks += result.get('chunks', 0)
            
            logger.info(f"Scraping completed: {total_documents} documents, {total_chunks} chunks")
            return {
                "documents_processed": total_documents,
                "chunks_created": total_chunks,
                "sources": len(SOURCES)
            }
            
        finally:
            await self.repository.close()

    async def _process_url(self, session: aiohttp.ClientSession, url: str, headers: dict, timeout: int) -> Dict[str, int]:
        """Fetch, clean, chunk, extract metadata, save locally, and store in PostgreSQL."""
        try:
            logger.info(f"🔍 Starting to process URL: {url}")
            
            # Skip URLs that are commented out or empty
            if not url or url.startswith('#'):
                logger.info(f"⏭️  Skipping disabled URL: {url}")
                return {"documents": 0, "chunks": 0, "skipped": True}
            
            # Delete existing documents from this source first
            try:
                deleted_count = await self.repository.delete_documents_by_source(url)
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} existing documents for source: {url}")
            except Exception as e:
                logger.warning(f"Failed to delete existing documents for {url}: {str(e)}")
            
            # Add a small delay to avoid overwhelming the server
            await asyncio.sleep(1)
            
            # Fetch the URL content
            try:
                logger.info(f"Fetching content from: {url}")
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 403:
                        msg = f"Access forbidden (403) for {url}. The server may be blocking automated requests."
                        logger.warning(msg)
                        return {"documents": 0, "chunks": 0, "error": msg}
                    
                    if response.status == 404:
                        msg = f"Page not found (404) for {url}"
                        logger.warning(msg)
                        return {"documents": 0, "chunks": 0, "error": msg}
                    
                    if response.status >= 400:
                        msg = f"HTTP error {response.status} for {url}"
                        logger.warning(msg)
                        return {"documents": 0, "chunks": 0, "error": msg}
                    
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    if 'text/html' not in content_type and 'text/plain' not in content_type:
                        msg = f"Unsupported content type '{content_type}' for {url}"
                        logger.warning(msg)
                        return {"documents": 0, "chunks": 0, "error": msg}
                    
                    html = await response.text()
                    
            except aiohttp.ClientError as e:
                msg = f"Error fetching {url}: {str(e)}"
                logger.error(msg)
                return {"documents": 0, "chunks": 0, "error": msg}

            # Parse HTML and extract text content
            try:
                logger.info(f"Parsing content from: {url}")
                soup = BeautifulSoup(html, "html.parser")
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header", "iframe", "form", "button"]):
                    element.decompose()
                
                # Get clean text content
                full_content = soup.get_text(separator="\n", strip=True)
                
                if not full_content or len(full_content.strip()) < 100:  # Arbitrary minimum length
                    msg = f"Insufficient content found for {url} (length: {len(full_content) if full_content else 0} chars)"
                    logger.warning(msg)
                    return {"documents": 0, "chunks": 0, "error": msg}
                
                logger.info(f"Successfully extracted {len(full_content)} characters from {url}")
                
            except Exception as e:
                msg = f"Error parsing content from {url}: {str(e)}"
                logger.error(msg, exc_info=True)
                return {"documents": 0, "chunks": 0, "error": msg}

            # Extract metadata
            try:
                extracted_metadata = self._extract_metadata(url, full_content)
                logger.info(f"Extracted metadata for {url}")
            except Exception as e:
                msg = f"Error extracting metadata from {url}: {str(e)}"
                logger.error(msg, exc_info=True)
                return {"documents": 0, "chunks": 0, "error": msg}
            
            # Save to local markdown file
            try:
                self._save_to_markdown(extracted_metadata, full_content)
                logger.info(f"Saved content to local file for: {url}")
            except Exception as e:
                logger.warning(f"Failed to save content to local file for {url}: {str(e)}")

            # Process and ingest content
            chunks_created = await self._process_and_ingest_content(url, full_content, extracted_metadata)
            
            if chunks_created > 0:
                logger.info(f"Successfully processed {url}: {chunks_created} chunks created")
                return {"documents": 1, "chunks": chunks_created}
            else:
                msg = f"No chunks were created for {url}"
                logger.warning(msg)
                return {"documents": 0, "chunks": 0, "error": msg}

        except Exception as e:
            msg = f"Unexpected error processing {url}: {str(e)}"
            logger.error(msg, exc_info=True)
            return {"documents": 0, "chunks": 0, "error": msg}

    async def _process_and_ingest_content(
        self, 
        url: str, 
        content: str, 
        metadata: Dict[str, any]
    ) -> int:
        """Process content and ingest into PostgreSQL with pgvector."""
        try:
            logger.info(f"Processing content from {url} (length: {len(content)} chars)")
            
            # Ensure content is a non-empty string
            if not content or not isinstance(content, str):
                logger.warning(f"No valid content to process for {url}")
                return 0
                
            # Split content into chunks
            try:
                chunks = self.text_splitter.split_text(content)
                if not chunks:
                    logger.warning(f"Could not split content into chunks for {url}")
                    return 0
                logger.info(f"Split content into {len(chunks)} chunks for {url}")
            except Exception as e:
                logger.error(f"Error splitting text for {url}: {str(e)}")
                return 0

            # Generate embeddings
            try:
                embeddings = self.embedding_model.encode(chunks).tolist()
                if not embeddings or len(embeddings) != len(chunks):
                    logger.error(f"Failed to generate embeddings for {url}")
                    return 0
            except Exception as e:
                logger.error(f"Error generating embeddings for {url}: {str(e)}")
                return 0
            
            # Determine framework and category based on URL
            try:
                framework, category = self._categorize_source(url)
                title = self._extract_title(url)
                tags = self._extract_tags(url)
                rule_id = str(metadata.get('rule_id', hashlib.md5(url.encode()).hexdigest()[:8]))
                
                # Ensure all values are strings or convert them to strings
                if not isinstance(rule_id, str):
                    rule_id = str(rule_id)
                if not isinstance(framework, str):
                    framework = str(framework) if framework is not None else "unknown"
                if not isinstance(category, str):
                    category = str(category) if category is not None else "general"
                if not isinstance(title, str):
                    title = title if isinstance(title, str) else ""
                if not isinstance(tags, list):
                    tags = []
                
                # Clean up tags to ensure they're all strings
                tags = [str(tag) for tag in tags if tag]
                
                # Log the prepared metadata for debugging
                logger.debug(f"Prepared metadata for {url}: {metadata}")
                
            except Exception as e:
                logger.error(f"Error preparing metadata for {url}: {str(e)}", exc_info=True)
                return 0
            
            # Ingest each chunk into PostgreSQL
            chunks_ingested = 0
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    # Create a clean metadata dictionary with only the expected fields
                    document_metadata = {
                        'source': str(url),  # Ensure source is a string
                        'rule_id': rule_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'title': title,
                        'category': category,
                        'framework': framework,
                        'tags': tags,
                        'language': 'en',  # Default language
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Log the document metadata before creating DocumentMetadata
                    logger.debug(f"Creating document metadata for chunk {i}: {document_metadata}")
                    
                    # Create DocumentMetadata object with the clean metadata
                    doc_metadata = DocumentMetadata(**document_metadata)
                    
                    # Log the document metadata after creating DocumentMetadata
                    logger.debug(f"Created DocumentMetadata: {doc_metadata.dict()}")
                    
                    # Ensure the embedding is a list of floats
                    if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
                        logger.error(f"Invalid embedding format for chunk {i} from {url}")
                        continue
                        
                    # Log the embedding dimensions for debugging
                    logger.debug(f"Embedding dimensions for chunk {i}: {len(embedding) if embedding else 0}")
                    
                    await self.repository.create_document(
                        content=chunk,
                        metadata=doc_metadata,
                        embedding=embedding
                    )
                    chunks_ingested += 1
                    logger.debug(f"Successfully ingested chunk {i} from {url}")
                    
                except Exception as e:
                    logger.error(f"Error ingesting chunk {i} from {url}: {str(e)}", exc_info=True)
                    continue  # Try to continue with remaining chunks
            
            if chunks_ingested > 0:
                logger.info(f"Successfully ingested {chunks_ingested}/{len(chunks)} chunks from {url} into PostgreSQL")
            else:
                logger.error(f"Failed to ingest any chunks from {url}")
                
            return chunks_ingested
            
        except Exception as e:
            logger.error(f"Unexpected error processing content from {url}: {str(e)}", exc_info=True)
            return 0

    def _extract_metadata(self, url: str, content: str) -> Dict[str, any]:
        """Extract structured metadata tailored for campus kiosk."""
        parsed_url = urlparse(url)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        # Default values
        category = "general"
        subcategory = "general"
        source_type = "web"
        framework, source_category = self._categorize_source(url)

        # Title extraction
        title = (
            self._extract_title_from_content(content)
            or self._sanitize_filename(path_parts[-1] if path_parts else url)
        )
        item_id = hashlib.md5(url.encode()).hexdigest()
        content_lower = content.lower()
        now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

        # Subcategory based on content (campus-specific)
        if any(k in content_lower for k in ["history", "founder", "established"]):
            subcategory = "history"
        elif any(k in content_lower for k in ["courses", "programs", "curriculum"]):
            subcategory = "academics"
        elif any(k in content_lower for k in ["library", "books", "lrc"]):
            subcategory = "library"
        elif any(k in content_lower for k in ["sports", "gym", "stadium", "court"]):
            subcategory = "sports"
        elif any(k in content_lower for k in ["canteen", "food", "cafeteria"]):
            subcategory = "dining"
        elif any(k in content_lower for k in ["hostel", "accommodation", "dorm"]):
            subcategory = "hostels"
        elif any(k in content_lower for k in ["event", "festival", "cultural", "exhibit", "museum"]):
            subcategory = "events_culture"
        elif any(k in content_lower for k in ["admission", "apply", "brochure", "eligibility"]):
            subcategory = "admissions"
        elif any(k in content_lower for k in ["research", "publication", "papers"]):
            subcategory = "research"

        # Tags extraction (enhanced for campus kiosk)
        tags = self._extract_tags(url)
        if any(k in content_lower for k in ["heritage", "ancient", "monument"]):
            tags.append("heritage")
        if any(k in content_lower for k in ["student", "faculty", "education", "learning"]):
            tags.append("education")
        if any(k in content_lower for k in ["sports", "fitness", "game", "gym"]):
            tags.append("sports")
        if any(k in content_lower for k in ["food", "canteen", "cafeteria", "dining"]):
            tags.append("food")
        if any(k in content_lower for k in ["art", "gallery", "exhibit", "museum"]):
            tags.append("culture")
        if any(k in content_lower for k in ["hostel", "accommodation", "dorm"]):
            tags.append("hostel")
        if any(k in content_lower for k in ["event", "festival", "cultural"]):
            tags.append("events")
        if any(k in content_lower for k in ["admission", "apply", "eligibility"]):
            tags.append("admissions")
        if any(k in content_lower for k in ["research", "publication", "papers"]):
            tags.append("research")
        
        tags = list(set(tags)) or ["general"]

        # Summary and extra_info sections for kiosk display
        summary = (
            self._extract_section(content, ["summary", "overview", "about"])
            or "No explicit summary available."
        )

        extra_info = (
            self._extract_section(content, ["details", "information", "description"])
            or "No detailed description provided."
        )

        return {
            "id": item_id,
            "title": title,
            "content": content,
            "source_url": url,
            "source_type": source_type,
            "source_category": source_category,
            "category": category,
            "subcategory": subcategory,
            "tags": tags,
            "summary": summary,
            "extra_info": extra_info,
            "vector_id": hashlib.md5(f"{item_id}_vector".encode()).hexdigest(),
            "created_at": now_utc,
            "updated_at": now_utc,
        }

    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract a title from the first heading in content."""
        match = re.search(r'^\s*#+\s*(.+)', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped and len(stripped) > 20 and not stripped.startswith(('---', '***', '===', '---')):
                return stripped
        return None

    def _extract_section(self, content: str, keywords: List[str]) -> Optional[str]:
        """Extract content from a section identified by keywords."""
        keywords_pattern = "|".join(re.escape(k) for k in keywords)
        pattern = rf"(?:^|\n)##+\s*(?:{keywords_pattern}[^\n]*)\s*\n(.*?)(?=\n##+|$)"
        
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be a valid filename."""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename[:200]

    def _save_to_markdown(self, metadata: Dict[str, any], full_content: str):
        """Save the scraped data and metadata to a structured markdown file."""
        save_path = self.scraped_data_dir / metadata.get('category', 'general') / metadata.get('subcategory', 'general')
        save_path.mkdir(parents=True, exist_ok=True)
        
        filename_base = metadata.get('title') or metadata.get('id', 'unknown')
        rule_name_sanitized = self._sanitize_filename(filename_base)
        file_name = f"{rule_name_sanitized}.md"
        file_path = save_path / file_name

        kiosk_metadata_keys = [
            "id", "title", "source_url", "source_type", "source_category",
            "category", "subcategory", "tags", "summary", "extra_info",
            "vector_id", "created_at", "updated_at"
        ]
        front_matter_metadata = {k: str(metadata.get(k, "")) for k in kiosk_metadata_keys}

        full_content_for_md = full_content

        front_matter = "---\n"
        for key, value in front_matter_metadata.items():
            front_matter += f"{key}: {value}\n"
        front_matter += "---\n\n"

        md_content = f"{front_matter}# {metadata.get('title', metadata.get('id', 'Unknown'))}\n\n{full_content_for_md}"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Saved structured markdown to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save markdown file {file_path}: {e}", exc_info=True)

    def _categorize_source(self, url: str) -> tuple[str, str]:
        """Categorize a source URL into framework and category.
        
        Args:
            url: The URL to categorize
            
        Returns:
            A tuple of (framework, category) as strings
        """
        url_lower = url.lower()
        
        # Departments
        if any(x in url_lower for x in ["engineering", "cse", "computer-science"]):
            return "Campus", "Academic Department"
        if any(x in url_lower for x in ["management", "commerce"]):
            return "Campus", "Business & Management"

        # Facilities
        if any(x in url_lower for x in ["library", "learning-resource-centre", "lrc"]):
            return "Campus", "Library & Learning Resources"
        if any(x in url_lower for x in ["sports", "gym", "stadium", "court"]):
            return "Campus", "Sports Facilities"
        if any(x in url_lower for x in ["canteen", "food", "cafeteria"]):
            return "Campus", "Food & Beverages"
        if any(x in url_lower for x in ["hostel", "accommodation", "dorm"]):
            return "Campus", "Accommodation"

        # Events
        if any(x in url_lower for x in ["event", "festival", "cultural"]):
            return "Campus", "Events & Culture"

        # Admissions
        if any(x in url_lower for x in ["admission", "apply", "brochure"]):
            return "Campus", "Admissions"

        # Fallback
        return "Campus", "General Information"

    def _extract_title(self, url: str) -> str:
        """
        Friendly and meaningful titles for kiosk content.
        No IAM-specific rules.
        """
        url_lower = url.lower()

        # Departments
        if any(x in url_lower for x in ["engineering", "cse", "computer-science"]):
            return "Department of Engineering Sciences"
        if any(x in url_lower for x in ["management", "commerce"]):
            return "School of Management & Commerce"

        # Facilities
        if any(x in url_lower for x in ["library", "lrc"]):
            return "Library & Learning Resource Centre"
        if any(x in url_lower for x in ["sports", "gym", "stadium", "court"]):
            return "Campus Sports & Recreation Facilities"
        if any(x in url_lower for x in ["canteen", "food", "cafeteria"]):
            return "Campus Dining & Canteen Services"
        if any(x in url_lower for x in ["hostel", "accommodation", "dorm"]):
            return "Student Hostels & Accommodation"

        # Cultural / Museum / Events
        if any(x in url_lower for x in ["museum", "gallery", "exhibit"]):
            return "Campus Museum & Exhibits"
        if any(x in url_lower for x in ["event", "festival", "cultural"]):
            return "Campus Events & Cultural Activities"

        # Admissions
        if any(x in url_lower for x in ["admission", "apply", "brochure"]):
            return "Admissions & Application Information"

        # Fallback (use URL path)
        try:
            domain = url.split('//')[-1].split('/')[0]
            path_parts = [p for p in url.split('/')[3:] if p]
            if path_parts:
                title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                return f"{title} - {domain}"
            return f"Information from {domain}"
        except:
            return url

    def _extract_tags(self, url: str) -> List[str]:
        """Generate semantic tags for campus kiosk content."""
        url_lower = url.lower()
        tags = []

        tag_map = {
            # Departments
            "engineering": "engineering",
            "cse": "cse",
            "computer-science": "cse",
            "management": "management",
            "commerce": "commerce",

            # Facilities
            "library": "library",
            "lrc": "library",
            "sports": "sports",
            "gym": "sports",
            "stadium": "sports",
            "court": "sports",
            "canteen": "food",
            "food": "food",
            "cafeteria": "food",
            "hostel": "hostel",
            "accommodation": "hostel",
            "dorm": "hostel",

            # events
            "event": "events",
            "festival": "events",
            "cultural": "events",

            # Admissions
            "admission": "admissions",
            "apply": "admissions",
            "brochure": "admissions",

            # Research
            "research": "research",
            "publication": "research",
            "papers": "research",
            "books": "research",
        }

        for key, tag in tag_map.items():
            if key in url_lower:
                tags.append(tag)

        return list(set(tags)) or ["general"]


async def get_scraping_results() -> dict:
    """Run the scraper and return results as a clean dictionary."""
    scraper = KnowledgeBaseScraper()
    try:
        results = await scraper.scrape_and_ingest()
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **results
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "error_type": e.__class__.__name__
        }

async def main():
    """Main function to run the scraper with console output."""
    # Configure console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    try:
        # Get results
        results = await get_scraping_results()
        
        # Log the results
        if results["status"] == "success":
            logger.info(f"Scraping completed successfully: {results}")
        else:
            logger.error(f"Scraping failed: {results}")
        
        # Print results as JSON to stdout (for the parent process)
        print(json.dumps(results, indent=2))
        
        # Exit with appropriate status code
        sys.exit(0 if results["status"] == "success" else 1)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "error_type": e.__class__.__name__
        }
        logger.error("Unexpected error in main:", exc_info=True)
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
