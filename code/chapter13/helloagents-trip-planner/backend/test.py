"""测试高德地图MCP服务器连接和工具列表"""

from app.services.amap_service import get_amap_mcp_tool
from app.config import validate_config, get_settings

def test_amap_mcp_connection():
    """测试连接高德地图MCP服务器并列出工具列表"""
    try:
        # 验证配置
        print("1. 验证配置...")
        validate_config()
        
        settings = get_settings()
        print(f"   高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")
        
        # 获取MCP工具实例
        print("\n2. 连接高德地图MCP服务器...")
        amap_mcp_tool = get_amap_mcp_tool()
        
        # 获取工具列表
        print("\n3. 获取工具列表...")
        tools_result = amap_mcp_tool.run({"action": "list_tools"})
        print(f"{tools_result}")
                
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        print(f"\n错误详情:\n{traceback.format_exc()}")


if __name__ == "__main__":
    print("=" * 50)
    print("  高德地图MCP服务器连接和工具列表测试")
    print("=" * 50)
    test_amap_mcp_connection()
