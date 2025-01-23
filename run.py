from main import create_app
import multiprocessing

# Uygulama instance'ını oluştur
app = create_app()

if __name__ == '__main__':
    # CPU çekirdek sayısının 2 katı kadar worker
    workers = multiprocessing.cpu_count() * 2
    
    # Gunicorn ile çalıştır
    import gunicorn.app.base
    
    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items()
                     if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': '127.0.0.1:5000',
        'workers': workers,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'timeout': 120,
        'keepalive': 5,
        'preload_app': True
    }

    StandaloneApplication(app, options).run() 