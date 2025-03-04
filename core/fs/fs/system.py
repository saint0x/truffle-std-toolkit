import os
import shutil
import subprocess
from typing import Optional
import truffle

class FileSystemTool:
    """Tool for basic filesystem operations."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()
        self._sudo_password = None

    def _request_sudo(self) -> str:
        """Request sudo password from user if not already stored."""
        if not self._sudo_password:
            self._sudo_password = getpass.getpass("Enter sudo password: ")
        return self._sudo_password

    def _run_sudo_command(self, command: list) -> tuple:
        """Run a command with sudo privileges."""
        sudo_password = self._request_sudo()
        process = subprocess.Popen(
            ['sudo', '-S'] + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate(input=sudo_password + '\n')
        return process.returncode, stdout, stderr

    @truffle.tool(
        description="Create a new directory",
        icon="folder-plus"
    )
    @truffle.args(
        path="Directory path to create",
        mode="Directory permissions in octal format (e.g., 0755)",
        require_sudo="Whether sudo privileges are required",
        parents="Create parent directories if they don't exist"
    )
    def CreateDirectory(self, path: str, mode: int = 0o755, require_sudo: bool = False, parents: bool = True) -> dict:
        """Create a new directory with specified permissions."""
        path = os.path.expanduser(path)
        
        try:
            if require_sudo:
                # Create directory with sudo
                command = ['mkdir']
                if parents:
                    command.append('-p')
                command.append(path)
                returncode, stdout, stderr = self._run_sudo_command(command)
                
                if returncode != 0:
                    return {"error": f"Failed to create directory: {stderr}"}
                    
                # Set permissions with sudo
                mode_str = oct(mode)[-4:]  # Get last 4 digits of octal representation
                self._run_sudo_command(['chmod', mode_str, path])
            else:
                os.makedirs(path, mode=mode, exist_ok=parents)
            
            return {
                "success": True,
                "path": path,
                "mode": oct(mode)[-4:]
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Copy files or directories",
        icon="copy"
    )
    @truffle.args(
        source="Source path",
        destination="Destination path",
        require_sudo="Whether sudo privileges are required"
    )
    def Copy(self, source: str, destination: str, require_sudo: bool = False) -> dict:
        """Copy a file or directory to a new location."""
        source = os.path.expanduser(source)
        destination = os.path.expanduser(destination)

        if not os.path.exists(source):
            return {"error": f"Source path does not exist: {source}"}

        try:
            if require_sudo:
                command = ['cp', '-r' if os.path.isdir(source) else '', source, destination]
                returncode, stdout, stderr = self._run_sudo_command(command)
                if returncode != 0:
                    return {"error": f"Failed to copy: {stderr}"}
            else:
                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)

            return {
                "success": True,
                "source": source,
                "destination": destination
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Move or rename files or directories",
        icon="move"
    )
    @truffle.args(
        source="Source path",
        destination="Destination path",
        require_sudo="Whether sudo privileges are required"
    )
    def Move(self, source: str, destination: str, require_sudo: bool = False) -> dict:
        """Move a file or directory to a new location."""
        source = os.path.expanduser(source)
        destination = os.path.expanduser(destination)

        if not os.path.exists(source):
            return {"error": f"Source path does not exist: {source}"}

        try:
            if require_sudo:
                command = ['mv', source, destination]
                returncode, stdout, stderr = self._run_sudo_command(command)
                if returncode != 0:
                    return {"error": f"Failed to move: {stderr}"}
            else:
                shutil.move(source, destination)

            return {
                "success": True,
                "source": source,
                "destination": destination
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Delete files or directories",
        icon="trash"
    )
    @truffle.args(
        path="Path to delete",
        recursive="Whether to recursively delete directories",
        require_sudo="Whether sudo privileges are required",
        force="Whether to ignore nonexistent files and never prompt"
    )
    def Delete(self, path: str, recursive: bool = False, require_sudo: bool = False, force: bool = False) -> dict:
        """Delete a file or directory."""
        path = os.path.expanduser(path)

        if not os.path.exists(path) and not force:
            return {"error": f"Path does not exist: {path}"}

        try:
            if require_sudo:
                command = ['rm']
                if recursive:
                    command.append('-r')
                if force:
                    command.append('-f')
                command.append(path)
                
                returncode, stdout, stderr = self._run_sudo_command(command)
                if returncode != 0:
                    return {"error": f"Failed to delete: {stderr}"}
            else:
                if os.path.isfile(path) or (not recursive and os.path.islink(path)):
                    os.remove(path)
                elif recursive and os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)

            return {
                "success": True,
                "path": path
            }
        except Exception as e:
            return {"error": str(e)} 