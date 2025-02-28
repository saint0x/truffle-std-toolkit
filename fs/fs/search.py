import os
import glob
from pathlib import Path
import truffle

class FileSearchTool:
    """Tool for finding and locating files in the filesystem."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()

    @truffle.tool(
        description="Find files in the specified directory based on pattern matching",
        icon="search"
    )
    @truffle.args(
        path="Directory path to search in",
        pattern="File pattern to match (e.g., *.py, *.txt)",
        recursive="Whether to search recursively in subdirectories"
    )
    def FindFiles(self, path: str, pattern: str, recursive: bool = True) -> dict:
        """Find files matching the specified pattern in the given directory."""
        search_path = os.path.expanduser(path)
        if not os.path.exists(search_path):
            return {"error": f"Path does not exist: {path}"}

        try:
            if recursive:
                search_pattern = os.path.join(search_path, "**", pattern)
                files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(search_path, pattern)
                files = glob.glob(search_pattern)

            return {
                "success": True,
                "files": [str(Path(f).resolve()) for f in files],
                "count": len(files)
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Search for files containing specific text content",
        icon="file-search"
    )
    @truffle.args(
        path="Directory path to search in",
        text="Text content to search for",
        file_pattern="Optional file pattern to filter (e.g., *.txt)",
        case_sensitive="Whether the search should be case-sensitive"
    )
    def FindContent(self, path: str, text: str, file_pattern: str = "*", case_sensitive: bool = False) -> dict:
        """Search for files containing specific text content."""
        matches = []
        search_path = os.path.expanduser(path)
        
        if not os.path.exists(search_path):
            return {"error": f"Path does not exist: {path}"}

        try:
            for root, _, files in os.walk(search_path):
                for file in files:
                    if not glob.fnmatch.fnmatch(file, file_pattern):
                        continue
                        
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if not case_sensitive:
                                if text.lower() in content.lower():
                                    matches.append(file_path)
                            else:
                                if text in content:
                                    matches.append(file_path)
                    except (UnicodeDecodeError, IOError):
                        continue  # Skip binary or unreadable files

            return {
                "success": True,
                "matches": [str(Path(f).resolve()) for f in matches],
                "count": len(matches)
            }
        except Exception as e:
            return {"error": str(e)} 