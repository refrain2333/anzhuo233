"""
社区与笔记相关模型
"""
from app import db
from datetime import datetime
from app.models.user import User

class Note(db.Model):
    """笔记模型"""
    __tablename__ = 'note'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    title = db.Column(db.String(100), nullable=False, comment='笔记标题')
    content = db.Column(db.Text, comment='笔记内容')
    category = db.Column(db.String(50), comment='笔记分类')
    is_starred = db.Column(db.Boolean, default=False, comment='是否星标')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    share_count = db.Column(db.Integer, default=0, comment='分享次数')
    summary = db.Column(db.Text, comment='笔记摘要')
    summary_generated_at = db.Column(db.DateTime, comment='摘要生成时间')
    
    # 关系
    files = db.relationship('NoteFile', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('NoteTag', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('notes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Note {self.title}>'

class NoteFile(db.Model):
    """笔记文件模型"""
    __tablename__ = 'note_file'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id', ondelete='CASCADE'), nullable=False, comment='笔记ID，外键')
    file_url = db.Column(db.String(255), nullable=False, comment='文件URL')
    file_type = db.Column(db.Enum('pdf', 'image', 'word', 'text'), nullable=False, comment='文件类型')
    file_size = db.Column(db.Integer, nullable=False, comment='文件大小（字节）')
    file_name = db.Column(db.String(100), nullable=False, comment='文件名')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, comment='上传时间')
    api_processed = db.Column(db.Boolean, default=False, comment='是否已通过API处理')
    api_response = db.Column(db.Text, comment='API处理结果')
    
    def __repr__(self):
        return f'<NoteFile {self.file_name}>'

class NoteTag(db.Model):
    """笔记标签模型"""
    __tablename__ = 'note_tag'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id', ondelete='CASCADE'), nullable=False, comment='笔记ID，外键')
    tag_name = db.Column(db.String(50), nullable=False, comment='标签名称')
    
    def __repr__(self):
        return f'<NoteTag {self.tag_name}>'

class Post(db.Model):
    """帖子模型"""
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    title = db.Column(db.String(100), nullable=False, comment='帖子标题')
    content = db.Column(db.Text, nullable=False, comment='帖子内容')
    category = db.Column(db.Enum('note_share', 'qa', 'discussion'), nullable=False, comment='帖子类别')
    is_anonymous = db.Column(db.Boolean, default=False, comment='是否匿名')
    likes_count = db.Column(db.Integer, default=0, comment='点赞数')
    comments_count = db.Column(db.Integer, default=0, comment='评论数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    status = db.Column(db.Enum('normal', 'reported', 'banned'), default='normal', comment='帖子状态')
    
    # 关系
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False, comment='帖子ID，外键')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    content = db.Column(db.Text, nullable=False, comment='评论内容')
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id', ondelete='SET NULL'), comment='父评论ID，外键，用于回复')
    likes_count = db.Column(db.Integer, default=0, comment='点赞数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    status = db.Column(db.Enum('normal', 'reported', 'banned'), default='normal', comment='评论状态')
    
    # 关系
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class LikeRecord(db.Model):
    """点赞记录模型"""
    __tablename__ = 'like_record'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    target_type = db.Column(db.Enum('post', 'comment'), nullable=False, comment='点赞目标类型')
    target_id = db.Column(db.Integer, nullable=False, comment='点赞目标ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='点赞时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<LikeRecord {self.user_id} - {self.target_type} - {self.target_id}>'

class Favorite(db.Model):
    """收藏记录模型"""
    __tablename__ = 'favorite'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    target_type = db.Column(db.Enum('post', 'note', 'resource'), nullable=False, comment='收藏目标类型')
    target_id = db.Column(db.Integer, nullable=False, comment='收藏目标ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='收藏时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Favorite {self.user_id} - {self.target_type} - {self.target_id}>'

class Message(db.Model):
    """私信模型"""
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='发送者ID，外键')
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='接收者ID，外键')
    content = db.Column(db.Text, nullable=False, comment='私信内容')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发送时间')
    
    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Message {self.sender_id} to {self.receiver_id}>' 