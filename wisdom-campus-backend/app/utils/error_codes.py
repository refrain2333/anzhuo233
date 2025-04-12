"""
错误码定义模块
定义系统中使用的所有错误码及其对应的错误信息
错误码格式: AABBB
- AA: 模块编号 (10-99)
- BBB: 具体错误编号 (001-999)
"""

class ErrorCode:
    """错误码定义"""
    # 通用错误 (10xxx)
    SYSTEM_ERROR = 10000        # 系统错误
    INVALID_REQUEST = 10001     # 无效的请求参数
    UNAUTHORIZED = 10002        # 未授权访问
    FORBIDDEN = 10003           # 权限不足
    NOT_FOUND = 10004           # 资源不存在
    DB_ERROR = 10005            # 数据库错误
    INVALID_INPUT = 10006       # 无效的输入数据
    RATE_LIMIT_EXCEEDED = 10007 # 请求频率超限
    
    # 认证模块错误 (20xxx)
    AUTH_LOGIN_FAILED = 20001        # 登录失败
    AUTH_USER_NOT_FOUND = 20002      # 用户不存在
    AUTH_INVALID_PASSWORD = 20003    # 密码错误
    AUTH_EMAIL_NOT_VERIFIED = 20004  # 邮箱未验证
    AUTH_USER_ALREADY_EXISTS = 20005 # 用户已存在
    AUTH_STUDENT_ID_EXISTS = 20006   # 学号已被注册
    AUTH_EMAIL_EXISTS = 20007        # 邮箱已被注册
    AUTH_VERIFICATION_FAILED = 20008 # 验证失败
    AUTH0_ERROR = 20009              # Auth0服务错误
    TOKEN_EXPIRED = 20010            # 令牌已过期
    TOKEN_INVALID = 20011            # 无效的令牌
    
    # 用户模块错误 (30xxx)
    USER_NOT_FOUND = 30001      # 用户不存在
    USER_UPDATE_FAILED = 30002  # 更新用户信息失败
    USER_PROFILE_NOT_FOUND = 30003  # 用户资料不存在
    USER_INVALID_DATA = 30004   # 无效的用户数据
    
    # 学习模块错误 (40xxx)
    COURSE_NOT_FOUND = 40001    # 课程不存在
    TASK_NOT_FOUND = 40002      # 任务不存在
    PLAN_NOT_FOUND = 40003      # 学习计划不存在
    FOCUS_RECORD_ERROR = 40004  # 专注记录错误
    
    # 错误信息映射
    messages = {
        # 通用错误
        SYSTEM_ERROR: "系统错误，请稍后重试",
        INVALID_REQUEST: "无效的请求参数",
        UNAUTHORIZED: "请先登录后再访问",
        FORBIDDEN: "您没有权限执行此操作",
        NOT_FOUND: "请求的资源不存在",
        DB_ERROR: "数据库操作失败，请稍后重试",
        INVALID_INPUT: "输入数据格式有误，请检查后重试",
        RATE_LIMIT_EXCEEDED: "请求过于频繁，请稍后再试",
        
        # 认证模块错误
        AUTH_LOGIN_FAILED: "登录失败，请检查您的账号和密码",
        AUTH_USER_NOT_FOUND: "用户不存在，请先注册",
        AUTH_INVALID_PASSWORD: "密码错误，请重新输入",
        AUTH_EMAIL_NOT_VERIFIED: "邮箱尚未验证，请查收验证邮件",
        AUTH_USER_ALREADY_EXISTS: "用户已存在，请直接登录",
        AUTH_STUDENT_ID_EXISTS: "该学号已被注册，请使用其他学号",
        AUTH_EMAIL_EXISTS: "该邮箱已注册，请直接登录或找回密码",
        AUTH_VERIFICATION_FAILED: "验证失败，请重新验证",
        AUTH0_ERROR: "认证服务暂时不可用，请稍后再试",
        TOKEN_EXPIRED: "登录已过期，请重新登录",
        TOKEN_INVALID: "无效的登录凭证，请重新登录",
        
        # 用户模块错误
        USER_NOT_FOUND: "用户不存在",
        USER_UPDATE_FAILED: "更新用户信息失败",
        USER_PROFILE_NOT_FOUND: "用户资料不存在",
        USER_INVALID_DATA: "用户数据无效",
        
        # 学习模块错误
        COURSE_NOT_FOUND: "课程不存在",
        TASK_NOT_FOUND: "任务不存在",
        PLAN_NOT_FOUND: "学习计划不存在",
        FOCUS_RECORD_ERROR: "专注记录操作失败",
    }
    
    @classmethod
    def get_message(cls, code):
        """获取错误代码对应的默认错误信息"""
        return cls.messages.get(code, "未知错误") 