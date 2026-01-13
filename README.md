# 宿舍预定系统 - 后端

## 项目概述

宿舍预定系统是一个基于Python Flask的Web应用，用于管理学生宿舍预定、选宿倾向和AI推荐等功能。

## 技术栈

- **后端框架**: Python Flask
- **API规范**: OpenAPI 3.0
- **数据库**: MySQL
- **ORM**: MySQL Connector/Python
- **AI推荐**: Volcengine Ark SDK
- **认证**: JWT

## 安装与设置

### 1. 克隆项目

```bash
git clone http://mygitlab.quwancode.com/120231080609/api.dorm_reservation_system.git
cd dorm_reservation_system/back-end
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv env_python_final_assignment
.nv_python_final_assignment\Scripts\activate

# Linux/macOS
python3 -m venv env
source env/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 数据库配置

1. 确保MySQL已安装并运行
2. 创建数据库：
   ```sql
   CREATE DATABASE dorm_reservation_system;
   ```
3. 导入数据库结构：
   ```bash
   mysql -u root -p dorm_reservation_system < dorm_reservation_system.sql
   ```
4. 修改数据库连接配置（如需要）：
   - 编辑 `database.py` 文件中的数据库连接参数

### 5. 配置AI API密钥

1. 编辑 `ai_recommendation.py` 文件
2. 设置您的Volcengine API密钥：
   ```python
   client = VolcengineArk(api_key="YOUR_API_KEY")
   ```

## 运行应用

### 开发环境

```bash
# Windows
.nv_python_final_assignment\Scripts\activate
python -m connexion run openapi.yaml --port 8080

# Linux/macOS
source env/bin/activate
python -m connexion run openapi.yaml --port 8080
```

### 生产环境

```bash
# Windows
env_python_final_assignment\Scripts\python.exe app.py > server.log 2>&1 &

# Linux/macOS
nohup python app.py > server.log 2>&1 &
```

## API文档

应用启动后，API文档可通过以下URL访问：
- **Swagger UI**: http://localhost:8080/ui
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## 项目结构

```
back-end/
├── controllers/              # 控制器
│   └── default_controller.py # 主要API实现
├── models/                   # 数据模型
│   ├── __init__.py
│   └── *.py                  # 自动生成的模型类
├── ai_recommendation.py       # AI推荐模块
├── app.py                     # 应用入口
├── database.py                # 数据库连接
├── db.py                      # 数据库操作
├── dorm_reservation_system.sql # 数据库结构
├── openapi.yaml               # API规范
└── requirements.txt           # 依赖列表
```

## 核心功能

### 1. 学生管理
- 学生登录
- 选宿倾向管理
- 推荐宿舍查看

### 2. 宿舍管理
- 楼栋信息管理
- 楼层信息管理
- 房间信息管理

### 3. 预定管理
- 床位预定
- 预定状态管理
- 预定历史记录

### 4. AI推荐系统
- 基于选宿倾向的智能推荐
- 使用Volcengine Ark API

## API端点

### 学生相关

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/students/login` | POST | 学生登录 |
| `/api/students/information` | GET | 获取选宿倾向和推荐宿舍 |
| `/api/students/information` | PUT | 更新选宿倾向 |
| `/api/students/recommend-dormitory` | PUT | 获取AI推荐宿舍 |

### 宿舍相关

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/buildings` | GET | 获取楼栋列表 |
| `/api/floors` | GET | 获取楼层列表 |
| `/api/rooms` | GET | 获取房间列表 |
| `/api/rooms/{room_id}` | GET | 获取房间详情 |
| `/api/rooms/{room_id}/beds` | GET | 获取床位列表 |

### 预定相关

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/bookings` | POST | 提交预定 |
| `/api/bookings/cancel` | POST | 取消预定 |
| `/api/bookings/student/{student_id}` | GET | 获取预定历史 |

## 数据库结构

主要表结构：

1. `students` - 学生信息表
2. `buildings` - 楼栋信息表
3. `floors` - 楼层信息表
4. `rooms` - 房间信息表
5. `beds` - 床位信息表
6. `bookings` - 预定信息表

## AI推荐系统

### 功能说明

AI推荐系统基于学生的选宿倾向，通过Volcengine Ark API为学生推荐最适合的宿舍。

### 实现原理

1. 收集学生的选宿倾向
2. 从数据库中获取所有可用宿舍信息
3. 调用Volcengine Ark API进行智能推荐
4. 返回推荐结果

### 配置说明

在 `ai_recommendation.py` 中配置API密钥：

```python
# 配置Volcengine API密钥
client = VolcengineArk(api_key="YOUR_API_KEY")
```

## 开发指南

### 代码风格
- 使用PEP 8规范
- 函数注释使用docstring
- 变量命名清晰

### 调试

启用调试模式：

```bash
python -m connexion run openapi.yaml --port 8080 --debug
```

## 生产部署

### 环境要求

- Python 3.8+
- MySQL 5.7+
- 足够的内存和存储空间

### 部署步骤

1. 安装依赖
2. 配置数据库
3. 设置环境变量
4. 启动应用

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 监控与日志

应用日志默认输出到 `server.log`，建议配置日志轮换。

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证数据库连接参数

2. **API返回500错误**
   - 查看服务器日志
   - 检查数据库查询语句

3. **AI推荐失败**
   - 检查API密钥配置
   - 验证网络连接


