import os
import json
import codecs
from typing import Union, Optional
import truffle

class FileContentTool:
    """Tool for reading, writing, and manipulating file contents."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()

    @truffle.tool(
        description="Read the contents of a file",
        icon="file-text"
    )
    @truffle.args(
        path="Path to the file to read",
        encoding="File encoding (default: utf-8)",
        start_line="Optional start line number (1-based)",
        end_line="Optional end line number (1-based)"
    )
    def ReadFile(self, path: str, encoding: str = "utf-8", start_line: Optional[int] = None, end_line: Optional[int] = None) -> dict:
        """Read the contents of a file with optional line range."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        if not os.path.isfile(path):
            return {"error": f"Path is not a file: {path}"}

        try:
            with codecs.open(path, 'r', encoding=encoding) as f:
                if start_line is None and end_line is None:
                    content = f.read()
                    return {
                        "success": True,
                        "content": content,
                        "encoding": encoding
                    }
                else:
                    lines = f.readlines()
                    start_idx = (start_line or 1) - 1
                    end_idx = end_line if end_line is None else end_line - 1
                    selected_lines = lines[start_idx:end_idx]
                    return {
                        "success": True,
                        "content": "".join(selected_lines),
                        "encoding": encoding,
                        "start_line": start_line or 1,
                        "end_line": end_line or len(lines),
                        "total_lines": len(lines)
                    }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Write content to a file",
        icon="file-plus"
    )
    @truffle.args(
        path="Path to the file to write",
        content="Content to write to the file",
        encoding="File encoding (default: utf-8)",
        append="Whether to append to the file instead of overwriting"
    )
    def WriteFile(self, path: str, content: Union[str, dict, list], encoding: str = "utf-8", append: bool = False) -> dict:
        """Write or append content to a file."""
        path = os.path.expanduser(path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        try:
            mode = 'a' if append else 'w'
            
            # Handle JSON content
            if isinstance(content, (dict, list)):
                with codecs.open(path, mode, encoding=encoding) as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                with codecs.open(path, mode, encoding=encoding) as f:
                    f.write(str(content))

            return {
                "success": True,
                "path": path,
                "mode": "append" if append else "write",
                "encoding": encoding
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Replace text in a file",
        icon="edit"
    )
    @truffle.args(
        path="Path to the file",
        old_text="Text to replace",
        new_text="Replacement text",
        encoding="File encoding (default: utf-8)",
        count="Maximum number of replacements (default: -1 for all)"
    )
    def ReplaceInFile(self, path: str, old_text: str, new_text: str, encoding: str = "utf-8", count: int = -1) -> dict:
        """Replace text in a file with new text."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        if not os.path.isfile(path):
            return {"error": f"Path is not a file: {path}"}

        try:
            with codecs.open(path, 'r', encoding=encoding) as f:
                content = f.read()

            new_content, num_replacements = content.replace(old_text, new_text, count), 0
            if count == -1:
                num_replacements = content.count(old_text)
            else:
                num_replacements = min(content.count(old_text), count)

            if num_replacements > 0:
                with codecs.open(path, 'w', encoding=encoding) as f:
                    f.write(new_content)

            return {
                "success": True,
                "path": path,
                "replacements_made": num_replacements,
                "encoding": encoding
            }
        except Exception as e:
            return {"error": str(e)} 