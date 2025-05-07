# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.glossary import Glossary  # noqa
from app.models.translation_job import TranslationJob  # noqa
