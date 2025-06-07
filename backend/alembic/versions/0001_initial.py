"""Initial migration creating all tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Uploaded files
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('file_type', sa.String()),
        sa.Column('file_path', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Transcriptions
    op.create_table(
        'transcriptions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Transcription segments
    op.create_table(
        'transcription_segments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('transcription_id', sa.Integer(), sa.ForeignKey('transcriptions.id'), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('speaker_label', sa.String()),
        sa.Column('language_detected', sa.String()),
        sa.Column('text', sa.String())
    )
    # Processed scripts
    op.create_table(
        'processed_scripts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('target_language', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Processed segments
    op.create_table(
        'processed_segments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('processed_script_id', sa.Integer(), sa.ForeignKey('processed_scripts.id'), nullable=False),
        sa.Column('transcription_segment_id', sa.Integer(), sa.ForeignKey('transcription_segments.id'), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('speaker_label', sa.String()),
        sa.Column('processed_text', sa.String())
    )
    # TTS generations
    op.create_table(
        'tts_generations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('processed_script_id', sa.Integer(), sa.ForeignKey('processed_scripts.id'), nullable=False),
        sa.Column('voice_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # TTS segments
    op.create_table(
        'tts_segments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tts_generation_id', sa.Integer(), sa.ForeignKey('tts_generations.id'), nullable=False),
        sa.Column('processed_segment_id', sa.Integer(), sa.ForeignKey('processed_segments.id'), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('speaker_label', sa.String()),
        sa.Column('audio_file_path', sa.String())
    )
    # Lip sync jobs
    op.create_table(
        'lip_sync_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tts_generation_id', sa.Integer(), sa.ForeignKey('tts_generations.id'), nullable=False),
        sa.Column('video_file_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Lip sync segments
    op.create_table(
        'lip_sync_segments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('lip_sync_job_id', sa.Integer(), sa.ForeignKey('lip_sync_jobs.id'), nullable=False),
        sa.Column('tts_segment_id', sa.Integer(), sa.ForeignKey('tts_segments.id'), nullable=False),
        sa.Column('aligned_audio_path', sa.String())
    )
    # Audio mix jobs
    op.create_table(
        'audio_mix_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('lip_sync_job_id', sa.Integer(), sa.ForeignKey('lip_sync_jobs.id'), nullable=False),
        sa.Column('original_audio_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Audio mix segments
    op.create_table(
        'audio_mix_segments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('audio_mix_job_id', sa.Integer(), sa.ForeignKey('audio_mix_jobs.id'), nullable=False),
        sa.Column('output_audio_path', sa.String()),
        sa.Column('channel_info', sa.String())
    )
    # Final output jobs
    op.create_table(
        'final_output_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('audio_mix_job_id', sa.Integer(), sa.ForeignKey('audio_mix_jobs.id'), nullable=False),
        sa.Column('video_file_path', sa.String()),
        sa.Column('final_video_path', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    # Subtitle files
    op.create_table(
        'subtitle_files',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('final_output_job_id', sa.Integer(), sa.ForeignKey('final_output_jobs.id'), nullable=False),
        sa.Column('language_code', sa.String()),
        sa.Column('subtitle_format', sa.String()),
        sa.Column('file_path', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('subtitle_files')
    op.drop_table('final_output_jobs')
    op.drop_table('audio_mix_segments')
    op.drop_table('audio_mix_jobs')
    op.drop_table('lip_sync_segments')
    op.drop_table('lip_sync_jobs')
    op.drop_table('tts_segments')
    op.drop_table('tts_generations')
    op.drop_table('processed_segments')
    op.drop_table('processed_scripts')
    op.drop_table('transcription_segments')
    op.drop_table('transcriptions')
    op.drop_table('uploaded_files')
    op.drop_table('projects')
