from datetime import datetime
from decimal import Decimal
import mysql.connector
from mysql.connector import pooling
from database import DB_CONFIG

connection_pool = pooling.MySQLConnectionPool(
    pool_name="dorm_pool",
    pool_size=5,
    pool_reset_session=True,
    **DB_CONFIG
)

def get_db_connection():
    return connection_pool.get_connection()

def dict_to_response_data(obj):
    """将数据库查询结果转换为响应数据格式"""
    if obj is None:
        return None
    return dict(obj)

def format_datetime(obj):
    """格式化datetime对象为字符串"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return obj

def decimal_to_float(obj):
    """将Decimal转换为float"""
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

def log_operation(conn, operator_type, operator_id, operation, target_type, target_id, ip_address, operation_result):
    """记录操作日志
    
    Args:
        conn: 数据库连接对象
        operator_type: 操作者类型 (admin/student)
        operator_id: 操作者ID
        operation: 操作内容
        target_type: 操作对象类型 (student/room/booking/building/floor)
        target_id: 操作对象ID
        ip_address: 操作IP地址
        operation_result: 操作结果 (success/fail)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO operation_logs 
            (operator_type, operator_id, operation, target_type, target_id, ip_address, operation_result) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (operator_type, operator_id, operation, target_type, target_id, ip_address, operation_result)
        )
        conn.commit()
    except Exception as e:
        # 日志记录失败不影响主业务
        print(f"日志记录失败: {e}")
    finally:
        cursor.close()