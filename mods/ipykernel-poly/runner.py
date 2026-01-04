import base64
import json

# import re
import requests
from ipykernel.kernelbase import Kernel


class PolyRunnerKernel(Kernel):
    implementation = "PolyRunner"
    implementation_version = "2.1"
    language = "markdown"
    language_version = "1.0"
    language_info = {
        "name": "poly_runner",
        "mimetype": "text/markdown",
        "file_extension": ".md",
    }
    banner = "Poly Runner Kernel - Stateless execution for Mermaid & more"

    def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
        **kwargs,
    ):
        if not silent:
            try:
                # 1. 鲁棒解析：不再单纯依赖正则
                lang, content = self._parse_code_block(code)

                # 2. 调试回显：如果解析失败，让我们知道 (调试用，稳定后可注释)
                # self._send_text(f"[Debug] Detected Lang: {lang}")

                # 3. 路由分发
                if lang == "mermaid":
                    self._handle_mermaid(content)
                elif lang == "plantuml":
                    self._handle_plantuml(content)
                elif lang == "json":
                    self._handle_json_format(content)
                elif lang == "detect":
                    self._handle_auto_detect(content)
                else:
                    # 如果有语言标记但没处理器 (比如 ```python)，还是原样返回吧
                    self._send_text(f"No handler for: {lang}\n{content[:30]}...")

            except Exception as e:
                self._send_text(f"Kernel Critical Error: {str(e)}")

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def _parse_code_block(self, raw_code):
        """
        通过行分析来解析代码块，比正则更稳定
        """
        lines = raw_code.strip().splitlines()
        if not lines:
            return "detect", raw_code

        first_line = lines[0].strip()

        # 检查是否以 ``` 开头
        if first_line.startswith("```"):
            # 提取语言标识 (例如: ```mermaid -> mermaid)
            lang = first_line.lstrip("`").strip().lower()

            # 提取内容：去掉第一行，如果最后一行也是 ``` 则去掉
            content_lines = lines[1:]
            if content_lines and content_lines[-1].strip().startswith("```"):
                content_lines.pop()

            return lang, "\n".join(content_lines)

        return "detect", raw_code

    def _handle_mermaid(self, code):
        """Mermaid 处理器 (带超时控制)"""
        try:
            # 清理一下可能存在的首尾空白
            clean_code = code.strip()
            if not clean_code:
                self._send_text("Empty Mermaid code block.")
                return

            graphbytes = clean_code.encode("utf8")
            base64_bytes = base64.b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
            url = "https://mermaid.ink/img/" + base64_string

            # 增加 timeout，防止网络卡死导致前端无响应
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                self._display_image(response.content, "jpeg")
            else:
                self._send_text(f"Mermaid Render Error (HTTP {response.status_code})")

        except requests.exceptions.RequestException as e:
            self._send_text(f"Network Error (Check mermaid.ink access): {e}")
        except Exception as e:
            self._send_text(f"Mermaid Handler Error: {e}")

    def _handle_plantuml(self, code):
        self._send_text(f"PlantUML not implemented yet.\nCode: {code[:20]}...")

    def _handle_json_format(self, code):
        try:
            # 尝试处理包含 ```json wrapper 的情况 (虽然 _parse_code_block 应该已经处理了)
            clean_code = code.strip()
            obj = json.loads(clean_code)
            formatted = json.dumps(obj, indent=4, ensure_ascii=False)
            self._send_text(formatted)
        except json.JSONDecodeError as e:
            self._send_text(f"Invalid JSON: {e}")

    def _handle_auto_detect(self, code):
        """智能回退：尝试在无 ``` 标记的情况下猜测"""
        c = code.strip()

        # 常见 Mermaid 关键字
        mermaid_keywords = [
            "graph ",
            "flowchart ",
            "sequenceDiagram",
            "classDiagram",
            "pie",
            "gantt",
            "erDiagram",
        ]

        if any(c.startswith(kw) for kw in mermaid_keywords):
            self._handle_mermaid(c)
        elif c.startswith("{") or c.startswith("["):
            self._handle_json_format(c)
        else:
            # 既没有 ``` 标记，也不像 Mermaid，原样回显
            self._send_text(code)

    def _display_image(self, image_data, format="jpeg"):
        self.send_response(
            self.iopub_socket,
            "display_data",
            {
                "data": {
                    f"image/{format}": base64.b64encode(image_data).decode("utf-8")
                },
                "metadata": {},
            },
        )

    def _send_text(self, text):
        stream_content = {"name": "stdout", "text": text}
        self.send_response(self.iopub_socket, "stream", stream_content)


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=PolyRunnerKernel)
