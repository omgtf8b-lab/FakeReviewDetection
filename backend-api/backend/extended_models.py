"""Additive tables: existing users/products/reviews are not rebuilt."""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base


class ProductLinkAnalysis(Base):
    __tablename__ = 'product_link_analyses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    url = Column(String(2000), nullable=False)
    platform = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default='queued')
    result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CollectionSnapshot(Base):
    __tablename__ = 'collection_snapshots'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    canonical_url = Column(String(2000), nullable=False)
    platform = Column(String(30), nullable=False)
    source = Column(String(80), nullable=False)
    payload = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CollectedReview(Base):
    __tablename__ = 'collected_reviews'
    __table_args__ = (UniqueConstraint('snapshot_id','source_review_id',name='uq_collected_review_snapshot'),)
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('collection_snapshots.id',ondelete='CASCADE'), nullable=False,index=True)
    source_review_id = Column(String(150), nullable=False)
    content = Column(Text, nullable=False,default='')
    rating = Column(Float, nullable=True)
    author_id = Column(String(150), nullable=True)
    payload = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    display_name = Column(String(150), default='')
    shop_name = Column(String(150), default='')
    shop_description = Column(Text, default='')
    phone = Column(String(30), default='')
    token_version = Column(Integer, nullable=False, default=0)


class ProductExtra(Base):
    __tablename__ = 'product_extra'
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    image_url = Column(String(1000), default='')
    stock = Column(Integer, default=0)
    sale_status = Column(String(20), default='active')
    canonical_key = Column(String(200), default='')


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReviewReply(Base):
    __tablename__ = 'review_replies'
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReviewVote(Base):
    __tablename__ = 'review_votes'
    __table_args__ = (UniqueConstraint('review_id', 'user_id'),)
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    useful = Column(Boolean, nullable=False)


class Moderation(Base):
    __tablename__ = 'review_moderations'
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    label = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportResolution(Base):
    __tablename__ = 'report_resolutions'
    report_id = Column(Integer, ForeignKey('review_reports.id', ondelete='CASCADE'), primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    note = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Analysis(Base):
    __tablename__ = 'direct_analyses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskSnapshot(Base):
    __tablename__ = 'risk_snapshots'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    score = Column(Float, nullable=False)
    level = Column(String(20), nullable=False)
    evidence = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrustSnapshot(Base):
    __tablename__ = 'shop_trust_scores'
    __table_args__ = (UniqueConstraint('shop_id', 'day'),)
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    day = Column(String(10), nullable=False)
    total = Column(Integer, nullable=False)
    fake = Column(Integer, nullable=False)
    pending = Column(Integer, nullable=False)
    trust_score = Column(Float, nullable=True)


class FraudCluster(Base):
    __tablename__ = 'fraud_clusters'
    id = Column(Integer, primary_key=True)
    members = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class Setting(Base):
    __tablename__ = 'system_settings'
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Watch(Base):
    __tablename__ = 'product_watches'
    __table_args__ = (UniqueConstraint('product_id', 'user_id'),)
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class PasswordReset(Base):
    __tablename__ = 'password_resets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)


class Outbox(Base):
    __tablename__ = 'notification_outbox'
    id = Column(Integer, primary_key=True)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(20), default='queued')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrainingJob(Base):
    __tablename__ = 'training_jobs'
    id = Column(Integer, primary_key=True)
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    kind = Column(String(30), nullable=False)
    status = Column(String(20), default='queued')
    details = Column(Text, default='')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Content(Base):
    __tablename__ = 'site_content'
    id = Column(Integer, primary_key=True)
    kind = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)


class ExternalIdentity(Base):
    __tablename__ = 'external_identities'
    uid = Column(String(128), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class Device(Base):
    __tablename__ = 'push_devices'
    token = Column(String(1024), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class Preference(Base):
    __tablename__ = 'notification_preferences'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    email_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=False)


class SearchEvent(Base):
    __tablename__ = 'search_events'
    id = Column(Integer, primary_key=True)
    kind = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    operation = Column(String(20), nullable=False, default='upsert')
    status = Column(String(20), nullable=False, default='queued')


class ModelExperiment(Base):
    __tablename__ = 'model_experiments'
    id = Column(Integer, primary_key=True)
    model_a = Column(String(200), nullable=False)
    model_b = Column(String(200), nullable=False)
    traffic_b = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)


class ModelObservation(Base):
    __tablename__ = 'model_observations'
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey('model_experiments.id'), nullable=False)
    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False)
    variant = Column(String(1), nullable=False)
    result = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
