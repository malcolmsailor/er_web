from werkzeug.middleware.profiler import ProfilerMiddleware

from er_web import app

app.config["PROFILE"] = True
app.wsgi_app = ProfilerMiddleware(
    app.wsgi_app, restrictions=[30], profile_dir="profiling"
)
app.run(debug=True)
