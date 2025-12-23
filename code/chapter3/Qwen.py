"""
使用 huggingface_hub 从国内镜像下载和运行 Qwen 模型
使用方法:
  python Qwen_hf_hub_v3.py                    # 正常运行，检查本地是否存在模型
  python Qwen_hf_hub_v3.py --force-download   # 强制重新下载模型
"""

import torch
import os
import sys
from huggingface_hub import snapshot_download, try_to_load_from_cache
from transformers import AutoModelForCausalLM, AutoTokenizer

# 设置镜像站点
hf_url = 'https://hf-mirror.com'
os.environ['HF_ENDPOINT'] = hf_url

# 指定模型ID
model_id = "Qwen/Qwen1.5-0.5B-Chat"

# 设置本地缓存目录 - 使用绝对路径
cache_dir = "d:\\models"

# 检查命令行参数，是否强制重新下载
force_download = "--force-download" in sys.argv
if force_download:
    print("检测到 --force-download 参数，将强制重新下载模型")

# 设置设备，优先使用GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 获取快照路径
def get_snapshot_path():
    """获取模型的快照路径"""
    try:
        # 尝试从缓存加载配置文件
        config_path = try_to_load_from_cache(
            model_id, "config.json", cache_dir=cache_dir
        )
        
        if config_path is None:
            return None
        
        # 从配置文件路径提取快照路径
        # config_path 格式: ./model_cache/models--Qwen--Qwen1.5-0.5B-Chat/snapshots/<hash>/config.json
        snapshot_path = os.path.dirname(config_path)
        print(f"找到快照路径: {snapshot_path}")
        return snapshot_path
    except Exception as e:
        print(f"获取快照路径时出错: {e}")
        return None

# 检查模型是否存在
snapshot_path = get_snapshot_path()
model_exists = snapshot_path is not None and not force_download

if model_exists:
    print("模型已存在于本地缓存，直接加载...")
    try:
        # 直接从快照路径加载模型
        tokenizer = AutoTokenizer.from_pretrained(
            snapshot_path, 
            trust_remote_code=True,
            local_files_only=True
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            snapshot_path, 
            trust_remote_code=True,
            local_files_only=True
        ).to(device)
        
        print("模型和分词器加载完成！")
    except Exception as e:
        print(f"从缓存加载模型失败: {e}")
        print("将尝试重新下载...")
        model_exists = False

if not model_exists:
    if force_download:
        print("强制重新下载模型...")
    else:
        print(f"模型未找到或不完整，正在从镜像站点下载: {model_id}")
    try:
        # 下载模型到本地缓存
        local_model_path = snapshot_download(
            repo_id=model_id,
            endpoint=hf_url,
            cache_dir=cache_dir,
            resume_download=True,
            force_download=force_download
        )
        print(f"模型已下载到: {local_model_path}")
        
        tokenizer = AutoTokenizer.from_pretrained(local_model_path, trust_remote_code=True)
        
        model = AutoModelForCausalLM.from_pretrained(local_model_path, trust_remote_code=True).to(device)
        
        print("模型和分词器加载完成！")
    except Exception as e:
        print(f"下载或加载模型失败: {e}")
        exit(1)

# 准备对话输入
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你好，请介绍你自己，说明你的特点和能力。"}
]

# 使用分词器的模板格式化输入
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 编码输入文本
model_inputs = tokenizer([text], return_tensors="pt").to(device)

print("编码后的输入文本:")
print(model_inputs)

# 使用模型生成回答
# max_new_tokens 控制了模型最多能生成多少个新的Token
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens=512
)

# 将生成的 Token ID 截取掉输入部分
# 这样我们只解码模型新生成的部分
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

# 解码生成的 Token ID
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("\n模型的回答:")
print(response)