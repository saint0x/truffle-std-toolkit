import os
import stat
import pwd
import grp
import subprocess
import truffle

class FilePermissionsTool:
    """Tool for managing file and directory permissions."""
    
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
        description="Change file or directory permissions",
        icon="lock"
    )
    @truffle.args(
        path="Path to the file or directory",
        mode="Permissions in octal format (e.g., 0755)",
        recursive="Whether to apply recursively to directories",
        require_sudo="Whether sudo privileges are required"
    )
    def Chmod(self, path: str, mode: int, recursive: bool = False, require_sudo: bool = False) -> dict:
        """Change the permissions of a file or directory."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        try:
            mode_str = oct(mode)[-4:]  # Get last 4 digits of octal representation
            
            if require_sudo:
                command = ['chmod']
                if recursive and os.path.isdir(path):
                    command.append('-R')
                command.extend([mode_str, path])
                
                returncode, stdout, stderr = self._run_sudo_command(command)
                if returncode != 0:
                    return {"error": f"Failed to change permissions: {stderr}"}
            else:
                if recursive and os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        os.chmod(root, mode)
                        for item in dirs + files:
                            os.chmod(os.path.join(root, item), mode)
                else:
                    os.chmod(path, mode)

            return {
                "success": True,
                "path": path,
                "mode": mode_str,
                "recursive": recursive
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Change file or directory owner",
        icon="user"
    )
    @truffle.args(
        path="Path to the file or directory",
        user="Username or UID of the new owner",
        group="Group name or GID of the new group (optional)",
        recursive="Whether to apply recursively to directories",
        require_sudo="Whether sudo privileges are required"
    )
    def Chown(self, path: str, user: str, group: str = None, recursive: bool = False, require_sudo: bool = True) -> dict:
        """Change the owner and/or group of a file or directory."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        try:
            # Convert username/group to uid/gid if necessary
            try:
                uid = int(user)
            except ValueError:
                try:
                    uid = pwd.getpwnam(user).pw_uid
                except KeyError:
                    return {"error": f"User not found: {user}"}

            if group:
                try:
                    gid = int(group)
                except ValueError:
                    try:
                        gid = grp.getgrnam(group).gr_gid
                    except KeyError:
                        return {"error": f"Group not found: {group}"}
            else:
                gid = -1

            if require_sudo:
                command = ['chown']
                if recursive and os.path.isdir(path):
                    command.append('-R')
                owner_str = f"{user}:{group}" if group else user
                command.extend([owner_str, path])
                
                returncode, stdout, stderr = self._run_sudo_command(command)
                if returncode != 0:
                    return {"error": f"Failed to change owner: {stderr}"}
            else:
                if recursive and os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        os.chown(root, uid, gid)
                        for item in dirs + files:
                            os.chown(os.path.join(root, item), uid, gid)
                else:
                    os.chown(path, uid, gid)

            return {
                "success": True,
                "path": path,
                "user": user,
                "group": group if group else "unchanged",
                "recursive": recursive
            }
        except Exception as e:
            return {"error": str(e)} 