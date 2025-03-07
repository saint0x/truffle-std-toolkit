import os
import re
import subprocess
from typing import List, Optional, Dict, Union
import truffle

class GrepTool:
    """Tool for advanced code and text searching capabilities."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()

    @truffle.tool(
        description="Search for pattern in files using regular expressions",
        icon="search-code"
    )
    @truffle.args(
        pattern="Regular expression pattern to search for",
        path="Directory or file path to search in",
        file_pattern="File pattern to include (e.g., *.py, *.{js,ts})",
        ignore_case="Whether to perform case-insensitive search",
        recursive="Whether to search recursively in subdirectories",
        context_lines="Number of context lines to include before and after matches"
    )
    def Search(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        ignore_case: bool = False,
        recursive: bool = True,
        context_lines: int = 0
    ) -> Dict[str, Union[bool, List[Dict[str, Union[str, int]]]]]:
        """
        Search for a regex pattern in files, with support for context lines and file filtering.
        Returns matches with line numbers and context.
        """
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        try:
            # Build ripgrep command for efficient searching
            cmd = ["rg", "--json"]  # Use JSON output for structured parsing
            
            if ignore_case:
                cmd.append("-i")
            if recursive and os.path.isdir(path):
                cmd.append("--follow")  # Follow symbolic links
            if context_lines > 0:
                cmd.extend(["-C", str(context_lines)])
            
            # Add file pattern
            if file_pattern != "*":
                cmd.extend(["-g", file_pattern])

            # Add pattern and path
            cmd.extend([pattern, path])

            # Run the search
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode not in [0, 1]:  # 1 means no matches, which is ok
                return {"error": f"Search failed: {stderr}"}

            # Parse the JSON output
            matches = []
            current_file = None
            current_matches = []

            for line in stdout.splitlines():
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    if data["type"] == "begin":
                        if current_file and current_matches:
                            matches.append({
                                "file": current_file,
                                "matches": current_matches
                            })
                        current_file = data["data"]["path"]["text"]
                        current_matches = []
                    elif data["type"] == "match":
                        match_data = data["data"]
                        current_matches.append({
                            "line_number": match_data["line_number"],
                            "content": match_data["lines"]["text"],
                            "submatches": [{
                                "start": m["start"],
                                "end": m["end"],
                                "match": m["text"]
                            } for m in match_data["submatches"]]
                        })
                except json.JSONDecodeError:
                    continue

            # Add the last file's matches
            if current_file and current_matches:
                matches.append({
                    "file": current_file,
                    "matches": current_matches
                })

            return {
                "success": True,
                "matches": matches,
                "total_files": len(matches),
                "total_matches": sum(len(m["matches"]) for m in matches)
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Find function definitions and declarations in code files",
        icon="code"
    )
    @truffle.args(
        name="Function name to search for (supports regex)",
        path="Directory or file path to search in",
        language="Programming language to search in (e.g., python, javascript)",
        exact_match="Whether to require exact name matches"
    )
    def FindFunction(
        self,
        name: str,
        path: str = ".",
        language: Optional[str] = None,
        exact_match: bool = False
    ) -> Dict[str, Union[bool, List[Dict[str, Union[str, int]]]]]:
        """
        Find function definitions and declarations in code files.
        Supports multiple programming languages and uses language-specific patterns.
        """
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        # Language-specific patterns for function definitions
        patterns = {
            "python": rf"def\s+{name}\s*\(",
            "javascript": rf"(function\s+{name}|const\s+{name}\s*=\s*(?:async\s*)?function|\({name}\)\s*=>)",
            "typescript": rf"(function\s+{name}|const\s+{name}\s*=\s*(?:async\s*)?function|\({name}\)\s*=>|{name}\s*:\s*Function)",
            "java": rf"(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+{name}\s*\(",
            "cpp": rf"[\w\<\>\[\]]+\s+{name}\s*\(",
            "go": rf"func\s+{name}\s*\(",
            "rust": rf"fn\s+{name}\s*\(",
            "ruby": rf"def\s+{name}",
        }

        try:
            # Determine file pattern and search pattern based on language
            if language:
                language = language.lower()
                if language not in patterns:
                    return {"error": f"Unsupported language: {language}"}
                    
                file_patterns = {
                    "python": "*.py",
                    "javascript": "*.{js,jsx}",
                    "typescript": "*.{ts,tsx}",
                    "java": "*.java",
                    "cpp": "*.{cpp,hpp,h}",
                    "go": "*.go",
                    "rust": "*.rs",
                    "ruby": "*.rb"
                }
                
                pattern = patterns[language]
                file_pattern = file_patterns[language]
            else:
                # If no language specified, search in all supported file types
                pattern = "|".join(f"({p})" for p in patterns.values())
                file_pattern = "*.{" + ",".join(["py", "js", "jsx", "ts", "tsx", "java", "cpp", "hpp", "h", "go", "rs", "rb"]) + "}"

            # Use the Search tool with appropriate parameters
            return self.Search(
                pattern=pattern if exact_match else pattern.replace(name, rf"\w*{name}\w*"),
                path=path,
                file_pattern=file_pattern,
                recursive=True,
                context_lines=2  # Include surrounding context for better understanding
            )
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Find class definitions in code files",
        icon="box"
    )
    @truffle.args(
        name="Class name to search for (supports regex)",
        path="Directory or file path to search in",
        language="Programming language to search in (e.g., python, javascript)",
        include_methods="Whether to include method definitions in results",
        exact_match="Whether to require exact name matches"
    )
    def FindClass(
        self,
        name: str,
        path: str = ".",
        language: Optional[str] = None,
        include_methods: bool = True,
        exact_match: bool = False
    ) -> Dict[str, Union[bool, List[Dict[str, Union[str, int]]]]]:
        """
        Find class definitions in code files.
        Optionally includes method definitions and supports multiple programming languages.
        """
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        # Language-specific patterns for class definitions
        patterns = {
            "python": rf"class\s+{name}(?:\s*\([^)]*\))?:",
            "javascript": rf"class\s+{name}(?:\s+extends\s+[A-Za-z_][A-Za-z0-9_]*)?",
            "typescript": rf"(?:export\s+)?class\s+{name}(?:\s+extends\s+[A-Za-z_][A-Za-z0-9_]*)?(?:\s+implements\s+[A-Za-z_][A-Za-z0-9_]*)?",
            "java": rf"(?:public|private|protected|static|\s)+class\s+{name}(?:\s+extends\s+[A-Za-z_][A-Za-z0-9_]*)?(?:\s+implements\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)?",
            "cpp": rf"class\s+{name}(?:\s*:\s*(?:public|private|protected)\s+[A-Za-z_][A-Za-z0-9_]*)?",
        }

        try:
            # Determine file pattern and search pattern based on language
            if language:
                language = language.lower()
                if language not in patterns:
                    return {"error": f"Unsupported language: {language}"}
                    
                file_patterns = {
                    "python": "*.py",
                    "javascript": "*.{js,jsx}",
                    "typescript": "*.{ts,tsx}",
                    "java": "*.java",
                    "cpp": "*.{cpp,hpp,h}",
                }
                
                pattern = patterns[language]
                file_pattern = file_patterns[language]
            else:
                # If no language specified, search in all supported file types
                pattern = "|".join(f"({p})" for p in patterns.values())
                file_pattern = "*.{" + ",".join(["py", "js", "jsx", "ts", "tsx", "java", "cpp", "hpp", "h"]) + "}"

            # Search for class definitions
            results = self.Search(
                pattern=pattern if exact_match else pattern.replace(name, rf"\w*{name}\w*"),
                path=path,
                file_pattern=file_pattern,
                recursive=True,
                context_lines=2 if include_methods else 0
            )

            if not results.get("success", False):
                return results

            # If including methods, search for method definitions within class blocks
            if include_methods and results["matches"]:
                # This is a simplified approach; for more accurate results,
                # you'd need to parse the code with a language-specific parser
                for file_match in results["matches"]:
                    file_path = file_match["file"]
                    
                    # Read the entire file to analyze class structure
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    for match in file_match["matches"]:
                        class_line = match["line_number"]
                        
                        # Simple indentation-based method detection for Python
                        # For other languages, you'd need more sophisticated parsing
                        if language == "python":
                            method_lines = []
                            i = class_line
                            class_indent = len(lines[i]) - len(lines[i].lstrip())
                            while i < len(lines):
                                line = lines[i]
                                if line.strip() and len(line) - len(line.lstrip()) > class_indent:
                                    if re.match(r'\s*def\s+', line):
                                        method_lines.append({
                                            "line_number": i + 1,
                                            "content": line.rstrip(),
                                        })
                                elif line.strip() and len(line) - len(line.lstrip()) <= class_indent:
                                    break
                                i += 1
                            if method_lines:
                                match["methods"] = method_lines

            return results
        except Exception as e:
            return {"error": str(e)} 