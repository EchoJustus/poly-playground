import base64
import json
import re

import requests
from ipykernel.kernelbase import Kernel


class PolyRunnerKernel(Kernel):
    implementation = "PolyRunner"
    implementation_version = "2.0"
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
            # 1. 解析代码：分离 语言标记(lang) 和 实际内容(content)
            lang, content = self._parse_code_block(code)

            # 2. 路由分发 (Dispatcher)
            # 这里是核心：根据提取到的 lang 决定调用哪个函数
            try:
                if lang == "mermaid":
                    self._handle_mermaid(content)

                elif lang == "plantuml":
                    self._handle_plantuml(content)

                elif lang == "json":
                    self._handle_json_format(content)

                elif lang == "detect":
                    # 如果没有 ```标记，尝试自动推断
                    self._handle_auto_detect(content)

                else:
                    self._send_text(
                        f"No handler for language: '{lang}'.\nContent echo:\n{content[:50]}..."
                    )

            except Exception as e:
                self._send_text(f"Execution Error: {str(e)}")

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def _parse_code_block(self, raw_code):
        """
        解析输入字符串。
        返回: (language_type, clean_content)
        """
        raw_code = raw_code.strip()

        # 正则匹配：以 ```开头，后跟语言标识符，最后以 ```结尾(可选)
        # 捕获组1: 语言标识符 (如 mermaid)
        # 捕获组2: 内容
        pattern = r"^```(\w+)\s*\n([\s\S]*?)(?:```)?$"
        match = re.match(pattern, raw_code)

        if match:
            lang = match.group(1).lower()
            content = match.group(2).strip()
            return lang, content
        else:
            # 用户可能直接选中了内部文本，没有带 ```
            return "detect", raw_code

    # --- Handlers (处理器) ---

    def _handle_mermaid(self, code):
        """Mermaid 处理器: 调用 mermaid.ink"""
        graphbytes = code.encode("utf8")
        base64_bytes = base64.b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        url = "https://mermaid.ink/img/" + base64_string

        response = requests.get(url)
        if response.status_code == 200:
            self._display_image(response.content, "jpeg")
        else:
            self._send_text(f"Mermaid Render Failed (HTTP {response.status_code})")

    def _handle_plantuml(self, code):
        """
        PlantUML 处理器
        注意：PlantUML 官方使用的是自定义的压缩算法(Deflate+非标准Base64)，而非标准Base64。
        这里为了演示，假设你有一个支持标准Base64或者Raw文本的PlantUML代理服务。
        如果没有，推荐使用简单的 hex 编码传给某些支持 hex 的公开 server，或者提示用户安装本地库。
        """
        # 这是一个简单的演示，实际 PlantUML 编码比较复杂，建议作为下一步扩展
        self._send_text(
            f"PlantUML Handler triggered!\n(To render PlantUML, a specific compression algo is needed.\nCode received: {code[:30]}...)"
        )

    def _handle_json_format(self, code):
        """实用工具示例：格式化 JSON"""
        try:
            obj = json.loads(code)
            formatted = json.dumps(obj, indent=4, ensure_ascii=False)
            self._send_text(formatted)
        except json.JSONDecodeError:
            self._send_text("Invalid JSON content.")

    def _handle_auto_detect(self, code):
        """无标记时的智能回退逻辑"""
        # 旧的关键词检测逻辑放在这里
        mermaid_keywords = [
            "graph ",
            "flowchart ",
            "sequenceDiagram",
            "classDiagram",
            "pie",
            "gantt",
        ]
        if any(code.startswith(kw) for kw in mermaid_keywords):
            self._handle_mermaid(code)
        elif code.startswith("{") or code.startswith("["):
            self._handle_json_format(code)
        else:
            self._send_text(code)  # 原样返回

    # --- Output Helpers ---

    def _display_image(self, image_data, format="jpeg"):
        """发送图片到前端"""
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
        """发送文本到前端"""
        stream_content = {"name": "stdout", "text": text}
        self.send_response(self.iopub_socket, "stream", stream_content)


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=PolyRunnerKernel)
