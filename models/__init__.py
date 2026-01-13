from .base_model import Model, util

from .api_admin_beds_get200_response import ApiAdminBedsGet200Response
from .api_admin_beds_get200_response_data import ApiAdminBedsGet200ResponseData
from .api_admin_beds_get200_response_data_list_inner import ApiAdminBedsGet200ResponseDataListInner
from .api_admin_bookings_get200_response import ApiAdminBookingsGet200Response
from .api_admin_bookings_get200_response_data import ApiAdminBookingsGet200ResponseData
from .api_admin_bookings_get200_response_data_list_inner import ApiAdminBookingsGet200ResponseDataListInner
from .api_admin_bookings_status_put200_response import ApiAdminBookingsStatusPut200Response
from .api_admin_bookings_status_put_request import ApiAdminBookingsStatusPutRequest
from .api_admin_buildings_get200_response import ApiAdminBuildingsGet200Response
from .api_admin_buildings_get200_response_data import ApiAdminBuildingsGet200ResponseData
from .api_admin_buildings_get200_response_data_list_inner import ApiAdminBuildingsGet200ResponseDataListInner
from .api_admin_dorms_delete_request import ApiAdminDormsDeleteRequest
from .api_admin_dorms_get200_response import ApiAdminDormsGet200Response
from .api_admin_dorms_get200_response_data import ApiAdminDormsGet200ResponseData
from .api_admin_dorms_get200_response_data_list_inner import ApiAdminDormsGet200ResponseDataListInner
from .api_admin_dorms_post200_response import ApiAdminDormsPost200Response
from .api_admin_dorms_post_request import ApiAdminDormsPostRequest
from .api_admin_dorms_put_request import ApiAdminDormsPutRequest
from .api_admin_floors_get200_response import ApiAdminFloorsGet200Response
from .api_admin_floors_get200_response_data import ApiAdminFloorsGet200ResponseData
from .api_admin_floors_get200_response_data_list_inner import ApiAdminFloorsGet200ResponseDataListInner
from .api_admin_history_get200_response import ApiAdminHistoryGet200Response
from .api_admin_history_get200_response_data import ApiAdminHistoryGet200ResponseData
from .api_admin_history_get200_response_data_list_inner import ApiAdminHistoryGet200ResponseDataListInner
from .api_admin_login_post200_response import ApiAdminLoginPost200Response
from .api_admin_login_post200_response_data import ApiAdminLoginPost200ResponseData
from .api_admin_login_post200_response_data_user_info import ApiAdminLoginPost200ResponseDataUserInfo
from .api_admin_login_post_request import ApiAdminLoginPostRequest
from .api_admin_rooms_get200_response import ApiAdminRoomsGet200Response
from .api_admin_rooms_get200_response_data import ApiAdminRoomsGet200ResponseData
from .api_admin_rooms_get200_response_data_list_inner import ApiAdminRoomsGet200ResponseDataListInner
from .api_admin_students_batch_post200_response import ApiAdminStudentsBatchPost200Response
from .api_admin_students_batch_post200_response_data import ApiAdminStudentsBatchPost200ResponseData
from .api_admin_students_batch_post_request import ApiAdminStudentsBatchPostRequest
from .api_admin_students_batch_post_request_students_inner import ApiAdminStudentsBatchPostRequestStudentsInner
from .api_admin_students_get200_response import ApiAdminStudentsGet200Response
from .api_admin_students_get200_response_data import ApiAdminStudentsGet200ResponseData
from .api_admin_students_get200_response_data_list_inner import ApiAdminStudentsGet200ResponseDataListInner
from .api_admin_time_settings_get200_response import ApiAdminTimeSettingsGet200Response
from .api_admin_time_settings_get200_response_data import ApiAdminTimeSettingsGet200ResponseData
from .api_admin_time_settings_put_request import ApiAdminTimeSettingsPutRequest
from .api_bookings_post200_response import ApiBookingsPost200Response
from .api_bookings_post200_response_data import ApiBookingsPost200ResponseData
from .api_bookings_post_request import ApiBookingsPostRequest
from .api_bookings_student_student_id_get200_response import ApiBookingsStudentStudentIdGet200Response
from .api_bookings_student_student_id_get200_response_data_inner import ApiBookingsStudentStudentIdGet200ResponseDataInner
from .api_buildings_get200_response import ApiBuildingsGet200Response
from .api_buildings_get200_response_data_inner import ApiBuildingsGet200ResponseDataInner
from .api_floors_get200_response import ApiFloorsGet200Response
from .api_floors_get200_response_data_inner import ApiFloorsGet200ResponseDataInner
from .api_rooms_get200_response import ApiRoomsGet200Response
from .api_rooms_get200_response_data_inner import ApiRoomsGet200ResponseDataInner
from .api_rooms_get200_response_data_inner_features import ApiRoomsGet200ResponseDataInnerFeatures
from .api_rooms_room_id_beds_get200_response import ApiRoomsRoomIdBedsGet200Response
from .api_rooms_room_id_beds_get200_response_data_inner import ApiRoomsRoomIdBedsGet200ResponseDataInner
from .api_students_login_post200_response import ApiStudentsLoginPost200Response
from .api_students_login_post200_response_data import ApiStudentsLoginPost200ResponseData
from .api_students_login_post_request import ApiStudentsLoginPostRequest

__all__ = [
    'Model', 'util',
    'ApiAdminBedsGet200Response',
    'ApiAdminBedsGet200ResponseData',
    'ApiAdminBedsGet200ResponseDataListInner',
    'ApiAdminBookingsGet200Response',
    'ApiAdminBookingsGet200ResponseData',
    'ApiAdminBookingsGet200ResponseDataListInner',
    'ApiAdminBookingsStatusPut200Response',
    'ApiAdminBookingsStatusPutRequest',
    'ApiAdminBuildingsGet200Response',
    'ApiAdminBuildingsGet200ResponseData',
    'ApiAdminBuildingsGet200ResponseDataListInner',
    'ApiAdminDormsDeleteRequest',
    'ApiAdminDormsGet200Response',
    'ApiAdminDormsGet200ResponseData',
    'ApiAdminDormsGet200ResponseDataListInner',
    'ApiAdminDormsPost200Response',
    'ApiAdminDormsPostRequest',
    'ApiAdminDormsPutRequest',
    'ApiAdminFloorsGet200Response',
    'ApiAdminFloorsGet200ResponseData',
    'ApiAdminFloorsGet200ResponseDataListInner',
    'ApiAdminHistoryGet200Response',
    'ApiAdminHistoryGet200ResponseData',
    'ApiAdminHistoryGet200ResponseDataListInner',
    'ApiAdminLoginPost200Response',
    'ApiAdminLoginPost200ResponseData',
    'ApiAdminLoginPost200ResponseDataUserInfo',
    'ApiAdminLoginPostRequest',
    'ApiAdminRoomsGet200Response',
    'ApiAdminRoomsGet200ResponseData',
    'ApiAdminRoomsGet200ResponseDataListInner',
    'ApiAdminStudentsBatchPost200Response',
    'ApiAdminStudentsBatchPost200ResponseData',
    'ApiAdminStudentsBatchPostRequest',
    'ApiAdminStudentsBatchPostRequestStudentsInner',
    'ApiAdminStudentsGet200Response',
    'ApiAdminStudentsGet200ResponseData',
    'ApiAdminStudentsGet200ResponseDataListInner',
    'ApiAdminTimeSettingsGet200Response',
    'ApiAdminTimeSettingsGet200ResponseData',
    'ApiAdminTimeSettingsPutRequest',
    'ApiBookingsPost200Response',
    'ApiBookingsPost200ResponseData',
    'ApiBookingsPostRequest',
    'ApiBookingsStudentStudentIdGet200Response',
    'ApiBookingsStudentStudentIdGet200ResponseDataInner',
    'ApiBuildingsGet200Response',
    'ApiBuildingsGet200ResponseDataInner',
    'ApiFloorsGet200Response',
    'ApiFloorsGet200ResponseDataInner',
    'ApiRoomsGet200Response',
    'ApiRoomsGet200ResponseDataInner',
    'ApiRoomsGet200ResponseDataInnerFeatures',
    'ApiRoomsRoomIdBedsGet200Response',
    'ApiRoomsRoomIdBedsGet200ResponseDataInner',
    'ApiStudentsLoginPost200Response',
    'ApiStudentsLoginPost200ResponseData',
    'ApiStudentsLoginPostRequest'
]