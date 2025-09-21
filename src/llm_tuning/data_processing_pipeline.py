import json
import asyncio
from pathlib import Path
import os
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
from onesim.models import get_model_manager, get_model, UserMessage


async def async_llm_call(prompt, model_name="gpt-4o-mini"):
    """
    Asynchronously call the LLM model with a single prompt
    """
    # Get a configured model
    model = get_model(model_name=model_name)
    
    # Create message
    user_msg = UserMessage(prompt)
    
    # Generate a response
    formatted_messages = model.format(user_msg)
    response = await model.acall(formatted_messages)
    
    # 减少打印长字符串，只打印重要信息
    prompt_summary = prompt[:100] + "..." if len(prompt) > 100 else prompt
    response_summary = response.text[:100] + "..." if len(response.text) > 100 else response.text
    print(f"LLM call: {model_name}, prompt length: {len(prompt)}, response length: {len(response.text)}")
    print(f"Response preview: {response_summary}")
    
    # Return the response text
    return response.text

async def call_llm_batch(prompts, model_config="gpt-4o-mini"):
    """
    Call the LLM model with a list of prompts and return the responses.
    
    Note: This function guarantees that the order of responses matches the order of input prompts.
    Each response at index i corresponds to the prompt at the same index i.
    """
    # Create the async function to process all prompts
    # async def process_all_prompts(): # No longer needed as we directly await gather
    #     tasks = [async_llm_call(prompt, model_config) for prompt in prompts]
    #     return await asyncio.gather(*tasks)

    # Run with retries
    while True:
        try:
            # Run the async function directly
            tasks = [async_llm_call(prompt, model_config) for prompt in prompts]
            # asyncio.gather() preserves the order of results to match the order of input tasks
            responses = await asyncio.gather(*tasks)
            print('Done!')
            return responses
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            print(f"Catching Exception {e}, Retrying...")
            await asyncio.sleep(1)
            continue

def load_data(file_path):
    """
    Load data from a JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def save_data(data, file_path):
    """
    Save data to a JSON file
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def verify_data(data, model_config="gpt-4o-mini"):
    """
    Verify the reliability of data items and score them from 1-10
    Skip items that already have a 'rating' score.
    """
    template = """Please act as a data quality verifier. You need to evaluate the reliability and quality of the following data item.
    Score the reliability from 1 to 5, where:
    - 1-2: Very unreliable (contains false information, logical contradictions, or harmful content)
    - 3: Somewhat reliable (contains minor inaccuracies or questionable statements)
    - 4-5: Highly reliable (factually accurate, logically sound, and helpful)
    
    Data item: {item}
    
    Your response should be ONLY a single number between 1 and 5, with no additional text.
    """
    
    # Filter out items that already have a rating score
    items_to_verify = []
    indices_to_verify = []
    
    for i, item in enumerate(data):
        if 'rating' not in item or item['rating'] == None or item['rating'] == 0:
            items_to_verify.append(item)
            indices_to_verify.append(i)
    
    # If all items already have ratings, return existing scores
    if not items_to_verify:
        print("All items already have rating scores. Skipping verification.")
        return [item.get('rating', 0) for item in data]
    
    # Generate prompts only for items that need verification
    prompts = [template.format(item=json.dumps(item, ensure_ascii=False, indent=4)) for item in items_to_verify]
    new_scores = await call_llm_batch(prompts, model_config)
    
    # Convert scores to integers with robust error handling
    processed_scores = []
    for score_text in new_scores:
        try:
            # 尝试直接解析为整数
            score = int(score_text.strip())
            # 确保分数在1-5范围内
            score = max(1, min(5, score))
            processed_scores.append(score)
        except ValueError:
            # 如果不是整数，尝试从文本中提取数字
            try:
                # 查找第一个数字
                numbers = re.findall(r'\d+', score_text)
                if numbers:
                    score = int(numbers[0])
                    # 确保分数在1-5范围内
                    score = max(1, min(5, score))
                    processed_scores.append(score)
                else:
                    # 如果没有找到数字，使用默认值5
                    print(f"Warning: Could not extract score from '{score_text}', using default score 5")
                    processed_scores.append(5)
            except Exception as e:
                # 如果出现任何错误，使用默认值5
                print(f"Error processing score: {e}, using default score 5")
                processed_scores.append(5)
    
    # Combine existing and new scores
    scores = [0] * len(data)  # Initialize with placeholder values
    
    # First, copy any existing scores
    for i, item in enumerate(data):
        if 'rating' in item:
            scores[i] = item['rating']
    
    # Then add new scores for items that were verified
    for i, idx in enumerate(indices_to_verify):
        scores[idx] = processed_scores[i]
    
    print(f"Verification completed. Verified {len(items_to_verify)} new items. Score distribution: {scores}")
    return scores

async def analyze_reasons(data, scores, threshold=None, model_config="gpt-4o-mini"):
    """
    Analyze reasons for low-scoring data items
    Skip items that already have a 'reason'
    """
    # Find indices of items that score below threshold AND don't already have a reason
    low_quality_indices = []

    if threshold is not None:
        for i, (item, score) in enumerate(zip(data, scores)):
            if score < threshold and ('reason' not in item or item['reason'] == None):
                low_quality_indices.append(i)
        
        if not low_quality_indices:
            print(f"No new data items to analyze (below threshold {threshold} without existing analysis)")
            # Return existing reasons in the expected format
            existing_reasons = []
            for i, item in enumerate(data):
                if 'reason' in item:
                    existing_reasons.append((i, item['reason']))
            return existing_reasons
    else:
        for i, (item, score) in enumerate(zip(data, scores)):
            if 'reason' not in item or item['reason'] == None:
                low_quality_indices.append(i)
    
    template = """Identify 2-3 main issues with this data item that affect its reliability:

    Data item: {item}
    
    List only the key issues using short bullet points.
    """
    
    low_quality_data = [data[i] for i in low_quality_indices]
    prompts = [template.format(item=json.dumps(item, ensure_ascii=False, indent=4)) for item in low_quality_data]
    reasons = await call_llm_batch(prompts, model_config)
    
    # Combine with existing reasons
    result_reasons = []
    
    # First add existing reasons
    for i, item in enumerate(data):
        if 'reason' in item and item['reason'] is not None:
            result_reasons.append((i, item['reason']))
    
    # Then add new reasons
    new_reasons = [(low_quality_indices[i], reasons[i]) for i in range(len(reasons))]
    result_reasons.extend(new_reasons)
    
    print(f"Reason analysis completed for {len(new_reasons)} new low-quality items")
    return result_reasons

async def refine_data(data, reason_analysis, model_config="gpt-4o-mini"):
    """
    Refine low-quality data items based on the reason analysis
    Skip items that already have a 'feedback'
    """
    if not reason_analysis:
        print("No data items to refine")
        return data
    
    template = """Please improve the following data item based on the issues identified below.
    
    Original data item: 
    {item}
    
    Issues to fix: {reason}
    
    Please address the issues listed above when creating an improved version.
    Provide ONLY the improved output content. Do not return the entire data item.
    """
    
    # Create a copy of the data to avoid modifying the original during iteration
    refined_data = data.copy()
    
    # Filter items that need refinement (have reasons but no feedback yet)
    indices_to_refine = []
    reasons_to_use = []
    
    for idx, reason in reason_analysis:
        if 'feedback' not in data[idx] or data[idx]['feedback'] == None:
            # The following item_copy block was unused and has been removed.
            # The actual item preparation for the LLM prompt happens later with item_for_template.
            indices_to_refine.append(idx)
            reasons_to_use.append(reason)
    
    if not indices_to_refine:
        print("All items with analysis already have feedback outputs. Skipping refinement.")
        return refined_data
    
    # Prepare prompts for refinement
    prompts = []
    
    for i, idx in enumerate(indices_to_refine):
        # Format the data item with proper indentation for better readability
        # 创建一个不包含reason字段的副本用于模板
        item_for_template = data[idx].copy()
        if 'reason' in item_for_template:
            # 临时移除reason字段，避免在显示数据项时重复显示reason
            del item_for_template['reason']
            
        formatted_item = json.dumps(item_for_template, ensure_ascii=False, indent=4)
        prompts.append(template.format(
            item=formatted_item,
            reason=reasons_to_use[i]
        ))
    
    # Get refined versions
    refined_outputs = await call_llm_batch(prompts, model_config)
    
    print(f"refined_outputs: {refined_outputs}")
    print(f"indices_to_refine: {indices_to_refine}")
    # Update the data with refined versions
    for i, refined_output in enumerate(refined_outputs):
        refined_data[indices_to_refine[i]]['feedback'] = refined_output
        refined_data[indices_to_refine[i]]['reason'] = reasons_to_use[i]
    
    print(f"Refinement completed for {len(refined_outputs)} new items")
    return refined_data

def find_config_path():
    """查找模型配置文件"""
    # 从可能的相对路径查找
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    potential_paths = [
        os.path.join(project_root, "config", "llm", "openai_model_config.json"),
        os.path.join(project_root, "src", "config", "llm", "openai_model_config.json"),
        os.path.join(current_dir, "..", "..", "config", "llm", "openai_model_config.json")
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            return path
    
    return None

async def main(input_file, output_file=None, threshold=8, model_config="gpt-4o"):
    """
    Main pipeline function that orchestrates the entire process
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to save the processed data (如果为None，将基于input_file自动生成)
        threshold: Quality threshold below which data items need refinement
        model_config: Configuration name for the model to use (e.g. "gpt-4o-mini")
    """
    # 如果output_file未提供，则根据input_file自动生成
    if output_file is None:
        input_basename = os.path.basename(input_file)
        output_dir = os.path.dirname(input_file)
        output_file = os.path.join(output_dir, f"processed_{input_basename}")

    # 加载模型配置
    config_path = find_config_path()
    model_manager = get_model_manager()
    
    if config_path:
        try:
            model_manager.load_model_configs(config_path)
            print(f"已加载模型配置: {config_path}")
        except Exception as e:
            print(f"警告: 加载模型配置失败: {e}")
            print("将尝试使用默认模型配置")
    else:
        print("未找到模型配置文件，将尝试使用默认模型配置")

    print(f"开始数据处理流程...")
    print(f"使用模型配置: {model_config}")
    print(f"从 {input_file} 加载数据")
    
    # 加载数据
    data = load_data(input_file)
    print(f"已加载 {len(data)} 条数据")
    
    # 统计已处理项目
    existing_scores = sum(1 for item in data if 'rating' in item)
    existing_analyses = sum(1 for item in data if 'reason' in item)
    existing_refinements = sum(1 for item in data if 'feedback' in item)
    
    if existing_scores > 0 or existing_analyses > 0 or existing_refinements > 0:
        print(f"发现已处理数据: {existing_scores} 已评分, {existing_analyses} 已分析, {existing_refinements} 已改进")
    
    # 步骤1: 验证数据质量
    print("步骤1: 验证数据质量...")
    scores = await verify_data(data, model_config)
    
    # 将评分添加到数据
    for i in range(len(data)):
        if 'rating' not in data[i] or data[i]['rating'] == None:
            data[i]['rating'] = scores[i]
    
    # 步骤2: 分析低质量数据原因
    print(f"步骤2: 分析评分低于 {threshold} 的数据项...")
    reason_analysis = await analyze_reasons(data, scores, threshold, model_config)
    
    # 将分析原因添加到数据
    for idx, reason in reason_analysis:
        if 'reason' not in data[idx]:
            data[idx]['reason'] = reason
    
    # 步骤3: 改进低质量数据
    print("步骤3: 改进低质量数据项...")
    refined_data = await refine_data(data, reason_analysis, model_config)
    
    # 保存处理后的数据
    print(f"保存处理后的数据到 {output_file}")
    save_data(refined_data, output_file)
    
    # 统计新处理的项目
    total_scores = sum(1 for item in refined_data if 'rating' in item)
    total_analyses = sum(1 for item in refined_data if 'reason' in item)
    total_refinements = sum(1 for item in refined_data if 'feedback' in item)
    
    new_scores = total_scores - existing_scores
    new_analyses = total_analyses - existing_analyses
    new_refinements = total_refinements - existing_refinements
    
    print("数据处理流程成功完成!")
    print(f"摘要: {new_scores} 新评分, {new_analyses} 新分析, {new_refinements} 新改进")
    print(f"总计: {total_scores} 已评分, {total_analyses} 已分析, {total_refinements} 已改进")
    
    return refined_data

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="处理决策数据并改进低质量样本")
    parser.add_argument("--input", "-i", type=str, required=True, help="输入数据文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出数据文件路径")
    parser.add_argument("--threshold", "-t", type=int, default=8, help="质量阈值，低于此值的数据将被改进")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o-mini", help="使用的模型配置")
    
    args = parser.parse_args()
    
    asyncio.run(
        main(
            input_file=args.input,
            output_file=args.output,
            threshold=args.threshold,
            model_config=args.model
        )
    ) 