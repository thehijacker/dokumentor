import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.config import config
from backend.document_processor import DocumentProcessor
import logging

logger = logging.getLogger(__name__)


class DocumentWatcher(FileSystemEventHandler):
    """Watch folder for new documents"""
    
    def __init__(self, processor: DocumentProcessor, user_id: int = 1):
        self.processor = processor
        self.user_id = user_id
        self.processing = set()
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if file is supported
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.docx']:
            logger.info(f"Ignoring unsupported file: {file_path}")
            return
        
        # Avoid processing the same file multiple times
        if file_path in self.processing:
            return
        
        self.processing.add(file_path)
        
        # Wait a bit to ensure file is fully written
        time.sleep(2)
        
        try:
            logger.info(f"Processing new file: {file_path}")
            result = self.processor.process_file(file_path, self.user_id)
            
            if result['success']:
                logger.info(f"Successfully processed: {file_path}")
                
                # Handle post-processing
                if config.get('watch_folder.delete_after_processing', False):
                    os.remove(file_path)
                    logger.info(f"Deleted processed file: {file_path}")
                elif config.get('watch_folder.move_to_archive', False):
                    archive_dir = os.path.join(
                        os.path.dirname(file_path),
                        'archive'
                    )
                    os.makedirs(archive_dir, exist_ok=True)
                    archive_path = os.path.join(archive_dir, os.path.basename(file_path))
                    os.rename(file_path, archive_path)
                    logger.info(f"Moved to archive: {archive_path}")
            else:
                logger.error(f"Failed to process: {file_path} - {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
        
        finally:
            self.processing.discard(file_path)


class WatchFolderService:
    """Service to monitor watch folder"""
    
    def __init__(self):
        self.observer = None
        self.watch_folder = config.get('storage.watch_folder', './watch_folder')
        self.enabled = config.get('watch_folder.enabled', True)
    
    def start(self, processor: DocumentProcessor, user_id: int = 1):
        """Start watching folder"""
        if not self.enabled:
            logger.info("Watch folder is disabled")
            return
        
        # Create watch folder if it doesn't exist
        os.makedirs(self.watch_folder, exist_ok=True)
        
        # Create observer
        event_handler = DocumentWatcher(processor, user_id)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_folder, recursive=False)
        self.observer.start()
        
        logger.info(f"Started watching folder: {self.watch_folder}")
    
    def stop(self):
        """Stop watching folder"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching folder")
