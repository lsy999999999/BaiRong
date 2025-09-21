"""
示例代码：展示如何从外部调用tune_llm模块进行LLM微调
"""

from codes.tune_llm import run_tuning

def main():
    # 示例1：使用最简单的方式调用，只指定必要参数
    print("示例1：使用最简单的方式调用")
    run_tuning(
        tuning_mode="sft",
        llm_path="/path/to/your/model",
    )
    
    # 示例2：自定义所有参数
    print("\n示例2：自定义所有参数")
    run_tuning(
        tuning_mode="ppo", 
        llm_path="/path/to/your/model",
        experiment_name="custom_experiment",
        tracking_uri="./custom_mlruns",
        devices="0",
    )

if __name__ == "__main__":
    main() 