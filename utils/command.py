from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path


class CommandRunner:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def ensure_command(self, executable: str) -> None:
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required executable '{executable}' was not found in PATH.")

    def run(self, command: list[str], cwd: str | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running command: %s", " ".join(command))
        
        # Use Popen to stream output in real-time
        process = subprocess.Popen(
            command,
            cwd=cwd,
            text=True,
            stdin=subprocess.PIPE if input_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr into stdout for easier streaming
            bufsize=1,
            universal_newlines=True,
        )

        output = []
        if input_text:
            process.stdin.write(input_text)
            process.stdin.close()

        for line in process.stdout:
            print(line, end="", flush=True)
            output.append(line)
        
        process.stdout.close()
        process.wait()
        full_output = "".join(output)

        if process.returncode != 0:
            raise RuntimeError(
                f"Command failed ({process.returncode}): {' '.join(command)}\nOUTPUT:\n{full_output}"
            )
        
        return subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=full_output,
            stderr=""
        )

    def write_text_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
