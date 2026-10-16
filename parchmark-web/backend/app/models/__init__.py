# Models package initialization

# Register every table on Base.metadata whenever any model module is imported,
# so standalone create_all/drop_all callers (app.database.seed --reset,
# app.database.init_db) see api_tokens, artifacts and artifact_versions and
# their foreign keys to users.
from app.models.api_token import ApiToken  # noqa: F401
from app.models.artifact import Artifact  # noqa: F401
from app.models.artifact_version import ArtifactVersion  # noqa: F401
