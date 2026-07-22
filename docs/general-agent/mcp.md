### 开发一个MCP的Tool
- 提供一个查名单的功能。

### mcp sdk 下载
```bash
# 创建并进入工程目录
mkdir my-mcp-server
cd my-mcp-server
# 创建虚拟环境
python3 -m venv .venv
# 进入虚拟环境
source .venv/bin/activate
# 虚拟环境安装 MCP 核心库
pip install mcp
```

### 编写Tool 
```python
import os
from mcp.server.fastmcp import FastMCP
# 初始化MCP服务，名字会显示在工具列表中
mcp = FastMCP("LocalNameFinder")
# 模拟一个默认的名单路径（可选）
DEFAULT_PATH = os.path.expanduser("/Users/liurui/workspace/my-mcp-server/names_list.txt")

@mcp.tool()
async def search_person_in_file(name: str, file_path: str = DEFAULT_PATH) -> str:
    """
    在指定的本地文本文件中查找人名。
    :param name: 要查找的人名。
    :param file_path: 文件的绝对路径，默认为文档目录下的 names_list.txt。
    """
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        return f"错误：文件 {path} 不存在。请确认路径是否正确。"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # 读取所有行并清理空格
            content = [line.strip() for line in f.readlines() if line.strip()]
        if name in content:
            return f"找到了！'{name}' 确实在名单中。"
        else:
            return f"名单中没有找到 '{name}'。当前名单共有 {len(content)} 人。"
    except Exception as e:
        return f"读取文件时出错: {str(e)}"

if __name__ == "__main__":
    mcp.run()
```

### OpenCode 集成
```shell
{
  "plugin": [
    "oh-my-opencode"
  ],
  "mcp": {
    "name-finder": {
      "type": "local",
      "enabled": true,
      "command": [
        "/Users/liurui/workspace/my-mcp-server/.venv/bin/python",
        "/Users/liurui/workspace/my-mcp-server/name_server.py"
      ],
      "environment": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  },
  "$schema": "https://opencode.ai/config.json"
}
```

### 测试Tool 

