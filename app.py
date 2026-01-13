import connexion

# 创建Connexion应用
app = connexion.FlaskApp(__name__, specification_dir='.')

# 添加API规范，降低严格验证要求，并配置CORS
app.add_api(
    'openapi.yaml', 
    strict_validation=False,  # 降低严格验证要求
    validate_responses=False,  # 关闭响应验证
    options={
        'cors': True,  # 启用CORS
        'cors_origin': '*'  # 允许所有源
    }
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
