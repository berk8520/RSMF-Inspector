import os
import shutil
import tempfile

class TempCacheService:
    """
    Manages temporary attachment and thumbnail directories.
    Automatically purges all temporary files upon opening a new RSMF container or closing the app.
    """
    
    @staticmethod
    def get_extracted_dir() -> str:
        temp_dir = os.path.join(tempfile.gettempdir(), "RSMF_Inspector_Extracted")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @staticmethod
    def get_thumbnails_dir() -> str:
        thumb_dir = os.path.join(tempfile.gettempdir(), "RSMF_Inspector_Thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)
        return thumb_dir

    @staticmethod
    def clear_cache():
        """Deletes all extracted attachment files and generated thumbnails from temp storage."""
        for target_dir in (TempCacheService.get_extracted_dir(), TempCacheService.get_thumbnails_dir()):
            if os.path.exists(target_dir):
                for filename in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception:
                        pass
