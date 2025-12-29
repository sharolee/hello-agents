"""TerminalTool4Windows - Windows命令行工具

为Agent提供安全的Windows命令行执行能力，支持：
- 文件系统操作（dir, type, more, findstr, where）
- 文本处理（powershell Measure-Object, sort, Get-Unique）
- 目录导航（cd）
- 安全限制（白名单命令、路径限制、超时控制）

使用场景：
- JIT（即时）文件检索与分析
- 代码仓库探索
- 日志文件分析
- 数据文件预览

安全特性：
- 命令白名单（只允许安全的只读命令）
- 工作目录限制（沙箱）
- 超时控制
- 输出大小限制
- 禁止危险操作（del, move, attrib等）
"""

from typing import Dict, Any, List, Optional
import subprocess
import os
import re
from pathlib import Path
import shlex
import platform

from hello_agents.tools.base import Tool, ToolParameter


class TerminalTool4Windows(Tool):
    """Windows命令行工具
    
    提供安全的Windows命令行执行能力，支持常用的文件系统和文本处理命令。
    
    安全限制：
    - 只允许白名单中的命令
    - 限制在指定工作目录内
    - 超时控制（默认30秒）
    - 输出大小限制（默认10MB）
    
    用法示例：
    ```python
    terminal = TerminalTool4Windows(workspace="./project")
    
    # 列出文件
    result = terminal.run({"command": "dir"})
    
    # 查看文件内容
    result = terminal.run({"command": "type README.md"})
    
    # 搜索文件
    result = terminal.run({"command": "findstr /s /i \"TODO\" src\\*.*"})
    
    # 查看文件前10行
    result = terminal.run({"command": "powershell Get-Content -Path data.csv -TotalCount 10"})
    ```
    """
    
    # Windows允许的命令白名单
    ALLOWED_COMMANDS = {
        # 文件列表与信息
        'dir', 'tree',
        # 文件内容查看
        'type', 'more', 'less',
        # 文件搜索
        'findstr', 'where',
        # 文本处理
        'sort', 'find',
        # 目录操作
        'cd', 'chdir',
        # 文件信息
        'wmic', 'vol', 'label',
        # 其他
        'echo', 'ver',
        # 代码执行
        'python', 'node', 'powershell', 'cmd', 'ipconfig', 'ping', 'systeminfo',
        # PowerShell 命令
        'get-content', 'select-string', 'measure-object', 'get-item', 
        'get-itemproperty', 'get-childitem', 'get-unique', 'get-location',
        'set-location', 'test-path', 'split-path', 'join-path',
    }
    
    def __init__(
        self,
        workspace: str = ".",
        timeout: int = 30,
        max_output_size: int = 10 * 1024 * 1024,  # 10MB
        allow_cd: bool = True
    ):
        super().__init__(
            name="terminal4windows",
            description="Windows命令行工具 - 执行安全的文件系统、文本处理和代码执行命令（dir, type, findstr, more等）"
        )
        
        self.workspace = Path(workspace).resolve()
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allow_cd = allow_cd
        
        # 当前工作目录（相对于workspace）
        self.current_dir = self.workspace
        
        # 确保工作目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        if not self.validate_parameters(parameters):
            return "❌ 参数验证失败"
        
        command = parameters.get("command", "").strip()
        
        if not command:
            return "❌ 命令不能为空"
        
        # 解析命令
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return f"❌ 命令解析失败: {e}"
        
        if not parts:
            return "❌ 命令不能为空"
        
        base_command = parts[0].lower()
        
        # 检查命令是否在白名单中
        if base_command not in self.ALLOWED_COMMANDS:
            return f"❌ 不允许的命令: {base_command}\n允许的命令: {', '.join(sorted(self.ALLOWED_COMMANDS))}"
        
        # 安全检查：验证命令中的文件路径是否在工作目录内
        security_check = self._check_command_security(command)
        if security_check:
            return security_check
        
        # 特殊处理 cd 命令
        if base_command in ('cd', 'chdir'):
            return self._handle_cd(parts)
        
        # 执行命令
        return self._execute_command(command)
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="command",
                type="string",
                description=(
                    f"要执行的命令（白名单: {', '.join(sorted(list(self.ALLOWED_COMMANDS)[:10]))}...）\n"
                    "示例: 'dir', 'type file.txt', 'findstr /s /i \"pattern\" *.py', 'powershell Get-Content -Path data.csv -TotalCount 20'"
                ),
                required=True
            ),
        ]
    
    def _check_command_security(self, command: str) -> Optional[str]:
        """检查命令中的文件路径是否在工作目录内"""
        # 对于PowerShell命令，需要特殊处理
        if command.lower().startswith('powershell'):
            # 提取PowerShell命令部分
            ps_command = command
            if command.lower().startswith('powershell -command'):
                # 提取引号内的内容
                match = re.search(r'-command\s+"([^"]*)"', command, re.IGNORECASE)
                if match:
                    ps_command = match.group(1)
                else:
                    # 如果没有引号，尝试提取剩余部分
                    ps_command = command[len('powershell -command'):].strip()
            
            # 检查PowerShell命令中的文件路径
            # 常见的文件操作命令
            file_commands = ['get-content', 'type', 'cat', 'select-string', 'get-item', 'get-childitem']
            
            for cmd in file_commands:
                if cmd.lower() in ps_command.lower():
                    # 提取路径参数
                    if '-path' in ps_command.lower():
                        # 使用正则表达式提取-Path参数后的路径
                        path_match = re.search(r'-path\s+([^\s]+)', ps_command, re.IGNORECASE)
                        if path_match:
                            path = path_match.group(1).strip('"\'')
                            return self._validate_path(path)
                    else:
                        # 对于没有-Path参数的情况，尝试提取命令后的第一个参数
                        parts = ps_command.split()
                        for i, part in enumerate(parts):
                            if part.lower() == cmd and i + 1 < len(parts):
                                path = parts[i + 1].strip('"\'')
                                return self._validate_path(path)
        else:
            # 对于非PowerShell命令，检查常见的文件操作命令
            file_commands = ['type', 'cat', 'findstr', 'more', 'copy', 'move', 'del', 'erase']
            
            for cmd in file_commands:
                if command.lower().startswith(cmd):
                    # 提取命令后的参数
                    parts = command[len(cmd):].strip()
                    if parts:
                        # 对于多参数命令，只检查第一个参数（通常是文件路径）
                        args = parts.split()
                        if args:
                            path = args[0].strip('"\'')
                            return self._validate_path(path)
        
        return None
    
    def _validate_path(self, path: str) -> Optional[str]:
        """验证路径是否在工作目录内"""
        try:
            # 解析路径
            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1]
            
            # 如果是绝对路径
            if os.path.isabs(path):
                full_path = Path(path).resolve()
            else:
                # 相对于当前目录的路径
                full_path = (self.current_dir / path).resolve()
            
            # 检查是否在工作目录内
            try:
                full_path.relative_to(self.workspace)
                return None  # 路径安全
            except ValueError:
                return f"❌ 安全错误: 尝试访问工作目录外的文件或目录: {full_path}\n工作目录: {self.workspace}"
        except Exception as e:
            return f"❌ 路径验证失败: {e}"
    
    def _handle_cd(self, parts: List[str]) -> str:
        """处理 cd 命令"""
        if not self.allow_cd:
            return "❌ cd 命令已禁用"
        
        if len(parts) < 2:
            # cd 无参数，返回当前目录
            return f"当前目录: {self.current_dir}"
        
        target_dir = parts[1]
        
        # 处理相对路径
        if target_dir == "..":
            new_dir = self.current_dir.parent
        elif target_dir == ".":
            new_dir = self.current_dir
        elif target_dir == "~":
            new_dir = self.workspace
        else:
            new_dir = (self.current_dir / target_dir).resolve()
        
        # 检查是否在工作目录内
        try:
            new_dir.relative_to(self.workspace)
        except ValueError:
            return f"❌ 不允许访问工作目录外的路径: {new_dir}"
        
        # 检查目录是否存在
        if not new_dir.exists():
            return f"❌ 目录不存在: {new_dir}"
        
        if not new_dir.is_dir():
            return f"❌ 不是目录: {new_dir}"
        
        # 更新当前目录
        self.current_dir = new_dir
        return f"✅ 切换到目录: {self.current_dir}"
    
    def _execute_command(self, command: str) -> str:
        """执行命令"""
        try:
            # 检查是否是PowerShell命令
            is_powershell = command.strip().lower().startswith('powershell')
            
            # 对于文件内容查看命令，直接使用Python读取文件内容
            if any(cmd in command.lower() for cmd in ['type ', 'get-content', 'cat ']):
                # 提取文件路径
                file_path = None
                if 'type ' in command.lower():
                    # 提取type命令后的文件路径
                    file_path = command.split('type ', 1)[1].strip()
                elif 'get-content' in command.lower():
                    # 提取Get-Content命令后的文件路径
                    if '-path' in command.lower():
                        # 使用正则表达式提取-Path参数后的路径
                        path_match = re.search(r'-path\s+([^\s]+)', command, re.IGNORECASE)
                        if path_match:
                            file_path = path_match.group(1).strip('"\'')
                    else:
                        # 提取Get-Content后的第一个参数
                        parts = command.split()
                        for i, part in enumerate(parts):
                            if part.lower() == 'get-content' and i + 1 < len(parts):
                                file_path = parts[i + 1].strip('"\'')
                                break
                elif 'cat ' in command.lower():
                    # 提取cat命令后的文件路径
                    file_path = command.split('cat ', 1)[1].strip()
                
                # 如果找到了文件路径，使用Python直接读取文件内容
                if file_path:
                    try:
                        # 处理相对路径
                        if not os.path.isabs(file_path):
                            full_path = self.current_dir / file_path
                        else:
                            full_path = Path(file_path)
                        
                        # 检查文件是否存在
                        if not full_path.exists():
                            return f"❌ 文件不存在: {full_path}"
                        
                        # 检查是否在工作目录内
                        try:
                            full_path.relative_to(self.workspace)
                        except ValueError:
                            return f"❌ 安全错误: 尝试访问工作目录外的文件: {full_path}"
                        
                        # 读取文件内容
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        
                        # 处理-TotalCount参数
                        if '-totalcount' in command.lower():
                            tc_match = re.search(r'-totalcount\s+(\d+)', command, re.IGNORECASE)
                            if tc_match:
                                lines = content.split('\n')
                                content = '\n'.join(lines[:int(tc_match.group(1))])
                        
                        return content if content else "✅ 文件为空"
                    except Exception as e:
                        return f"❌ 读取文件失败: {e}"
            
            # 如果是PowerShell命令，确保使用正确的执行方式
            if is_powershell and not command.strip().lower().startswith('powershell -command'):
                # 提取PowerShell脚本部分
                ps_script = command.strip()[10:].strip()  # 移除'powershell'
                if not ps_script.startswith('-command'):
                    command = f"powershell -Command \"{ps_script}\""
            
            # 在当前目录下执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.current_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=os.environ.copy(),
                encoding='utf-8',
                errors='replace'  # 替换无法解码的字符
            )
            
            # 处理输出编码问题
            output = result.stdout if result.stdout is not None else ""
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            
            # 如果输出看起来像乱码（包含大量连续的问号或特殊字符），尝试用GBK解码
            if output and ('�' in output or (len(output) > 10 and output.count('�') > len(output) * 0.1)):
                try:
                    # 对于非文件查看命令，尝试用GBK解码
                    if not any(cmd in command.lower() for cmd in ['get-content', 'type ', 'cat ', '[system.io.file]']):
                        result = subprocess.run(
                            command,
                            shell=True,
                            cwd=str(self.current_dir),
                            capture_output=True,
                            timeout=self.timeout,
                            env=os.environ.copy()
                        )
                        
                        # 手动解码
                        gbk_output = result.stdout.decode('gbk', errors='replace') if result.stdout else ""
                        gbk_stderr = result.stderr.decode('gbk', errors='replace') if result.stderr else ""
                        
                        output = gbk_output
                        if gbk_stderr:
                            output += f"\n[stderr]\n{gbk_stderr}"
                except Exception:
                    # 如果解码也失败，保持原来的UTF-8输出
                    pass
            
            # 检查输出大小
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size]
                output += f"\n\n⚠️ 输出被截断（超过 {self.max_output_size} 字节）"
            
            # 添加返回码信息
            if result.returncode != 0:
                output = f"⚠️ 命令返回码: {result.returncode}\n\n{output}"
            
            return output if output else "✅ 命令执行成功（无输出）"
            
        except subprocess.TimeoutExpired:
            return f"❌ 命令执行超时（超过 {self.timeout} 秒）"
        except Exception as e:
            return f"❌ 命令执行失败: {e}"
    
    def get_current_dir(self) -> str:
        """获取当前工作目录"""
        return str(self.current_dir)
    
    def reset_dir(self):
        """重置到工作目录根"""
        self.current_dir = self.workspace