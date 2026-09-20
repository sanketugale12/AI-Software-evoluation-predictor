from backend.app.celery_app import celery_app

# Re-export for backward compatibility
__all__ = ["celery_app"]
