from volcenginesdkarkruntime import Ark
import os
from pydantic import BaseModel  # 用于定义响应解析模型

# 初始化方舟SDK客户端
client = Ark(
    # 从环境变量获取方舟API Key（需提前设置环境变量）
    api_key=os.getenv("ARK_API_KEY"),
)

# 定义最终响应模型（包含分步过程和最终答案）
class AdviseResponse(BaseModel):
    dormitory_number: str

# 调用AI推荐宿舍
def recommend_dormitory(student_id, student_information, available_rooms):
    """
    根据学生选宿倾向推荐宿舍
    
    参数:
    student_id: 学生ID
    student_information: 学生选宿倾向
    available_rooms: 可用宿舍列表，包含宿舍ID、类型、已选学生人数和他们的选宿倾向
    
    返回:
    推荐的宿舍ID
    """
    # 构建用户消息内容
    user_content = f"学生选宿倾向：{student_information}\n\n"
    
    # 添加可用宿舍信息
    user_content += "可用宿舍列表：\n"
    for room in available_rooms:
        user_content += f"宿舍ID：{room['room_id']}，类型：{room['room_type']}，已选人数：{room['selected_count']}\n"
        if room['selected_students']:
            user_content += f"  已选学生选宿倾向：\n"
            for student in room['selected_students']:
                user_content += f"    - {student['information']}\n"
    
    # 调用方舟模型生成响应（自动解析为指定模型）
    completion = client.beta.chat.completions.parse(
        model="doubao-seed-1-8-251228",
        messages=[
            {"role": "system", "content": "你现在要根据该同学的选宿倾向为一位同学推荐一个宿舍"},
            {"role": "user", "content": user_content} 
        ],
        response_format=AdviseResponse,  # 指定响应解析模型
        extra_body={
             "thinking": {
                 "type": "disabled" # 不使用深度思考能力
             }
         }
    )
    
    # 提取解析后的结构化响应
    resp = completion.choices[0].message.parsed
    
    # 返回推荐的宿舍ID
    return resp.dormitory_number