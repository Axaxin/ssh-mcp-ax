import os
import socket
import socks
import paramiko
from fastmcp import FastMCP


mcp = FastMCP("ssh-mcp-jkuv")

class SSHClientManager:
    def __init__(self):
        self.client = None
        self.is_connected = False

    def _get_env_var(self, name, default=None, required=True):
        value = os.getenv(name, default)
        if value is None and required:
            raise ValueError(f"Environment variable {name} is not set.")
        return value

    def connect(self) -> dict:
        if self.is_connected and self.client and self.client.get_transport() and self.client.get_transport().is_active():
            print("Already connected to SSH server.")
            return {"success": True, "message": "Already connected."}

        # hostname = self._get_env_var('SSH_HOSTNAME', required=True)
        # username = self._get_env_var('SSH_USERNAME', required=True)
        # password = self._get_env_var('SSH_PASSWORD', required=False)  # Optional
        # private_key_path = self._get_env_var('SSH_PRIVATE_KEY_PATH', required=False)  # Optional
        # private_key_password = self._get_env_var('SSH_PRIVATE_KEY_PASSWORD', required=False)  # Optional
        # proxy_hostname = self._get_env_var('SSH_PROXY_HOSTNAME', required=False)  # Optional
        # proxy_port = self._get_env_var('SSH_PROXY_PORT', required=False)  # Optional

        hostname = os.getenv('SSH_HOSTNAME')
        username = os.getenv('SSH_USERNAME')
        password = os.getenv('SSH_PASSWORD',None) # Optional
        private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH',None) # Optional
        private_key_password = os.getenv('SSH_PRIVATE_KEY_PASSWORD',None) # Optional
        proxy_hostname = os.getenv('SSH_PROXY_HOSTNAME',None) # Optional
        proxy_port = os.getenv('SSH_PROXY_PORT',None) # Optional

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if proxy_hostname and proxy_port:
                try:
                    proxy_port = int(proxy_port)
                    socks.set_default_proxy(socks.SOCKS5, proxy_hostname, proxy_port)
                    socket.socket = socks.socksocket
                except Exception as e:
                    return {"success": False, "message": f"Failed to set SOCKS5 proxy: {e}"}

            connect_kwargs = {"hostname": hostname, "username": username}

            if private_key_path:
                if private_key_password:
                    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=private_key_password)
                    connect_kwargs["pkey"] = private_key
                else:
                    connect_kwargs["key_filename"] = private_key_path
            elif password:
                connect_kwargs["password"] = password
            else:
                raise ValueError("Either SSH_PASSWORD or SSH_PRIVATE_KEY_PATH must be set for authentication.")

            self.client.connect(**connect_kwargs)

            self.is_connected = True
            return {"success": True, "message": f"Successfully connected to {hostname}."}

        except FileNotFoundError:
            return {"success": False, "message": f"Private key file not found: {private_key_path}"}
        except paramiko.AuthenticationException:
            return {"success": False, "message": "Authentication failed. Please check username, password, private key path, or private key password."}
        except paramiko.SSHException as e:
            return {"success": False, "message": f"SSH connection error: {e}"}
        except ValueError as e:
            return {"success": False, "message": f"Configuration error: {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unknown error occurred: {e}"}

    def is_ssh_connected(self) -> bool:
        return self.is_connected and self.client and self.client.get_transport() and self.client.get_transport().is_active()

    def execute_command(self, command: str) -> dict:
        if not self.is_ssh_connected():
            # print("SSH connection not active. Attempting to reconnect...")
            connect_result = self.connect()
            if not connect_result["success"]:
                return {"output": "", "error": f"Failed to re-establish SSH connection: {connect_result['message']}"}

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            return {"output": output, "error": error}
        except paramiko.SSHException as e:
            # If command execution fails due to SSH issues, mark as disconnected
            self.is_connected = False
            return {"output": "", "error": f"Error executing command: {e}. Connection might be lost."}
        except Exception as e:
            return {"output": "", "error": f"An unknown error occurred during command execution: {e}"}

    def close(self):
        if self.client:
            self.client.close()
            self.is_connected = False
            print("SSH connection closed.")

ssh_manager = SSHClientManager()

# Add SSH tools
# Add SSH tools
@mcp.tool()
def connect_ssh() -> dict:
    """Connects to the SSH server using environment variables."""
    return ssh_manager.connect()

@mcp.tool()
def check_ssh_connection() -> bool:
    """Checks if the SSH connection is active."""
    return ssh_manager.is_ssh_connected()

@mcp.tool()
def execute_ssh_command(command: str) -> dict:
    """Executes a command on the connected SSH server.

    Args:
        command: The command string to execute.
    """
    return ssh_manager.execute_command(command)


if __name__ == "__main__":
    try:
        mcp.run(transport="sse",host="0.0.0.0") 
    finally:
        ssh_manager.close() # Ensure SSH connection is closed on exit
