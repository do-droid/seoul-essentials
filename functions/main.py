"""Firebase Cloud Functions entry point.

Exposes a single HTTP function `api` that wraps the Flask app.
Region: asia-northeast3 (Seoul)
"""

from firebase_functions import https_fn, options

from app import create_app

flask_app = create_app()


@https_fn.on_request(
    region="asia-northeast3",
    memory=options.MemoryOption.MB_512,
    timeout_sec=60,
    max_instances=10,
    min_instances=0,
)
def api(req: https_fn.Request) -> https_fn.Response:
    """Single Cloud Function wrapping the Flask REST API."""
    with flask_app.request_context(req.environ):
        rv = flask_app.full_dispatch_request()
        return https_fn.Response(
            response=rv.get_data(),
            status=rv.status_code,
            headers=dict(rv.headers),
        )
