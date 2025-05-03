from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from .dataset import DatasetStatus, FileType, PipelineRunStatus, BusinessRuleSeverity

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    metadata = Column(JSON, default={})
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    sender = Column(String, nullable=False)  # 'user' or 'bot'
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    feedback = Column(String)
    rating = Column(Integer)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="evaluations")

class Dataset(Base):
    __tablename__ = 'datasets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    description = Column(String)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_path = Column(String)
    record_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    status = Column(SQLEnum(DatasetStatus), default=DatasetStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})

    # Relationships
    user = relationship("User", back_populates="datasets")
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="dataset", cascade="all, delete-orphan")
    business_rules = relationship("BusinessRule", back_populates="dataset", cascade="all, delete-orphan")
    embeddings = relationship("DatasetEmbedding", back_populates="dataset", uselist=False, cascade="all, delete-orphan")

class DatasetColumn(Base):
    __tablename__ = 'dataset_columns'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    nullable = Column(Boolean, default=True)
    stats = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="columns")

class DatasetEmbedding(Base):
    __tablename__ = 'dataset_embeddings'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), unique=True)
    embedding = Column(ARRAY(Float))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="embeddings")

class PipelineRun(Base):
    __tablename__ = 'pipeline_runs'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    status = Column(SQLEnum(PipelineRunStatus), default=PipelineRunStatus.PENDING)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    error_message = Column(String)
    metadata = Column(JSON, default={})

    dataset = relationship("Dataset", back_populates="pipeline_runs")
    steps = relationship("PipelineStep", back_populates="pipeline_run", cascade="all, delete-orphan")

class PipelineStep(Base):
    __tablename__ = 'pipeline_steps'

    id = Column(Integer, primary_key=True)
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id'))
    step_type = Column(String, nullable=False)
    status = Column(String, default='pending')
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(String)
    metadata = Column(JSON, default={})

    pipeline_run = relationship("PipelineRun", back_populates="steps")

class BusinessRule(Base):
    __tablename__ = 'business_rules'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    name = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    severity = Column(SQLEnum(BusinessRuleSeverity), default=BusinessRuleSeverity.MEDIUM)
    message = Column(String)
    is_active = Column(Boolean, default=True)
    model_generated = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="business_rules")
