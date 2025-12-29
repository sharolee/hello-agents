import os
from dotenv import load_dotenv

# 设置 HuggingFace 镜像端点 - 必须在导入 transformers 之前设置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 加载环境变量 - 必须在导入任何使用环境变量的模块之前调用
load_dotenv(override=True)

from datetime import datetime
from typing import List
from hello_agents.tools import MemoryTool
from hello_agents.core.database_config import get_database_config

def main():
    """主函数"""
    print("🚀 test")
    # os.getenv("QDRANT_URL")
    # print("QDRANT_URL:", os.getenv("QDRANT_URL"))

    # db_config = get_database_config()
    # print(db_config)
    
    clip_model = None
    clip_processor = None
    image_dim = 512
    
    try:
        from transformers import CLIPModel, CLIPProcessor
        clip_name = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
        clip_model = CLIPModel.from_pretrained(clip_name)
        clip_processor = CLIPProcessor.from_pretrained(clip_name)
        # 估计输出维度
        image_dim = clip_model.config.projection_dim if hasattr(clip_model.config, 'projection_dim') else 512
        print(f"✅ CLIP模型从 {clip_name} 加载成功，使用镜像端点: {os.environ.get('HF_ENDPOINT', '默认')}")
    except Exception as e:
        clip_model = None
        clip_processor = None
        image_dim = 512
        print(f"❌ CLIP模型加载失败: {e}")
    
    clap_model = None
    clap_processor = None
    audio_dim = 512
    
    try:
        from transformers import ClapProcessor, ClapModel
        clap_name = os.getenv("CLAP_MODEL", "laion/clap-htsat-unfused")
        clap_model = ClapModel.from_pretrained(clap_name)
        clap_processor = ClapProcessor.from_pretrained(clap_name)
        # 估计输出维度
        audio_dim = getattr(clap_model.config, 'projection_dim', None) or 512
        print(f"✅ CLAP模型从 {clap_name} 加载成功，使用镜像端点: {os.environ.get('HF_ENDPOINT', '默认')}")
    except Exception as e:
        clap_model = None
        clap_processor = None
        audio_dim = 512
        print(f"❌ CLAP模型加载失败: {e}")
    # memory_tool = MemoryTool(
    #     user_id="demo_user",
    #     memory_types=["working", "episodic", "semantic", "perceptual"]
    # )

    # result = memory_tool.execute(
    #     "add",
    #     content="正在学习HelloAgents框架的记忆系统",
    #     memory_type="working",
    #     importance=0.7,
    #     task_type="learning"
    # )
    # print(f"工作记忆: {result}")

    # result = memory_tool.execute(
    #     "search",
    #     query="记忆", 
    #     memory_type="working", 
    #     limit=2
    # )
    # print(f"搜索结果: {result}")

if __name__ == "__main__":
    main()