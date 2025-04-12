"""数据库模型模块"""

# 导入所有模型，确保在使用db时可以访问到
from app.models.user import User, UserProfile, Major, Semester
from app.models.learning import Course, CourseSchedule, Grade, MajorCourse
from app.models.learning import StudyPlan, Task, FocusRecord, CheckIn
from app.models.community import Note, NoteFile, NoteTag, Post, Comment
from app.models.community import LikeRecord, Favorite, Message
from app.models.resource import Badge, UserBadge, LearningResource
from app.models.resource import ResourceRecommendation, ResourceComment
from app.models.resource import LearningBehavior, LearningAnalysis
from app.models.ai import AILearningAssistant, AIQuestion, AIConfig
from app.models.ai import Notification, SearchHistory, AdminLog 