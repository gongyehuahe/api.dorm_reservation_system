import connexion
from db import get_db_connection, log_operation
import bcrypt
from ai_recommendation import recommend_dormitory

# 密码哈希和验证辅助函数
def hash_password(password):
    """对密码进行哈希加密"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    """验证密码是否匹配"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def api_check_login_time():
    """检查当前时间是否在可登录时间范围内"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询当前时间是否在任意一条预约时间记录的范围内
        cursor.execute(
            "SELECT id FROM reservation_periods WHERE NOW() BETWEEN start_time AND end_time LIMIT 1"
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return {
                "success": True,
                "message": "当前时间在可登录范围内",
                "data": {
                    "allow_login": True
                }
            }, 200
        else:
            return {
                "success": True,
                "message": "当前时间不在可登录范围内",
                "data": {
                    "allow_login": False
                }
            }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_students_login_post(body):
    """学生登录"""
    try:
        student_id = body.get('student_id')
        password = body.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询学生信息
        cursor.execute("SELECT s.id, s.student_id, s.name, m.major_name AS major, s.grade, s.gender, s.password FROM students s JOIN majors m ON s.major_id = m.id WHERE s.student_id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学号或密码错误"
            }, 401
        
        # 验证密码
        if not verify_password(password, student['password']):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学号或密码错误"
            }, 401
        
        cursor.close()
        conn.close()
        
        # 将英文性别转换为中文
        gender_map = {
            'M': '男',
            'F': '女'
        }
        student_gender = gender_map.get(student['gender'], student['gender'])
        
        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "user_info": {
                    "student_id": student['id'],
                    "student_number": student['student_id'],
                    "name": student['name'],
                    "major": student['major'],
                    "grade": student['grade'],
                    "gender": student_gender
                },
                "token": f"student_{student['id']}_token"
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_buildings_get(gender=None):
    """获取楼栋列表"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 确保学生只能看到自己性别对应的宿舍楼
        # 严格按性别筛选，不允许返回所有楼栋
        
        # 处理gender参数，转换为数据库使用的格式
        target_gender = None
        
        # 检查gender是否有效，不是None或undefined字符串
        if gender is not None and gender != 'undefined' and gender != '':
            # 将中文性别转换为英文，以便数据库查询
            gender_map = {
                '男': 'M',
                '女': 'F',
                'm': 'M',
                'f': 'F'
            }
            
            # 转换性别参数，处理中文和英文性别
            if gender in gender_map:
                target_gender = gender_map[gender]
            elif gender.upper() in ['M', 'F']:
                # 直接匹配英文大写性别
                target_gender = gender.upper()
        
        if target_gender in ['M', 'F']:
            # 严格按性别筛选，只返回匹配学生性别的宿舍楼，同时获取宿舍类型、面积、价格和设施
            cursor.execute("""
                SELECT DISTINCT b.id as building_id, b.name, b.gender, b.introduction,
                       rt.id as room_type_id, rt.introduction as room_type,
                       rt.area, rt.price, rt.bed_count,
                       rt.sketch_image, rt.real_image,
                       GROUP_CONCAT(DISTINCT f.facility_name SEPARATOR ', ') as facilities
                FROM buildings b
                LEFT JOIN floors f2 ON b.id = f2.building_id
                LEFT JOIN rooms r ON f2.id = r.floor_id
                LEFT JOIN room_types rt ON r.room_type_id = rt.id
                LEFT JOIN rooms_facilities rf ON rt.id = rf.room_type_id
                LEFT JOIN facilities f ON rf.facility_id = f.id
                WHERE b.gender = %s
                GROUP BY b.id, b.name, b.gender, b.introduction, rt.id, rt.introduction, rt.area, rt.price, rt.bed_count, rt.sketch_image, rt.real_image
            """, (target_gender,))
        else:
            # 如果没有有效性别参数，返回空列表，不允许学生看到所有楼栋
            cursor.execute("""
                SELECT DISTINCT b.id as building_id, b.name, b.gender, b.introduction,
                       rt.id as room_type_id, rt.introduction as room_type,
                       rt.area, rt.price, rt.bed_count,
                       rt.sketch_image, rt.real_image,
                       GROUP_CONCAT(DISTINCT f.facility_name SEPARATOR ', ') as facilities
                FROM buildings b
                LEFT JOIN floors f2 ON b.id = f2.building_id
                LEFT JOIN rooms r ON f2.id = r.floor_id
                LEFT JOIN room_types rt ON r.room_type_id = rt.id
                LEFT JOIN rooms_facilities rf ON rt.id = rf.room_type_id
                LEFT JOIN facilities f ON rf.facility_id = f.id
                WHERE 1=0
                GROUP BY b.id, b.name, b.gender, b.introduction, rt.id, rt.introduction, rt.area, rt.price, rt.bed_count, rt.sketch_image, rt.real_image
            """)
        
        building_data = cursor.fetchall()
        
        # 将数据按楼栋分组，每个楼栋包含多个宿舍类型
        buildings = {}
        for item in building_data:
            building_id = item['building_id']
            if building_id not in buildings:
                buildings[building_id] = {
                    'building_id': building_id,
                    'name': item['name'],
                    'gender': '男' if item['gender'] == 'M' else '女',
                    'introduction': item['introduction'],
                    'room_types': []
                }
            
            if item['room_type_id']:
                buildings[building_id]['room_types'].append({
                    'room_type_id': item['room_type_id'],
                    'room_type': item['room_type'],
                    'area': float(item['area']),
                    'price': float(item['price']),
                    'bed_count': item['bed_count'],
                    'facilities': item['facilities'] or '',
                    'sketch_image': item['sketch_image'],
                    'real_image': item['real_image']
                })
        
        # 转换为列表格式
        buildings = list(buildings.values())
        
        return {
            "success": True,
            "message": "获取成功",
            "data": buildings
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_floors_get(building_id=None):
    """获取楼层列表"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 处理building_id参数
        if building_id == 'undefined' or building_id is None:
            return {
                "success": False,
                "message": "楼栋ID不能为空"
            }, 400
        
        # 查询指定楼栋的所有楼层，并返回正确的字段名
        cursor.execute("SELECT id as floor_id, building_id, floor_number, image FROM floors WHERE building_id = %s ORDER BY floor_number", (building_id,))
        floors = cursor.fetchall()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": floors
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_rooms_get(floor_id=None, student_id=None):
    """获取房间列表，添加专业限制"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 处理floor_id参数
        if floor_id == 'undefined' or floor_id is None:
            return {
                "success": False,
                "message": "楼层ID不能为空"
            }, 400
        
        # 查询指定楼层的所有房间，关联房间类型表获取房间类型、价格、面积和设施
        cursor.execute("""
            SELECT r.id as room_id, r.room_number, 
                   ft.introduction as room_type, ft.price, ft.area, r.status,
                   ft.sketch_image as room_type_sketch_image, ft.real_image as room_type_real_image,
                   GROUP_CONCAT(DISTINCT f.facility_name SEPARATOR ', ') as facilities
            FROM rooms r
            JOIN room_types ft ON r.room_type_id = ft.id
            LEFT JOIN rooms_facilities rf ON ft.id = rf.room_type_id
            LEFT JOIN facilities f ON rf.facility_id = f.id
            WHERE r.floor_id = %s
            GROUP BY r.id, r.room_number, ft.introduction, ft.price, ft.area, r.status, ft.sketch_image, ft.real_image
            ORDER BY r.room_number
        """, (floor_id,))
        rooms = cursor.fetchall()
        
        # 为床位数查询创建新的游标
        beds_cursor = conn.cursor(dictionary=True)
        
        # 获取学生专业ID（如果提供了student_id）
        student_major_id = None
        if student_id:
            cursor.execute("SELECT major_id FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()
            if student:
                student_major_id = student['major_id']
        
        # 为每个房间计算可用床位数和检查专业限制
        for room in rooms:
            # 查询该房间的总床位数
            beds_cursor.execute("SELECT COUNT(*) as total_beds FROM beds WHERE room_id = %s", (room['room_id'],))
            room['total_beds'] = beds_cursor.fetchone()['total_beds']
            
            # 查询该房间的可用床位数
            beds_cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (room['room_id'],))
            room['available_beds'] = beds_cursor.fetchone()['available_beds']
            
            # 确保设施字段存在
            if 'facilities' not in room:
                room['facilities'] = ''
            
            # 检查房间的专业限制
            if student_major_id:
                # 查询房间的专业限制
                cursor.execute("SELECT major_id FROM room_majors WHERE room_id = %s", (room['room_id'],))
                room_majors = cursor.fetchall()
                
                # 检查专业限制
                if room_majors:  # 有专业限制
                    # 检查学生专业是否在房间允许的专业列表中
                    major_allowed = any(rm['major_id'] == student_major_id for rm in room_majors)
                    
                    # 优先处理房间状态
                    if room['status'] == '不可预定' or room['status'] == '已被预定':
                        # 如果房间状态为不可预定或已被预定，直接使用原状态
                        room['display_status'] = room['status']
                    elif not major_allowed:
                        # 专业不匹配，修改显示状态为不可预定
                        room['display_status'] = '不可预定'
                    else:
                        # 专业匹配且房间状态可用，保持原状态
                        room['display_status'] = room['status']
                else:  # 无专业限制
                    # 没有专业限制，直接使用房间原状态
                    room['display_status'] = room['status']
            else:
                # 没有提供student_id，使用原状态
                room['display_status'] = room['status']
        
        # 关闭床位数查询游标
        beds_cursor.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": rooms
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_rooms_room_id_get(room_id, student_id=None):
    """获取房间详情，添加专业限制"""
    conn = None
    cursor = None
    beds_cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 处理room_id参数
        if room_id == 'undefined' or room_id is None:
            return {
                "success": False,
                "message": "房间ID不能为空"
            }, 400
        
        # 查询指定房间的详情，关联房间类型表获取相关信息
        cursor.execute("""
            SELECT r.id as room_id, r.room_number, r.floor_id, r.room_type_id, r.status,
                   rt.introduction as room_type, rt.price, rt.area, rt.bed_count,
                   rt.sketch_image as room_type_sketch_image, rt.real_image as room_type_real_image,
                   rt.sketch_image as layout_image,
                   GROUP_CONCAT(DISTINCT f.facility_name SEPARATOR ', ') as facilities
            FROM rooms r
            JOIN room_types rt ON r.room_type_id = rt.id
            LEFT JOIN rooms_facilities rf ON rt.id = rf.room_type_id
            LEFT JOIN facilities f ON rf.facility_id = f.id
            WHERE r.id = %s
            GROUP BY r.id, r.room_number, r.floor_id, r.room_type_id, r.status,
                     rt.introduction, rt.price, rt.area, rt.bed_count,
                     rt.sketch_image, rt.real_image
        """, (room_id,))
        room = cursor.fetchone()
        
        if not room:
            return {
                "success": False,
                "message": "房间不存在"
            }, 404
        
        # 为房间计算可用床位数
        beds_cursor = conn.cursor(dictionary=True)
        # 查询该房间的总床位数
        beds_cursor.execute("SELECT COUNT(*) as total_beds FROM beds WHERE room_id = %s", (room_id,))
        room['total_beds'] = beds_cursor.fetchone()['total_beds']
        
        # 查询该房间的可用床位数
        beds_cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (room_id,))
        room['available_beds'] = beds_cursor.fetchone()['available_beds']
        
        # 确保设施字段存在
        if 'facilities' not in room:
            room['facilities'] = ''
        
        # 检查专业限制
        if student_id:
            # 获取学生专业ID
            cursor.execute("SELECT major_id FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()
            if student:
                student_major_id = student['major_id']
                
                # 查询房间的专业限制
                cursor.execute("SELECT major_id FROM room_majors WHERE room_id = %s", (room_id,))
                room_majors = cursor.fetchall()
                
                # 检查专业限制
                if room_majors:  # 有专业限制
                    # 检查学生专业是否在房间允许的专业列表中
                    major_allowed = any(rm['major_id'] == student_major_id for rm in room_majors)
                    
                    # 优先处理房间状态
                    if room['status'] == '不可预定' or room['status'] == '已被预定':
                        # 如果房间状态为不可预定或已被预定，直接使用原状态
                        room['display_status'] = room['status']
                    elif not major_allowed:
                        # 专业不匹配，修改显示状态为不可预定
                        room['display_status'] = '不可预定'
                    else:
                        # 专业匹配且房间状态可用，保持原状态
                        room['display_status'] = room['status']
                else:  # 无专业限制
                    # 没有专业限制，直接使用房间原状态
                    room['display_status'] = room['status']
            else:
                # 学生不存在，修改显示状态为不可预定
                room['display_status'] = '不可预定'
        else:
            # 没有提供student_id，使用原状态
            room['display_status'] = room['status']
        
        return {
            "success": True,
            "message": "获取成功",
            "data": room
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if beds_cursor:
            beds_cursor.close()
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_rooms_room_id_beds_get(room_id, student_id=None):
    """获取床位列表，添加专业限制"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询指定房间的所有床位，关联房间类型表获取价格信息
        cursor.execute("""
            SELECT b.id as bed_id, b.bed_number, b.status, rt.price
            FROM beds b
            JOIN rooms r ON b.room_id = r.id
            JOIN room_types rt ON r.room_type_id = rt.id
            WHERE b.room_id = %s
            ORDER BY b.bed_number
        """, (room_id,))
        beds = cursor.fetchall()
        
        # 检查专业限制
        if student_id:
            # 获取学生专业ID
            cursor.execute("SELECT major_id FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()
            if student:
                student_major_id = student['major_id']
                
                # 查询房间的专业限制
                cursor.execute("SELECT major_id FROM room_majors WHERE room_id = %s", (room_id,))
                room_majors = cursor.fetchall()
                
                # 查询房间状态
                cursor.execute("SELECT status FROM rooms WHERE id = %s", (room_id,))
                room_status = cursor.fetchone()['status']
                
                # 检查专业限制
                if room_majors:  # 有专业限制
                    # 检查学生专业是否在房间允许的专业列表中
                    major_allowed = any(rm['major_id'] == student_major_id for rm in room_majors)
                    
                    # 优先处理房间状态
                    if room_status == '不可预定' or room_status == '已被预定':
                        # 如果房间状态为不可预定或已被预定，修改所有床位的显示状态
                        for bed in beds:
                            bed['display_status'] = room_status
                    elif not major_allowed:
                        # 专业不匹配，修改所有床位的显示状态为不可预定
                        for bed in beds:
                            bed['display_status'] = '不可预定'
                    else:
                        # 专业匹配且房间状态可用，保持床位原状态
                        for bed in beds:
                            bed['display_status'] = bed['status']
                else:  # 无专业限制
                    # 没有专业限制，根据房间原状态决定床位显示状态
                    if room_status == '不可预定' or room_status == '已被预定':
                        # 如果房间状态为不可预定或已被预定，使用房间状态
                        for bed in beds:
                            bed['display_status'] = room_status
                    else:
                        # 房间状态可用，保持床位原状态
                        for bed in beds:
                            bed['display_status'] = bed['status']
            else:
                # 学生不存在，修改所有床位的显示状态为不可预定
                for bed in beds:
                    bed['display_status'] = '不可预定'
        else:
            # 没有提供student_id，使用原状态
            for bed in beds:
                bed['display_status'] = bed['status']
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": beds
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_bookings_post(body):
    """提交预定"""
    conn = None
    cursor = None
    try:
        # 添加调试日志
        print(f"预定请求参数: {body}")
        
        # 获取请求参数
        student_id = body.get('student_id')
        bed_id = body.get('bed_id')
        
        # 验证参数
        if not student_id or not bed_id:
            print("参数为空: student_id={}, bed_id={}".format(student_id, bed_id))
            return {
                "success": False,
                "message": "学生ID和床位ID不能为空"
            }, 400
        
        # 转换参数类型
        try:
            student_id = int(student_id)
            bed_id = int(bed_id)
        except (ValueError, TypeError):
            print("参数类型错误: student_id={}, bed_id={}".format(student_id, bed_id))
            return {
                "success": False,
                "message": "学生ID和床位ID必须是整数"
            }, 400
        
        print(f"处理预定请求: student_id={student_id}, bed_id={bed_id}")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        print("数据库连接成功")
        
        # 关闭自动提交，开始事务
        conn.autocommit = False
        print("事务开始（关闭自动提交）")
        
        # 1. 检查床位是否存在且可用
        cursor.execute("SELECT id, room_id, status FROM beds WHERE id = %s", (bed_id,))
        bed = cursor.fetchone()
        print(f"床位查询结果: {bed}")
        
        if not bed:
            conn.rollback()
            print("床位不存在")
            return {
                "success": False,
                "message": "床位不存在"
            }, 404
        
        if bed['status'] != '可预定':
            conn.rollback()
            print(f"床位不可预定，当前状态: {bed['status']}")
            return {
                "success": False,
                "message": "床位不可预定"
            }, 400
        
        room_id = bed['room_id']
        print(f"房间ID: {room_id}")
        
        # 2. 检查学生是否存在
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        print(f"学生查询结果: {student}")
        
        if not student:
            conn.rollback()
            print("学生不存在")
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 3. 检查学生所有预订记录，只有无记录或全部为已取消/已离开时才允许预定
        cursor.execute("SELECT booking_status FROM bookings WHERE student_id = %s", (student_id,))
        all_bookings = cursor.fetchall()
        print(f"所有预定记录检查结果: {all_bookings}")
        
        if all_bookings:
            # 检查是否存在未取消且未离开的记录
            for booking in all_bookings:
                status_stripped = booking['booking_status'].replace(' ', '')
                if status_stripped != '已取消' and status_stripped != '已离开':
                    conn.rollback()
                    print("学生存在未取消或已入住的预定记录，不允许重复预定")
                    return {
                        "success": False,
                        "message": "学生存在未取消或已入住的预定记录，不允许重复预定"
                    }, 400
        
        # 4. 在 bookings 表中新增记录
        cursor.execute("""
            INSERT INTO bookings (student_id, bed_id, booking_status, created_at, updated_at)
            VALUES (%s, %s, '已预定', NOW(), NOW())
        """, (student_id, bed_id))
        
        booking_id = cursor.lastrowid
        print(f"插入预定记录成功，booking_id: {booking_id}")
        
        # 5. 在 beds 表中更新状态为"已被预定"
        cursor.execute("UPDATE beds SET status = '已被预定' WHERE id = %s", (bed_id,))
        print(f"更新床位状态成功，受影响行数: {cursor.rowcount}")
        
        # 6. 检查房间剩余床位数
        cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (room_id,))
        available_beds = cursor.fetchone()['available_beds']
        print(f"房间剩余床位数: {available_beds}")
        
        # 7. 如果剩余床位数为0，更新房间状态为"已被预定"
        if available_beds == 0:
            cursor.execute("UPDATE rooms SET status = '已被预定' WHERE id = %s", (room_id,))
            print(f"更新房间状态为已被预定，受影响行数: {cursor.rowcount}")
        
        # 提交事务
        conn.commit()
        print("事务提交成功")
        
        return {
            "success": True,
            "message": "预定成功",
            "data": {
                "booking_id": booking_id
            }
        }, 200
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_bookings_student_student_id_get(student_id, page=1, page_size=10):
    """获取学生预定历史"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 添加调试日志
        print(f"API请求: student_id={student_id}, page={page}, page_size={page_size}")
        
        # 将student_id转换为整数类型，因为路径参数是字符串
        student_id = int(student_id)
        # 确保page和page_size也是整数
        page = int(page)
        page_size = int(page_size)
        
        # 添加调试日志
        print(f"转换后参数: student_id={student_id}, page={page}, page_size={page_size}")
        
        # 计算分页偏移量
        offset = (page - 1) * page_size
        
        # 测试简单查询，不使用JOIN，确保能获取到基本预订记录
        simple_query = "SELECT * FROM bookings WHERE student_id = %s"
        cursor.execute(simple_query, (student_id,))
        simple_result = cursor.fetchall()
        print(f"简单查询结果: {simple_result}")
        
        # 查询学生预定记录，先获取基础预订信息
        cursor.execute("""
            SELECT bk.id as booking_id,
                   bk.booking_status as status,
                   bk.created_at as booking_time,
                   bk.updated_at as update_time,
                   bk.student_id,
                   bk.bed_id
            FROM bookings bk
            WHERE bk.student_id = %s
            ORDER BY bk.created_at DESC
            LIMIT %s OFFSET %s
        """, (student_id, page_size, offset))
        
        bookings = cursor.fetchall()
        print(f"分页查询结果: {bookings}")
        
        # 查询总记录数
        cursor.execute("SELECT COUNT(*) as total FROM bookings WHERE student_id = %s", (student_id,))
        total = cursor.fetchone()['total']
        print(f"总记录数: {total}")
        
        # 处理每条预订记录，获取关联信息
        for booking in bookings:
            # 查询床位信息
            cursor.execute("""
                SELECT bd.bed_number, r.room_number, f.floor_number, b.name as building_name
                FROM beds bd
                JOIN rooms r ON bd.room_id = r.id
                JOIN floors f ON r.floor_id = f.id
                JOIN buildings b ON f.building_id = b.id
                WHERE bd.id = %s
            """, (booking['bed_id'],))
            bed_info = cursor.fetchone() or {}
            
            # 添加关联字段
            booking['bed_number'] = bed_info.get('bed_number', 0)
            booking['room_number'] = bed_info.get('room_number', '')
            booking['building_name'] = bed_info.get('building_name', '')
            booking['floor_number'] = bed_info.get('floor_number', 0)
            
            # 组合房间名称
            booking['roomName'] = f"{bed_info.get('building_name', '')}{bed_info.get('room_number', '')}"
            # 查询房间类型和价格信息
            cursor.execute("""
                SELECT rt.price, rt.bed_count
                FROM rooms r
                JOIN room_types rt ON r.room_type_id = rt.id
                WHERE r.id = (SELECT room_id FROM beds WHERE id = %s)
            """, (booking['bed_id'],))
            room_info = cursor.fetchone() or {}
            # 使用从数据库获取的实际价格
            booking['amount'] = room_info.get('price', 0.0)
            # 使用bed_count构建房间类型名称，如"4人间"、"6人间"
            booking['room_type'] = f"{room_info.get('bed_count', 0)}人间"
        
        return {
            "success": True,
            "message": "获取成功",
            "data": bookings,
            "total": total,
            "page": page,
            "page_size": page_size
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def api_change_password_post(body):
    """修改密码"""
    try:
        student_id = body.get('student_id')
        old_password = body.get('old_password')
        new_password = body.get('new_password')
        
        # 验证参数
        if not student_id or not old_password or not new_password:
            return {
                "success": False,
                "message": "学生ID、原密码和新密码不能为空"
            }, 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询学生信息
        cursor.execute("SELECT id, password FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 验证原密码
        if not verify_password(old_password, student['password']):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "原密码错误"
            }, 401
        
        # 哈希新密码
        hashed_new_password = hash_password(new_password)
        
        # 更新密码
        cursor.execute("UPDATE students SET password = %s WHERE id = %s", (hashed_new_password, student['id']))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "密码修改成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_bookings_cancel_post(body):
    """取消预定"""
    conn = None
    cursor = None
    try:
        # 添加调试日志
        print(f"取消预定请求参数: {body}")
        
        # 获取请求参数
        booking_id = body.get('booking_id')
        
        # 验证参数
        if not booking_id:
            print("参数为空: booking_id={}".format(booking_id))
            return {
                "success": False,
                "message": "预定ID不能为空"
            }, 400

        # 转换参数类型
        try:
            booking_id = int(booking_id)
        except (ValueError, TypeError):
            print("参数类型错误: booking_id={}".format(booking_id))
            return {
                "success": False,
                "message": "预定ID必须是整数"
            }, 400
        
        print(f"处理取消预定请求: booking_id={booking_id}")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        print("数据库连接成功")
        
        # 关闭自动提交，开始事务
        conn.autocommit = False
        print("事务开始（关闭自动提交）")
        
        # 1. 检查预定是否存在
        cursor.execute("SELECT id, bed_id, student_id, booking_status FROM bookings WHERE id = %s", (booking_id,))
        booking = cursor.fetchone()
        print(f"预定查询结果: {booking}")
        
        if not booking:
            conn.rollback()
            print("预定不存在")
            return {
                "success": False,
                "message": "预定不存在"
            }, 404
        
        # 检查预定状态是否为已预定（处理可能包含空格的情况）
        status_stripped = booking['booking_status'].replace(' ', '')
        if status_stripped != '已预定':
            conn.rollback()
            print(f"预定状态不是已预定，当前状态: {booking['booking_status']}")
            return {
                "success": False,
                "message": "预定状态不是已预定"
            }, 400
        
        bed_id = booking['bed_id']
        print(f"床位ID: {bed_id}")
        
        # 2. 获取床位对应的房间ID
        cursor.execute("SELECT room_id FROM beds WHERE id = %s", (bed_id,))
        bed_info = cursor.fetchone()
        print(f"床位信息: {bed_info}")
        
        if not bed_info:
            conn.rollback()
            print("床位不存在")
            return {
                "success": False,
                "message": "床位不存在"
            }, 404
        
        room_id = bed_info['room_id']
        print(f"房间ID: {room_id}")
        
        # 3. 更新bookings表状态为"已取消"
        cursor.execute("UPDATE bookings SET booking_status = '已取消', updated_at = NOW() WHERE id = %s", (booking_id,))
        print(f"更新预定状态成功，受影响行数: {cursor.rowcount}")
        
        # 4. 更新beds表状态为"可预定"
        cursor.execute("UPDATE beds SET status = '可预定' WHERE id = %s", (bed_id,))
        print(f"更新床位状态成功，受影响行数: {cursor.rowcount}")
        
        # 5. 检查房间剩余床位数
        cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (room_id,))
        available_beds = cursor.fetchone()['available_beds']
        print(f"房间剩余床位数: {available_beds}")
        
        # 6. 如果有剩余床位，更新房间状态为"可预定"
        if available_beds > 0:
            cursor.execute("UPDATE rooms SET status = '可预定' WHERE id = %s", (room_id,))
            print(f"更新房间状态为可预定，受影响行数: {cursor.rowcount}")
        
        # 提交事务
        conn.commit()
        print("事务提交成功")
        
        return {
            "success": True,
            "message": "取消预定成功"
        }, 200
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        return {
            "success": False,
            "message": str(e)
        }, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def handle_options():
    """处理OPTIONS请求"""
    return {
        "success": True,
        "message": "OPTIONS请求成功"
    }, 200

def api_admin_login_post(body):
    """管理员登录"""
    try:
        username = body.get('username')
        password = body.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询管理员信息
        cursor.execute("SELECT id, username, password FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()
        
        if not admin:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "用户名或密码错误"
            }, 401
        
        # 验证密码
        if not verify_password(password, admin['password']):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "用户名或密码错误"
            }, 401
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "user_info": {
                    "admin_id": admin['id'],
                    "username": admin['username']
                },
                "token": f"admin_{admin['id']}_token"
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_students_get(page=1, page_size=10):
    """获取学生列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询学生总数
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total = cursor.fetchone()['total']
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询学生列表，关联专业表获取专业名称
        cursor.execute("""SELECT s.id as student_id, s.student_id as student_number, s.name, m.major_name, s.grade, s.gender 
                         FROM students s 
                         JOIN majors m ON s.major_id = m.id 
                         ORDER BY s.id DESC 
                         LIMIT %s OFFSET %s""", (page_size, offset))
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "data_list": students,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_majors_get():
    """获取所有专业列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有专业，返回专业ID和名称
        cursor.execute("SELECT id as major_id, major_name as name FROM majors ORDER BY major_name ASC")
        majors = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "data_list": majors
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_students_reset_password_post(body):
    """重置学生密码"""
    try:
        student_id = body.get('student_id')
        new_password = body.get('new_password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查学生是否存在
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 哈希新密码
        hashed_new_password = hash_password(new_password)
        
        # 更新密码
        cursor.execute("UPDATE students SET password = %s WHERE id = %s", (hashed_new_password, student_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "密码重置成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_students_update_put(body):
    """更新学生信息，支持更换专业、修改年级和姓名"""
    try:
        # 从请求体中获取参数
        id = body.get('id')  # 使用id作为学生唯一标识
        name = body.get('name')  # 姓名（可选）
        major = body.get('major')  # 新专业名称（可选）
        major_id = body.get('major_id')  # 新专业ID（可选，优先级高于专业名称）
        grade = body.get('grade')  # 年级（可选）
        gender = body.get('gender')  # 性别（可选）
        information = body.get('information')  # 选宿倾向（可选）
        
        # 将id转换为整数，处理前端可能发送的字符串类型
        try:
            id = int(id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "学生ID必须是整数"
            }, 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查学生是否存在
        cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 构建更新语句，只更新前端提供的字段
        update_fields = []
        update_values = []
        
        # 处理姓名字段
        if name is not None:
            update_fields.append("name = %s")
            update_values.append(name)
        
        # 处理选宿倾向字段
        if information is not None:
            update_fields.append("information = %s")
            update_values.append(information)
        
        # 处理专业字段
        final_major_id = None
        if major_id:
            # 如果提供了major_id，直接使用
            try:
                final_major_id = int(major_id)
            except (ValueError, TypeError):
                cursor.close()
                conn.close()
                return {
                    "success": False,
                    "message": "专业ID必须是整数"
                }, 400
            
            # 验证major_id是否存在
            cursor.execute("SELECT id FROM majors WHERE id = %s", (final_major_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return {
                    "success": False,
                    "message": "专业ID不存在"
                }, 400
            
            update_fields.append("major_id = %s")
            update_values.append(final_major_id)
        elif major:
            # 如果提供了major名称，根据名称查询专业ID
            print(f"Debug: 接收到的专业名称: {major}")
            
            # 尝试直接匹配专业名称
            cursor.execute("SELECT id FROM majors WHERE major_name = %s", (major,))
            major_data = cursor.fetchone()
            
            if not major_data:
                    # 如果直接匹配失败，尝试查询所有专业并打印
                    cursor.execute("SELECT id, major_name FROM majors")
                    all_majors = cursor.fetchall()
                    print(f"Debug: 所有专业: {all_majors}")
                    
                    # 尝试不区分大小写匹配
                    cursor.execute("SELECT id FROM majors WHERE LOWER(major_name) = LOWER(%s)", (major,))
                    major_data = cursor.fetchone()
                    
                    if not major_data:
                        cursor.close()
                        conn.close()
                        return {
                            "success": False,
                            "message": f"专业名称不存在，可用专业: {[m['major_name'] for m in all_majors]}"
                        }, 400
            
            final_major_id = major_data['id']
            update_fields.append("major_id = %s")
            update_values.append(final_major_id)
        
        # 处理年级字段
        if grade is not None:
            update_fields.append("grade = %s")
            update_values.append(str(grade))  # 确保grade是字符串类型
        
        # 处理性别字段
        if gender is not None:
            # 转换性别格式，数据库中存储的是M/F
            gender_map = {
                '男': 'M',
                '女': 'F',
                'male': 'M',
                'female': 'F',
                'm': 'M',
                'f': 'F'
            }
            db_gender = gender_map.get(gender, 'M')
            update_fields.append("gender = %s")
            update_values.append(db_gender)
        
        # 如果没有要更新的字段，直接返回成功
        if not update_fields:
            cursor.close()
            conn.close()
            return {
            "success": True,
            "message": "更新成功"
        }, 200
        
        # 构建更新SQL语句
        update_sql = f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(id)
        
        # 执行更新操作
        cursor.execute(update_sql, update_values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "更新成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500


def api_students_information_get(student_id):
    """获取学生选宿倾向和推荐宿舍，包括对应的楼层和宿舍楼"""
    try:
        # 将student_id转换为整数
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "学生ID必须是整数"
            }, 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询学生的选宿倾向和推荐宿舍
        cursor.execute("SELECT information, room_id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 初始化返回数据
        data = {
            "information": student['information'],
            "room_id": student['room_id']
        }
        
        # 如果有推荐宿舍ID，联表查询对应的楼层和宿舍楼信息
        if student['room_id']:
            # 联表查询房间、楼层和楼栋信息
            cursor.execute("""
                SELECT 
                    r.id as room_id, 
                    r.room_number, 
                    f.id as floor_id, 
                    f.floor_number, 
                    b.id as building_id, 
                    b.name as building_name
                FROM rooms r
                JOIN floors f ON r.floor_id = f.id
                JOIN buildings b ON f.building_id = b.id
                WHERE r.id = %s
            """, (student['room_id'],))
            room_info = cursor.fetchone()
            
            if room_info:
                data.update({
                    "room_number": room_info['room_number'],
                    "floor_id": room_info['floor_id'],
                    "floor_number": room_info['floor_number'],
                    "building_id": room_info['building_id'],
                    "building_name": room_info['building_name']
                })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取选宿倾向和推荐宿舍成功",
            "data": data
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_students_information_put(body):
    """更新学生选宿倾向"""
    try:
        # 从请求体中获取参数
        student_id = body.get('student_id')
        information = body.get('information')
        
        # 验证参数
        if not student_id or information is None:
            return {
                "success": False,
                "message": "学生ID和选宿倾向不能为空"
            }, 400
        
        # 将student_id转换为整数
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "学生ID必须是整数"
            }, 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查学生是否存在
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 更新选宿倾向
        cursor.execute(
            "UPDATE students SET information = %s WHERE id = %s",
            (information, student_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "选宿倾向更新成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500


def api_students_recommend_dormitory_put(body):
    """推荐宿舍并更新学生room_id字段"""
    try:
        # 从请求体中获取参数
        student_id = body.get('student_id')
        
        # 验证参数
        if not student_id:
            return {
                "success": False,
                "message": "学生ID不能为空"
            }, 400
        
        # 将student_id转换为整数
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "学生ID必须是整数"
            }, 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查学生是否存在
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "学生不存在"
            }, 404
        
        # 获取学生专业ID
        student_major_id = student['major_id']
        # 获取学生选宿倾向
        student_information = student['information'] or ''
        
        # 查询可用宿舍列表（可预定状态，专业符合或无专业限制）
        # 1. 查询所有可预定状态的宿舍
        cursor.execute("SELECT id as room_id, room_number, floor_id, room_type_id, status FROM rooms WHERE status = '可预定'")
        available_rooms = cursor.fetchall()
        
        # 2. 过滤出专业符合或无专业限制的宿舍
        eligible_rooms = []
        for room in available_rooms:
            # 查询该房间的专业限制
            cursor.execute("SELECT major_id FROM room_majors WHERE room_id = %s", (room['room_id'],))
            room_majors = cursor.fetchall()
            
            if not room_majors or any(rm['major_id'] == student_major_id for rm in room_majors):
                # 无专业限制或专业符合
                eligible_rooms.append(room)
        
        # 如果没有可用宿舍，返回错误
        if not eligible_rooms:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "暂无可用宿舍"
            }, 400
        
        # 获取每个宿舍的详细信息，包括房间类型和已选学生信息
        detailed_rooms = []
        for room in eligible_rooms:
            # 查询房间类型信息
            cursor.execute("SELECT introduction as room_type FROM room_types WHERE id = %s", (room['room_type_id'],))
            room_type = cursor.fetchone()['room_type']
            
            # 查询该房间已选学生人数
            cursor.execute("SELECT COUNT(*) as selected_count FROM bookings WHERE bed_id IN (SELECT id FROM beds WHERE room_id = %s) AND booking_status = '已预定'", (room['room_id'],))
            selected_count = cursor.fetchone()['selected_count']
            
            # 查询已选学生的选宿倾向（排除当前学生）
            cursor.execute("""
                SELECT s.information 
                FROM students s 
                JOIN bookings b ON s.id = b.student_id 
                JOIN beds bd ON b.bed_id = bd.id 
                WHERE bd.room_id = %s AND b.booking_status = '已预定' AND s.id != %s
            """, (room['room_id'], student_id))
            selected_students = cursor.fetchall()
            
            detailed_rooms.append({
                'room_id': room['room_id'],
                'room_type': room_type,
                'selected_count': selected_count,
                'selected_students': selected_students
            })
        
        # 调用AI推荐宿舍
        recommended_room_id = recommend_dormitory(student_id, student_information, detailed_rooms)
        
        # 将推荐的宿舍ID转换为整数
        try:
            recommended_room_id = int(recommended_room_id)
        except (ValueError, TypeError):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "AI推荐结果格式错误"
            }, 500
        
        # 更新学生表中的room_id字段
        cursor.execute(
            "UPDATE students SET room_id = %s WHERE id = %s",
            (recommended_room_id, student_id)
        )
        conn.commit()
        
        # 查询推荐宿舍的详细信息（宿舍楼、楼层、宿舍号）
        cursor.execute("""
            SELECT b.name as building_name, f.floor_number, r.room_number 
            FROM rooms r 
            JOIN floors f ON r.floor_id = f.id 
            JOIN buildings b ON f.building_id = b.id 
            WHERE r.id = %s
        """, (recommended_room_id,))
        room_detail = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "宿舍推荐成功",
            "data": {
                "room_id": recommended_room_id,
                "building_name": room_detail['building_name'],
                "floor_number": room_detail['floor_number'],
                "room_number": room_detail['room_number']
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_students_batch_post(body):
    """批量导入学生信息"""
    try:
        students = body.get('students', [])
        imported = 0
        failed = 0
        errors = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 遍历学生数据
        for i, student in enumerate(students):
            try:
                # 验证必填字段
                required_fields = ['student_id', 'name', 'gender', 'major_id', 'grade']
                for field in required_fields:
                    if field not in student or not student[field]:
                        raise ValueError(f"缺少必填字段: {field}")
                
                # 设置默认密码为123456并哈希加密
                default_password = hash_password('123456')
                
                # 转换性别值为数据库可接受的格式
                gender = student['gender']
                gender_map = {
                    '男': 'M',
                    '女': 'F',
                    'male': 'M',
                    'female': 'F',
                    'm': 'M',
                    'f': 'F'
                }
                # 先尝试直接匹配，然后尝试小写匹配
                gender = gender_map.get(gender) or gender_map.get(gender.lower(), 'M')
                
                # 检查学号是否已存在
                cursor.execute("SELECT COUNT(*) FROM students WHERE student_id = %s", (student['student_id'],))
                if cursor.fetchone()[0] > 0:
                    raise ValueError(f"学号已存在: {student['student_id']}")
                
                # 插入学生数据
                cursor.execute("""
                    INSERT INTO students (student_id, name, password, major_id, grade, gender)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    student['student_id'],
                    student['name'],
                    default_password,  # 实际项目中应该使用bcrypt加密
                    student['major_id'],
                    student['grade'],
                    gender
                ))
                imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"第{i+1}条记录失败: {str(e)}")
        
        # 提交事务
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"批量导入完成，成功{imported}条，失败{failed}条",
            "data": {
                "imported": imported,
                "failed": failed,
                "errors": errors
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_dorms_get(page=1, page_size=10):
    """获取宿舍列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询宿舍总数
        cursor.execute("SELECT COUNT(*) as total FROM rooms")
        total = cursor.fetchone()['total']
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询宿舍列表，关联楼层表、楼栋表和房间类型表获取完整信息，包括价格和room_type_id
        cursor.execute("SELECT r.id as room_id, r.room_number, ft.id as room_type_id, ft.introduction as room_type, ft.price, f.floor_number, b.name as building_name, r.status FROM rooms r JOIN floors f ON r.floor_id = f.id JOIN buildings b ON f.building_id = b.id JOIN room_types ft ON r.room_type_id = ft.id ORDER BY b.name, f.floor_number, r.room_number LIMIT %s OFFSET %s", (page_size, offset))
        dorms = cursor.fetchall()
        
        # 为每个宿舍计算可用床位数并获取专业限制
        for dorm in dorms:
            # 查询该房间的总床位数
            cursor.execute("SELECT COUNT(*) as total_beds FROM beds WHERE room_id = %s", (dorm['room_id'],))
            dorm['total_beds'] = cursor.fetchone()['total_beds']
            
            # 查询该房间的可用床位数
            cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (dorm['room_id'],))
            dorm['available_beds'] = cursor.fetchone()['available_beds']
            
            # 查询该房间的专业限制
            cursor.execute("SELECT rm.major_id, m.major_name FROM room_majors rm JOIN majors m ON rm.major_id = m.id WHERE rm.room_id = %s", (dorm['room_id'],))
            majors = cursor.fetchall()
            dorm['majors'] = majors
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "data_list": dorms,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_dorms_put(body):
    """更新宿舍"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 从body中获取宿舍ID
        room_id = body.get('room_id')
        
        if not room_id:
            return {
                "success": False,
                "message": "房间ID不能为空"
            }, 400
        
        # 获取当前房间的信息，包括当前的room_type_id
        cursor.execute("SELECT room_type_id FROM rooms WHERE id = %s", (room_id,))
        current_room = cursor.fetchone()
        if not current_room:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": "房间不存在"
            }, 404
        
        current_room_type_id = current_room[0]
        new_room_type_id = body.get('room_type_id', current_room_type_id)
        
        # 如果房间类型没有变化，直接更新其他字段
        if current_room_type_id == new_room_type_id:
            # 获取当前房间的状态
            cursor.execute("SELECT status FROM rooms WHERE id = %s", (room_id,))
            current_status = cursor.fetchone()[0]
            
            print(f"DEBUG: 更新宿舍 - 房间ID: {room_id}, 当前状态: {current_status}, 请求体: {body}")
            
            # 构建更新字段和参数
            update_fields = []
            params = []
            
            if 'room_number' in body:
                update_fields.append("room_number = %s")
                params.append(body['room_number'])
            
            # 如果有status字段，检查是否允许更新状态
            if 'status' in body:
                print(f"DEBUG: 更新宿舍 - 包含status字段: {body['status']}")
                # 只有非已被预定状态的房间才能修改状态
                if current_status != '已被预定':
                    new_status = body['status']
                    # 只允许在"可预定"和"不可预定"之间切换
                    if new_status in ['可预定', '不可预定']:
                        print(f"DEBUG: 更新宿舍 - 允许更新状态为: {new_status}")
                        update_fields.append("status = %s")
                        params.append(new_status)
                    else:
                        print(f"DEBUG: 更新宿舍 - 状态值不允许: {new_status}")
                else:
                    print(f"DEBUG: 更新宿舍 - 房间已被预定，不允许修改状态")
            else:
                print(f"DEBUG: 更新宿舍 - 不包含status字段")
            
            # 添加房间ID到参数列表
            params.append(room_id)
            
            # 构建并执行更新SQL
            if update_fields:
                update_sql = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, params)
            
            # 处理专业限制
            if 'majors' in body:
                # 1. 删除该宿舍的所有现有专业限制
                cursor.execute("DELETE FROM room_majors WHERE room_id = %s", (room_id,))
                
                # 2. 添加新的专业限制
                new_majors = body['majors']
                if new_majors and isinstance(new_majors, list):
                    for major_id in new_majors:
                        cursor.execute("INSERT INTO room_majors (room_id, major_id) VALUES (%s, %s)", (room_id, major_id))
            
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "message": "更新成功"
            }, 200
        
        # 1. 更新房间类型
        cursor.execute("UPDATE rooms SET room_type_id = %s WHERE id = %s", (new_room_type_id, room_id))
        
        # 2. 获取新旧房间类型的床位数
        cursor.execute("SELECT bed_count FROM room_types WHERE id = %s", (new_room_type_id,))
        new_bed_count = cursor.fetchone()[0]
        
        # 3. 获取当前房间的实际床位数
        cursor.execute("SELECT COUNT(*) FROM beds WHERE room_id = %s", (room_id,))
        current_bed_count = cursor.fetchone()[0]
        
        # 4. 计算需要调整的床位数
        bed_diff = new_bed_count - current_bed_count
        
        if bed_diff > 0:
            # 需要添加床位
            # 获取当前最大的bed_number
            cursor.execute("SELECT MAX(bed_number) FROM beds WHERE room_id = %s", (room_id,))
            max_bed_number = cursor.fetchone()[0]
            if max_bed_number is None:
                max_bed_number = 0
            
            # 添加新床位
            for i in range(bed_diff):
                new_bed_number = max_bed_number + 1 + i
                cursor.execute(
                    "INSERT INTO beds (room_id, bed_number, status) VALUES (%s, %s, %s)",
                    (room_id, new_bed_number, '可预定')
                )
        elif bed_diff < 0:
            # 需要删除床位
            beds_to_delete = abs(bed_diff)
            
            # 获取当前可删除的床位数量（状态为'可预定'的床位）
            cursor.execute("SELECT id, bed_number FROM beds WHERE room_id = %s AND status = '可预定' ORDER BY bed_number DESC", (room_id,))
            available_beds = cursor.fetchall()
            available_beds_count = len(available_beds)
            
            if available_beds_count < beds_to_delete:
                # 可用床位数不够删除
                cursor.close()
                conn.close()
                return {
                    "success": False,
                    "message": f"禁止删除：当前可删除床位数量为{available_beds_count}，需要删除{beds_to_delete}个"
                }, 400
            
            # 删除多余的床位
            for i in range(beds_to_delete):
                bed_id = available_beds[i][0]
                cursor.execute("DELETE FROM beds WHERE id = %s", (bed_id,))
        
        # 获取调整后的实际床位数
        cursor.execute("SELECT COUNT(*) FROM beds WHERE room_id = %s", (room_id,))
        adjusted_bed_count = cursor.fetchone()[0]
        
        # 检查是否有管理员手动设置的状态
        has_admin_status = 'status' in body
        
        # 检查是否修改了专业限制
        has_majors_change = 'majors' in body
        
        # 如果还有其他字段需要更新，或者修改了专业限制，就执行手动更新逻辑，不执行自动更新
        if 'room_number' in body or has_admin_status or has_majors_change:
            update_fields = []
            params = []
            
            if 'room_number' in body:
                update_fields.append("room_number = %s")
                params.append(body['room_number'])
            
            if has_admin_status:
                update_fields.append("status = %s")
                params.append(body['status'])
            
            if update_fields:
                params.append(room_id)
                update_sql = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, params)
        else:
            # 只有当没有管理员手动设置状态，并且没有修改专业限制时，才根据床位状态自动更新
            # 获取当前房间状态
            cursor.execute("SELECT status FROM rooms WHERE id = %s", (room_id,))
            current_status = cursor.fetchone()[0]
            
            # 只有当当前状态不是"已被预定"时，才更新房间状态
            if current_status != '已被预定':
                # 根据床位状态自动更新
                cursor.execute("SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'", (room_id,))
                available_beds = cursor.fetchone()[0]
                
                # 查询当前房间的所有床位数量
                cursor.execute("SELECT COUNT(*) as total_beds FROM beds WHERE room_id = %s", (room_id,))
                total_beds = cursor.fetchone()[0]
                
                # 根据床位状态更新房间状态
                if available_beds == 0 and total_beds > 0:
                    # 所有床位都已被预定，设置为"已被预定"
                    cursor.execute("UPDATE rooms SET status = '已被预定' WHERE id = %s", (room_id,))
                elif available_beds > 0:
                    # 有可用床位，设置为"可预定"
                    cursor.execute("UPDATE rooms SET status = '可预定' WHERE id = %s", (room_id,))
        
        # 处理专业限制
        if 'majors' in body:
            # 1. 删除该宿舍的所有现有专业限制
            cursor.execute("DELETE FROM room_majors WHERE room_id = %s", (room_id,))
            
            # 2. 添加新的专业限制
            new_majors = body['majors']
            if new_majors and isinstance(new_majors, list):
                for major_id in new_majors:
                    cursor.execute("INSERT INTO room_majors (room_id, major_id) VALUES (%s, %s)", (room_id, major_id))
        
        # 提交事务
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"更新成功，床位数量从{current_bed_count}调整为{adjusted_bed_count}"
        }, 200
    except Exception as e:
        # 回滚事务
        if conn and cursor:
            conn.rollback()
            cursor.close()
            conn.close()
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_buildings_get():
    """获取楼栋信息"""
    try:
        # 实现获取楼栋信息逻辑
        return {
            "success": True,
            "message": "获取成功",
            "data": []
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_floors_get(building_id):
    """获取楼层信息"""
    try:
        # 实现获取楼层信息逻辑
        return {
            "success": True,
            "message": "获取成功",
            "data": []
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_rooms_get(building_id, floor_id):
    """获取房间信息"""
    try:
        # 实现获取房间信息逻辑
        return {
            "success": True,
            "message": "获取成功",
            "data": []
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_beds_get(room_id):
    """获取床位信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询指定房间的所有床位
        cursor.execute("SELECT * FROM beds WHERE room_id = %s ORDER BY bed_number", (room_id,))
        beds = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": beds
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_bookings_get(page=1, page_size=10):
    """获取所有预约记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询总记录数
        cursor.execute("SELECT COUNT(*) as total FROM bookings")
        total = cursor.fetchone()['total']
        
        # 查询预约记录，关联学生、床位、房间、楼栋信息
        cursor.execute("""
            SELECT 
                b.id, 
                s.student_id as student_number, 
                s.name as student_name, 
                rooms.room_number, 
                buildings.name as building_name, 
                ft.price, 
                b.booking_status, 
                b.created_at as create_time
            FROM bookings b
            JOIN students s ON b.student_id = s.id
            JOIN beds ON b.bed_id = beds.id
            JOIN rooms ON beds.room_id = rooms.id
            JOIN floors ON rooms.floor_id = floors.id
            JOIN buildings ON floors.building_id = buildings.id
            JOIN room_types ft ON rooms.room_type_id = ft.id
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        bookings = cursor.fetchall()
        
        # 转换状态格式，前端期望数字状态码
        status_map = {
            '已预定': 0,
            '已取消': 2,
            '已入住': 1,
            '已离开': 3
        }
        
        formatted_bookings = []
        for booking in bookings:
            # 获取booking_status并去除可能的空格
            booking_status = booking['booking_status'].strip() if isinstance(booking['booking_status'], str) else booking['booking_status']
            formatted_booking = {
                'id': booking['id'],
                'student_id': booking['student_number'],
                'student_name': booking['student_name'],
                'room_name': booking['room_number'],
                'building_name': booking['building_name'],
                'price': booking['price'],
                'status': status_map.get(booking_status, 0),
                'create_time': booking['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            }
            formatted_bookings.append(formatted_booking)
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "data_list": formatted_bookings,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_bookings_status_put(body):
    """更新预约状态，支持将预约状态更改为已预定、已入住、已取消或已离开"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 从请求体获取参数，兼容前端传递的id字段
        booking_id = body.get('booking_id') or body.get('id')  # 预约记录ID，兼容前端使用id字段
        status = body.get('status')  # 新状态
        
        # 验证必填参数
        if not booking_id:
            return {
                "success": False,
                "message": "预约ID不能为空"
            }, 400
        
        if not status:
            return {
                "success": False,
                "message": "状态不能为空"
            }, 400
        
        # 直接使用前端传递的状态值，不需要状态映射
        # 验证状态值是否有效
        allowed_status = ['已预定', '已取消', '已入住', '已离开']
        if status not in allowed_status:
            return {
                "success": False,
                "message": f"状态值无效，允许的值为: {', '.join(allowed_status)}"
            }, 400
        
        # 先获取该预约记录对应的床位ID
        cursor.execute(
            "SELECT bed_id FROM bookings WHERE id = %s",
            (booking_id,)
        )
        result = cursor.fetchone()
        bed_id = result[0] if result else None
        
        # 更新预约状态
        cursor.execute(
            "UPDATE bookings SET booking_status = %s WHERE id = %s",
            (status, booking_id)
        )
        
        # 如果状态是"已离开"或"已取消"且找到了对应的床位ID，将床位状态改为可预定
        if status in ['已离开', '已取消'] and bed_id:
            # 获取床位对应的房间ID
            cursor.execute(
                "SELECT room_id FROM beds WHERE id = %s",
                (bed_id,)
            )
            room_result = cursor.fetchone()
            if room_result:
                room_id = room_result[0]
                
                # 更新床位状态为可预定
                cursor.execute(
                    "UPDATE beds SET status = '可预定' WHERE id = %s",
                    (bed_id,)
                )
                
                # 检查房间剩余床位数
                cursor.execute(
                    "SELECT COUNT(*) as available_beds FROM beds WHERE room_id = %s AND status = '可预定'",
                    (room_id,)
                )
                available_beds = cursor.fetchone()[0]
                
                # 如果有剩余床位，更新房间状态为"可预定"
                if available_beds > 0:
                    cursor.execute(
                        "UPDATE rooms SET status = '可预定' WHERE id = %s",
                        (room_id,)
                    )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "状态更新成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_room_types_get():
    """获取宿舍类型列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有宿舍类型
        cursor.execute("SELECT id, introduction, area, price FROM room_types WHERE is_active = 1 ORDER BY id")
        room_types = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": room_types
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_time_settings_get():
    """获取时间设置"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 从reservation_periods表中获取最新的一条预约时间设置
        cursor.execute(
            "SELECT start_time, end_time, updated_at as modify_time FROM reservation_periods ORDER BY id DESC LIMIT 1"
        )
        time_setting = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if time_setting:
            return {
                "success": True,
                "message": "获取成功",
                "data": {
                    "booking_start_time": time_setting['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    "booking_end_time": time_setting['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    "modify_time": time_setting['modify_time'].strftime('%Y-%m-%d %H:%M:%S')
                }
            }, 200
        else:
            # 如果没有记录，返回默认值
            return {
                "success": True,
                "message": "获取成功",
                "data": {
                    "booking_start_time": "2026-01-01 00:00:00",
                    "booking_end_time": "2026-12-31 23:59:59",
                    "modify_time": "2026-01-01 00:00:00"
                }
            }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_time_settings_put(body):
    """更新时间设置"""
    try:
        # 获取请求参数
        booking_start_time = body.get('booking_start_time')
        booking_end_time = body.get('booking_end_time')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 向reservation_periods表中插入一条新的预约时间设置记录
        cursor.execute(
            "INSERT INTO reservation_periods (start_time, end_time) VALUES (%s, %s)",
            (booking_start_time, booking_end_time)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "时间设置更新成功"
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500

def api_admin_history_get(studentId=None, studentName=None, startTime=None, endTime=None, status=None, page=1, page_size=10):
    """获取历史预约记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 构建查询条件
        conditions = []
        params = []
        
        if studentId:
            conditions.append("s.student_id = %s")
            params.append(studentId)
        
        if studentName:
            conditions.append("s.name LIKE %s")
            params.append(f"%{studentName}%")
        
        if startTime:
            conditions.append("b.created_at >= %s")
            params.append(startTime)
        
        if endTime:
            conditions.append("b.created_at <= %s")
            params.append(endTime)
        
        if status is not None and status != "":
            conditions.append("b.booking_status = %s")
            params.append(status)
        
        # 构建SQL查询
        base_query = """
            SELECT 
                b.id, 
                s.student_id as student_number, 
                s.name as student_name, 
                rooms.room_number, 
                buildings.name as building_name, 
                ft.price, 
                b.booking_status, 
                b.created_at as create_time
            FROM bookings b
            JOIN students s ON b.student_id = s.id
            JOIN beds ON b.bed_id = beds.id
            JOIN rooms ON beds.room_id = rooms.id
            JOIN floors ON rooms.floor_id = floors.id
            JOIN buildings ON floors.building_id = buildings.id
            JOIN room_types ft ON rooms.room_type_id = ft.id
        """
        
        # 添加条件
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""
        
        # 查询总记录数
        count_query = f"SELECT COUNT(*) as total FROM bookings b JOIN students s ON b.student_id = s.id {where_clause}"
        cursor.execute(count_query, params.copy())
        total = cursor.fetchone()['total']
        
        # 查询预约记录
        query = f"{base_query}{where_clause} ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        
        formatted_bookings = []
        for booking in bookings:
            formatted_booking = {
                'id': booking['id'],
                'student_id': booking['student_number'],
                'student_name': booking['student_name'],
                'room_name': booking['room_number'],
                'building_name': booking['building_name'],
                'create_time': booking['create_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'status': booking['booking_status'],
                'remark': ''
            }
            formatted_bookings.append(formatted_booking)
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "data_list": formatted_bookings,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
