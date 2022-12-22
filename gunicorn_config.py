workers = 4
bind = ['0.0.0.0:8080']
enable_stdio_inheritance = True
capture_output = True
loglevel = 'debug'
errorlog='/var/log/gunicorn/error.log'
