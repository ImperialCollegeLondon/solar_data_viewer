# Install the Solar Orbiter pipelines
uv tool install --python 3.10 "git+https://github.com/ImperialCollegeLondon/so-pipeline-core"
uv tool update-shell

# Use them to create a database with the right schema
export SOLO_SQLALCHEMY_URL="sqlite:///./db/db.sqlite3"
so-db create-db --with-schema
