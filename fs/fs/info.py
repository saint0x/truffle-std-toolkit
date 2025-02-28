import os
import stat
import pwd
import grp
from datetime import datetime
import truffle

class FileInfoTool:
    """Tool for retrieving detailed file and directory information."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()

    @truffle.tool(
        description="Get detailed information about a file or directory",
        icon="info"
    )
    @truffle.args(
        path="Path to the file or directory"
    )
    def GetInfo(self, path: str) -> dict:
        """Get detailed information about a file or directory including permissions, size, etc."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        try:
            stat_info = os.stat(path)
            
            # Get owner and group names
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except KeyError:
                owner = str(stat_info.st_uid)
                
            try:
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except KeyError:
                group = str(stat_info.st_gid)

            info = {
                "success": True,
                "path": path,
                "size": stat_info.st_size,
                "size_human": self._format_size(stat_info.st_size),
                "permissions": {
                    "mode_octal": oct(stat_info.st_mode)[-4:],
                    "mode_human": stat.filemode(stat_info.st_mode),
                    "readable": os.access(path, os.R_OK),
                    "writable": os.access(path, os.W_OK),
                    "executable": os.access(path, os.X_OK)
                },
                "owner": owner,
                "group": group,
                "type": {
                    "is_file": os.path.isfile(path),
                    "is_dir": os.path.isdir(path),
                    "is_link": os.path.islink(path),
                    "is_mount": os.path.ismount(path)
                },
                "timestamps": {
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                    "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                }
            }

            # Add link target if it's a symlink
            if os.path.islink(path):
                info["link_target"] = os.path.realpath(path)

            return info
        except Exception as e:
            return {"error": str(e)}

    def _format_size(self, size: int) -> str:
        """Convert size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"

    @truffle.tool(
        description="Get disk usage information for a directory",
        icon="hard-drive"
    )
    @truffle.args(
        path="Path to the directory",
        summarize="Whether to only show the total"
    )
    def GetDiskUsage(self, path: str, summarize: bool = False) -> dict:
        """Get disk usage information for a directory."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            details = []

            for root, dirs, files in os.walk(path):
                dir_count += len(dirs)
                file_count += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        if not summarize:
                            details.append({
                                "path": file_path,
                                "size": size,
                                "size_human": self._format_size(size)
                            })
                    except (OSError, IOError):
                        continue

            result = {
                "success": True,
                "total_size": total_size,
                "total_size_human": self._format_size(total_size),
                "file_count": file_count,
                "directory_count": dir_count
            }

            if not summarize:
                result["details"] = details

            return result
        except Exception as e:
            return {"error": str(e)} 