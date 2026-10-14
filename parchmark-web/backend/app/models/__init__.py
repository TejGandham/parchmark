# Models package initialization

# Register every table on Base.metadata whenever any model module is imported,
# so standalone create_all/drop_all callers (app.database.seed --reset,
# app.database.init_db) see api_tokens and its foreign key to users.
from app.models.api_token import ApiToken  # noqa: F401
