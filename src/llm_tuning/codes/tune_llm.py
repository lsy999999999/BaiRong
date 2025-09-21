import os
import sys
import re
import json
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datasets import load_dataset, Dataset
from trl import (
    SFTConfig,
    SFTTrainer,
    DataCollatorForCompletionOnlyLM,
    PPOConfig,
    PPOTrainer,
    AutoModelForCausalLMWithValueHead,
    create_reference_model,
)
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)
from transformers.integrations import MLflowCallback
from peft import LoraConfig, PeftModel, get_peft_model
import torch
import argparse
import mlflow
import time
import uuid
from datetime import datetime
from mlflow.models import infer_signature

from utils.constants import *
from utils.utils import check_load_adapter, check_dirs
from backend.models.model_library import get_model_library, ModelMetadata

# 初始化模型库
model_library = get_model_library()

def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuning_mode", type=str, help="sft or ppo", default="sft")
    parser.add_argument(
        "--llm_path", type=str, help="Path to the base LLM model", required=True
    )
    parser.add_argument(
        "--dataset_path", type=str, help="Path to the dataset", required=True
    )
    parser.add_argument(
        "--experiment_name", type=str, help="MLflow experiment name", default="llm_tuning"
    )
    parser.add_argument(
        "--tracking_uri", type=str, help="MLflow tracking URI", default="./mlruns"
    )
    parser.add_argument(
        "--devices", type=str, help="CUDA visible devices", default="0"
    )
    return parser.parse_args()


def tokenize_for_ppo(tokenizer, sample):
    """为PPO训练准备数据的通用函数"""
    sample["query_ids"] = tokenizer.encode(sample["prompt"])
    sample["response_ids"] = tokenizer.encode(sample["output"])
    sample["query"] = tokenizer.decode(sample["query_ids"])
    sample["response"] = tokenizer.decode(sample["response_ids"])
    sample["reward"] = float(sample["rating"])  # PPO内部仍使用reward字段
    return sample

def load_training_data(dataset_path, tuning_mode="sft", tokenizer=None):
    """
    加载并处理训练数据，根据tuning_mode动态处理
    
    Args:
        dataset_path: 数据集路径
        tuning_mode: 训练模式 ("sft" 或 "ppo")
        tokenizer: 用于PPO模式的分词器
        
    Returns:
        Dataset: 处理后的数据集
    """
    try:
        # 直接加载原始数据
        with open(dataset_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        # 过滤和处理数据
        valid_data = []
        for item in raw_data:
            # 跳过不包含必要字段的数据
            if "prompt" not in item or "output" not in item or "rating" not in item:
                continue
                
            # 清理输出中的Markdown代码块
            output = item["output"]
            if isinstance(output, str) and output.startswith("```") and output.endswith("```"):
                lines = output.strip().split("\n")
                if len(lines) > 2:
                    output = "\n".join(lines[1:-1])
                    
            # 创建训练样本
            sample = {
                "prompt": item["prompt"],
                "output": output,
                "rating": float(item["rating"])
            }
            
            # 添加可选字段
            for field in ["feedback", "reason"]:
                if field in item:
                    sample[field] = item[field]
            
            valid_data.append(sample)
            
        print(f"加载了{len(valid_data)}/{len(raw_data)}个有效样本")
        
        # 创建数据集
        dataset = Dataset.from_list(valid_data)
        
        # 根据模式进行特定处理
        if tuning_mode == "ppo" and tokenizer is not None:
            # 注意：这里需要为tokenize_for_ppo提供tokenizer参数
            dataset = dataset.map(lambda x: tokenize_for_ppo(tokenizer, x))
        
        return dataset
    
    except Exception as e:
        print(f"加载训练数据时出错: {e}")
        return None


def copy_saves_and_register(llm_path, tuning_mode, fine_tuning_params=None):
    """复制保存的模型并在模型库中注册"""
    # 复制模型到正式保存目录
    os.system(f"cp -r {TMP_SAVE_DIR}/* {SAVE_DIR}/")
    
    # 获取基础模型ID（使用路径作为ID）
    base_model_id = os.path.basename(llm_path)
    if not base_model_id:
        base_model_id = llm_path.replace("/", "_")
    
    # 生成新的模型ID
    model_id = f"ft_{tuning_mode}_{base_model_id}_{int(time.time())}"
    
    # 创建新的模型目录
    model_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "models",
        model_id
    )
    
    # 确保目录存在
    os.makedirs(model_dir, exist_ok=True)
    
    # 复制模型到新目录
    os.system(f"cp -r {SAVE_DIR}/* {model_dir}/")
    
    # 计算模型大小
    size = 0
    for dirpath, _, filenames in os.walk(model_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    
    # 尝试获取基础模型信息
    base_model = model_library.get_model_by_id(base_model_id)
    parameter_size = None
    if base_model and "parameter_size" in base_model:
        parameter_size = base_model.get("parameter_size")
    
    # 准备新模型的名称（包含参数大小）
    model_name = f"{os.path.basename(llm_path)}_{tuning_mode}_ft"
    
    # 准备元数据
    model_metadata = ModelMetadata(
        model_id=model_id,
        model_name=model_name,
        model_type="fine_tuned",
        description=f"微调模型，基于{os.path.basename(llm_path)}，使用{tuning_mode}方法",
        path=model_dir,
        created_at=datetime.now().isoformat(),
        base_model_id=base_model_id,
        fine_tuning_params=fine_tuning_params,
        version="1.0",
        size=size,
        parameter_size=parameter_size,
        tags=[tuning_mode, "fine-tuned"]
    )
    
    # 如果有参数大小，添加到标签
    if parameter_size and parameter_size not in model_metadata.tags:
        model_metadata.tags.append(parameter_size)
    
    # 在模型库中注册
    try:
        model_library.register_model(model_metadata)
        print(f"模型已注册到模型库，ID: {model_id}")
    except Exception as e:
        print(f"注册模型到模型库失败: {str(e)}")
    
    # 清理临时目录
    os.system(f"rm -rf {TMP_SAVE_DIR}")
    print(f"已将训练好的模型复制到 {SAVE_DIR} 和 {model_dir}")
    
    return model_id


class Tuner:
    def __init__(self, tuning_mode, llm_path, dataset_path=None, experiment_name="llm_tuning", tracking_uri="./mlruns"):
        self.tuning_mode = tuning_mode
        self.llm_path = llm_path
        self.dataset_path = dataset_path
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        
        # Setup MLflow
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        
        tokenizer = AutoTokenizer.from_pretrained(
            llm_path,
            trust_remote_code=True,
        )
        tokenizer.pad_token = tokenizer.eos_token
        self.tokenizer = tokenizer
        check_dirs(llm_path)

    def train_func(self):
        timestamp = int(time.time())
        fine_tuning_params = {
            "tuning_mode": self.tuning_mode,
            "llm_path": self.llm_path,
            "timestamp": timestamp
        }
        
        with mlflow.start_run(run_name=f"{self.tuning_mode}_training_{timestamp}"):
            # Log parameters
            mlflow.log_param("tuning_mode", self.tuning_mode)
            mlflow.log_param("llm_path", self.llm_path)
            
            if self.tuning_mode == "sft":
                model = self.sft_train()
            elif self.tuning_mode == "ppo":
                model = self.ppo_train()
                
            # Log the model to MLflow
            if model is not None:
                # Create a sample input for signature
                sample_input = {"prompt": "Hello, how are you?"}
                # Get sample output
                sample_output = {"response": "I'm doing well, thank you for asking!"}
                signature = infer_signature(sample_input, sample_output)
                
                mlflow.transformers.log_model(
                    transformers_model={
                        "model": model,
                        "tokenizer": self.tokenizer
                    },
                    artifact_path="model",
                    signature=signature,
                    task="text-generation",
                    registered_model_name=f"{self.tuning_mode}_model_{timestamp}",
                )
                
                # 保存其他训练参数
                fine_tuning_params.update({
                    "epochs": 1,  # 可以从trainer配置中获取
                    "batch_size": 1  # 可以从trainer配置中获取
                })
            
            # 复制并注册模型
            copy_saves_and_register(self.llm_path, self.tuning_mode, fine_tuning_params)

    def formatting_prompts_func(self, example):
        output_texts = []
        for i in range(len(example["prompt"])):
            text = f"### Question: {example['prompt'][i]}\n\n### Assistant: {example['output'][i]}"
            output_texts.append(text)
        return output_texts

    def sft_train(self):
        # 检查是否提供了数据集路径
        if self.dataset_path and os.path.exists(self.dataset_path):
            dataset_path = self.dataset_path
        else:
            # 使用默认路径
            dataset_path = os.path.join(SFT_FILE_PATH, "sft_data.json")
            
        if not os.path.exists(dataset_path):
            print(f"数据集文件不存在: {dataset_path}")
            return None
            
        # 加载并处理数据
        dataset = load_training_data(dataset_path, "sft")
        if dataset is None or len(dataset) == 0:
            print("没有有效的训练数据")
            return None
        
        # Log dataset info
        mlflow.log_param("dataset_size", len(dataset))
        mlflow.log_param("dataset_path", dataset_path)

        response_template_string = "\n### Assistant:"
        response_template_ids = self.tokenizer.encode(
            response_template_string, add_special_tokens=False
        )[2:]

        collator = DataCollatorForCompletionOnlyLM(
            response_template_ids, tokenizer=self.tokenizer
        )
        sft_config = SFTConfig(
            output_dir=TMP_SAVE_DIR,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            max_seq_length=8192,
            logging_steps=100,
        )

        if_load_adapter = check_load_adapter(self.llm_path)
        if if_load_adapter:
            model = AutoModelForCausalLM.from_pretrained(
                self.llm_path,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            model = PeftModel.from_pretrained(model, SAVE_DIR)
            for name, param in model.named_parameters():
                if "lora" in name:
                    param.requires_grad = True
            print("Loaded the adapter.")
        else:
            peft_config = LoraConfig(
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
            )

            model = AutoModelForCausalLM.from_pretrained(
                self.llm_path,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            model = get_peft_model(model, peft_config)

        self.trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            args=sft_config,
            tokenizer=self.tokenizer,
            data_collator=collator,
            formatting_func=self.formatting_prompts_func,
            callbacks=[MLflowCallback()],
        )

        print("Starting SFT training")
        self.trainer.train()

        # Log training metrics
        train_metrics = self.trainer.state.log_history
        for metric_dict in train_metrics:
            step = metric_dict.get("step", 0)
            for key, value in metric_dict.items():
                if key != "step" and isinstance(value, (int, float)):
                    mlflow.log_metric(key, value, step=step)

        self.trainer.save_model(TMP_SAVE_DIR)
        print(f"Training progress: 1.0")
        mlflow.log_metric("training_progress", 1.0)
        
        # Log model artifacts
        mlflow.log_artifacts(TMP_SAVE_DIR, artifact_path="model_files")
        
        return model

    def ppo_train(self):
        # 检查是否提供了数据集路径
        if self.dataset_path and os.path.exists(self.dataset_path):
            dataset_path = self.dataset_path
        else:
            # 使用默认路径
            dataset_path = os.path.join(PPO_FILE_PATH, "ppo_data.json")
            
        if not os.path.exists(dataset_path):
            print(f"数据集文件不存在: {dataset_path}")
            return None
            
        # 加载并处理数据
        dataset = load_training_data(dataset_path, "ppo", self.tokenizer)
        if dataset is None or len(dataset) == 0:
            print("没有有效的训练数据")
            return None
        
        # 设置数据格式
        dataset.set_format(
            type="torch", columns=["query_ids", "response_ids", "reward"]
        )
        
        # Log dataset info
        mlflow.log_param("dataset_size", len(dataset))
        mlflow.log_param("dataset_path", dataset_path)

        if_load_adapter = check_load_adapter(self.llm_path)
        if if_load_adapter:
            model = AutoModelForCausalLM.from_pretrained(
                self.llm_path,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            model = PeftModel.from_pretrained(model, SAVE_DIR)
            model = AutoModelForCausalLMWithValueHead.from_pretrained(
                model,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            print("Loaded the adapter.")
        else:
            peft_config = LoraConfig(
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
            )
            model = AutoModelForCausalLMWithValueHead.from_pretrained(
                self.llm_path,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                peft_config=peft_config,
            )

        for name, param in model.named_parameters():
            if "lora" in name:
                param.requires_grad = True

        ref_model = create_reference_model(model)

        ppo_config = PPOConfig(
            ppo_epochs=1,
            whiten_rewards=True,
            batch_size=1,
            remove_unused_columns=False,
            mini_batch_size=1,
        )

        def collator(data):
            return {key: [d[key] for d in data] for key in data[0]}

        self.trainer = PPOTrainer(
            config=ppo_config,
            model=model,
            ref_model=ref_model,
            tokenizer=self.tokenizer,
            dataset=dataset,
            data_collator=collator,
        )

        # Track PPO training metrics
        all_stats = []
        for _epoch, batch in enumerate(self.trainer.dataloader):
            query_tensors = batch["query_ids"]
            response_tensors = batch["response_ids"]
            rewards_tensors = [x.float() for x in batch["reward"]]

            stats = self.trainer.step(query_tensors, response_tensors, rewards_tensors)
            all_stats.append(stats)
            
            # Log PPO metrics
            if _epoch % 100 == 0:
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(key, value, step=_epoch)

        # Log average metrics
        if all_stats:
            avg_stats = {k: sum(d.get(k, 0) for d in all_stats) / len(all_stats) 
                        for k in set().union(*all_stats) if isinstance(all_stats[0].get(k, 0), (int, float))}
            for key, value in avg_stats.items():
                mlflow.log_metric(f"avg_{key}", value)

        self.trainer.save_pretrained(TMP_SAVE_DIR)
        print("Training progress: 1.0")
        mlflow.log_metric("training_progress", 1.0)
        
        # Log model artifacts
        mlflow.log_artifacts(TMP_SAVE_DIR, artifact_path="model_files")
        
        return self.trainer.model.pretrained_model


def run_tuning(tuning_mode, llm_path, dataset_path=None, experiment_name="llm_tuning", tracking_uri="./mlruns", devices="0"):
    """
    Main function to run the tuning process.
    
    Args:
        tuning_mode (str): Type of tuning, "sft" or "ppo"
        llm_path (str): Path to the LLM model to be tuned
        dataset_path (str): Path to the dataset file
        experiment_name (str): Name of the MLflow experiment
        tracking_uri (str): MLflow tracking URI
        devices (str): CUDA devices to use
    
    Returns:
        str: ID of the fine-tuned model
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = devices
    
    # 检查是否已经注册了基础模型
    base_model_id = os.path.basename(llm_path)
    if not base_model_id:
        base_model_id = llm_path.replace("/", "_")
    
    base_model = model_library.get_model_by_id(base_model_id)
    if not base_model:
        # 注册基础模型
        try:
            # 计算模型大小
            size = 0
            if os.path.exists(llm_path):
                if os.path.isdir(llm_path):
                    for dirpath, _, filenames in os.walk(llm_path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            size += os.path.getsize(fp)
                else:
                    size = os.path.getsize(llm_path)
            
            # 尝试从模型名称中提取参数量
            parameter_size = None
            model_name = os.path.basename(llm_path)
            
            # 常见参数量的正则表达式
            patterns = [
                r'(\d+)[Bb]',  # 匹配 7B, 14B 等
                r'(\d+(?:\.\d+)?)[\s-]*[Bb]illion'  # 匹配 7 Billion, 14-Billion 等
            ]
            
            for pattern in patterns:
                match = re.search(pattern, model_name)
                if match:
                    parameter_size = f"{match.group(1)}B"
                    break
            
            tags = ["base"]
            if parameter_size:
                tags.append(parameter_size)
            
            model_metadata = ModelMetadata(
                model_id=base_model_id,
                model_name=model_name,
                model_type="base",
                description=f"基础模型位于 {llm_path}",
                path=llm_path,
                created_at=datetime.now().isoformat(),
                size=size,
                parameter_size=parameter_size,
                tags=tags
            )
            model_library.register_model(model_metadata)
            print(f"已注册基础模型: {base_model_id}")
        except Exception as e:
            print(f"注册基础模型失败: {str(e)}")
    
    tuner = Tuner(tuning_mode, llm_path, dataset_path, experiment_name, tracking_uri)
    tuner.train_func()
    
    return None  # 返回新模型的ID


def main(args):
    # Set CUDA_VISIBLE_DEVICES environment variable
    os.environ["CUDA_VISIBLE_DEVICES"] = args.devices
    
    tuner = Tuner(
        args.tuning_mode, 
        args.llm_path,
        args.dataset_path,
        args.experiment_name, 
        args.tracking_uri
    )
    tuner.train_func()
    
    print("LLM tuning is done.")


if __name__ == "__main__":
    args = parse_args()
    main(args)