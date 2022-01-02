from __future__ import annotations

from fastapi import FastAPI
from fastapi_versioning import VersionedFastAPI, version

from api.v1.main import router as v1
from api.v2.main import router as v2

app = FastAPI(version="1.0.0",
              title="Dorthu's Petstore",
              servers=[{"url": "/", "description": "Default, relative server"}])


app.include_router(v1)
app.include_router(v2)

app = VersionedFastAPI(app,
                       version_format='{major}',
                       prefix_format='/v{major}')
