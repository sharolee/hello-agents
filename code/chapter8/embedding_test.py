#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的嵌入测试脚本
使用 .env 文件中的 dashscope 配置测试文本嵌入功能
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入嵌入模块
try:
    from hello_agents.memory.embedding import DashScopeEmbedding
except ImportError:
    print("错误: 无法导入 hello_agents.memory.embedding 模块")
    print("请确保已正确安装 hello_agents 包")
    sys.exit(1)


def test_dashscope_embedding():
    """测试 DashScope 嵌入功能"""
    print("=" * 50)
    print("DashScope 嵌入测试")
    print("=" * 50)
    
    # 从环境变量获取配置
    embed_model_name = os.getenv("EMBED_MODEL_NAME", "text-embedding-v1")
    embed_api_key = os.getenv("EMBED_API_KEY")
    embed_base_url = os.getenv("EMBED_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    print(f"模型名称: {embed_model_name}")
    print(f"API Base URL: {embed_base_url}")
    print(f"API Key: {'*' * 20}{embed_api_key[-4:] if embed_api_key else 'None'}")
    print()
    
    try:
        # 初始化嵌入模型
        print("正在初始化 DashScope 嵌入模型...")
        embedder = DashScopeEmbedding(
            model_name=embed_model_name,
            api_key=embed_api_key,
            base_url=embed_base_url
        )
        print(f"✓ 初始化成功，向量维度: {embedder.dimension}")
        print()
        
        # 测试文本
        test_texts = [
            "你好，世界！",
            "Python是一种编程语言",
            "人工智能正在改变世界",
            "Hello, world!",
            "Artificial Intelligence"
        ]
        
        print("测试文本嵌入:")
        print("-" * 30)
        
        # 单个文本嵌入测试
        print("\n1. 单个文本嵌入测试:")
        single_text = test_texts[0]
        embedding = embedder.encode(single_text)
        print(f"文本: '{single_text}'")
        print(f"向量维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        print(f"向量范数: {np.linalg.norm(embedding):.4f}")
        
        # 批量文本嵌入测试
        print("\n2. 批量文本嵌入测试:")
        embeddings = embedder.encode(test_texts)
        print(f"批量处理 {len(test_texts)} 个文本")
        print(f"返回向量数量: {len(embeddings)}")
        print(f"每个向量维度: {[len(emb) for emb in embeddings]}")
        
        # 相似度计算
        print("\n3. 文本相似度计算:")
        
        # 手动计算余弦相似度
        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            return dot_product / (norm1 * norm2)
        
        # 计算所有文本之间的相似度
        similarity_matrix = np.zeros((len(test_texts), len(test_texts)))
        for i in range(len(test_texts)):
            for j in range(len(test_texts)):
                similarity_matrix[i][j] = cosine_similarity(embeddings[i], embeddings[j])
        
        print("文本相似度矩阵:")
        for i, text in enumerate(test_texts):
            print(f"{i+1}. {text}")
        
        print("\n相似度值:")
        for i in range(len(test_texts)):
            for j in range(i+1, len(test_texts)):
                similarity = similarity_matrix[i][j]
                print(f"'{test_texts[i]}' vs '{test_texts[j]}': {similarity:.4f}")
        
        # 找出最相似的文本对
        max_sim = 0
        max_pair = (0, 0)
        for i in range(len(test_texts)):
            for j in range(i+1, len(test_texts)):
                if similarity_matrix[i][j] > max_sim:
                    max_sim = similarity_matrix[i][j]
                    max_pair = (i, j)
        
        print(f"\n最相似的文本对:")
        print(f"'{test_texts[max_pair[0]]}' vs '{test_texts[max_pair[1]]}'")
        print(f"相似度: {max_sim:.4f}")
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_dashscope_embedding()
    sys.exit(0 if success else 1)