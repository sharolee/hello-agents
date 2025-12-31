from hello_agents.tools import MCPTool, A2ATool, ANPTool
import asyncio
from hello_agents.protocols import MCPClient

# 1. MCP：访问工具
# mcp_tool = MCPTool()
# # result = mcp_tool.run({
# #     "action": "call_tool",
# #     "tool_name": "add",
# #     "arguments": {"a": 10, "b": 20}
# # })
# # print(f"MCP计算结果: {result}")  # 输出: 30.0
# result = mcp_tool.run({"action": "list_tools"})
# print(f"MCP提供的工具: {result}")  

# result = mcp_tool.run({
#     "action": "call_tool",
#     "tool_name": "get_system_info"
# })
# print(f"MCP系统信息: {result}")  


# 2. ANP：服务发现
# anp_tool = ANPTool()
# anp_tool.run({
#     "action": "register_service",
#     "service_id": "calculator",
#     "service_type": "math",
#     "endpoint": "http://localhost:8080"
# })
# services = anp_tool.run({"action": "discover_services"})
# print(f"发现的服务: {services}")

# # 3. A2A：智能体通信
# a2a_tool = A2ATool("http://localhost:5000")
# print("A2A工具创建成功")


async def test_mcp_client():
    """测试MCPClient连接和资源访问"""
    if MCPClient is None:
        print("MCPClient不可用，跳过测试")
        return
        
    try:
        # 方式1：连接到社区提供的文件系统服务器
        # npx会自动下载并运行@modelcontextprotocol/server-filesystem包
        client = MCPClient([
            "npx", "-y",
            "@modelcontextprotocol/server-filesystem",
            "."  # 指定根目录
        ])

        # 使用async with确保连接正确关闭
        async with client:
            # 在这里使用client
            resources = await client.list_resources()
            print(f"可用资源：{[r['uri'] for r in resources]}")

            # 读取资源
            if resources:
                # 使用第一个可用资源作为示例
                first_resource_uri = resources[0]['uri']
                resource_content = await client.read_resource(first_resource_uri)
                print(f"资源内容：{resource_content}")
            else:
                print("没有可用的资源")
    except Exception as e:
        print(f"测试MCPClient时出错: {e}")


if __name__ == "__main__":
    # 运行MCPClient测试
    asyncio.run(test_mcp_client())
