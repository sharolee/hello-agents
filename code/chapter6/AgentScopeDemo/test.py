# -*- coding: utf-8 -*-
"""
测试大模型响应
使用.env配置文件中的API设置
"""
import asyncio
import os
from dotenv import load_dotenv
from agentscope.model import OpenAIChatModel

# 加载环境变量
load_dotenv()

async def test_llm_response():
    """测试大模型是否能够正确响应"""
    
    # 从环境变量获取配置
    model_id = os.getenv("LLM_MODEL_ID")
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    timeout = int(os.getenv("LLM_TIMEOUT", "60"))
    
    print(f"正在测试模型配置:")
    print(f"模型ID: {model_id}")
    print(f"API Base URL: {base_url}")
    print(f"超时时间: {timeout}秒")
    print("-" * 50)
    
    try:
        # 初始化模型
        model = OpenAIChatModel(
            model_name=model_id,
            api_key=api_key,
            stream=False,
            client_args={
                "base_url": base_url
            }
        )
        
        # 测试简单对话
        test_messages = [
            {"role": "user", "content": "你好，请简单介绍一下你自己。"}
        ]
        
        print("发送测试请求...")
        response = await model(messages=test_messages)
        
        print("模型响应:")
        # 处理响应格式
        if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0 and 'text' in response.content[0]:
            print(response.content[0]['text'])
        else:
            print(response)
        print("-" * 50)
        
        # 测试更复杂的任务
        complex_messages = [
            {"role": "user", "content": "请列出三个中国历史上的著名人物，并每人用一句话描述。"}
        ]
        
        print("发送复杂任务请求...")
        complex_response = await model(messages=complex_messages)
        
        print("复杂任务响应:")
        # 处理响应格式
        if hasattr(complex_response, 'content') and isinstance(complex_response.content, list) and len(complex_response.content) > 0 and 'text' in complex_response.content[0]:
            print(complex_response.content[0]['text'])
        else:
            print(complex_response)
        print("-" * 50)
        
        print("✅ 测试成功！大模型能够正常响应。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_llm_response())