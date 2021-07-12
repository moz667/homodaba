
# TODO: Mover el tema de trazas a una lib a parte o investigar si exsiste  algo 
# parecido, que seguro que existira
verbosity = 0

class Trace(object):
    @staticmethod
    def set_verbosity(new_verbosity):
        global verbosity
        verbosity = new_verbosity
    
    @staticmethod
    def is_debug():
        return verbosity > 2

    @staticmethod
    def trace(title, message=None):
        print(title)
        if message:
            print(message)

    @staticmethod
    def info(title, message=None):
        if verbosity > 0:
            Trace.trace("INFO: %s" % title, message)

    @staticmethod
    def error(title, message=None):
        if verbosity > 0:
            Trace.trace("ERROR: %s" % title, message)

    @staticmethod
    def warning(title, message=None):
        if verbosity > 1:
            Trace.trace("WARNING: %s" % title, message)

    @staticmethod
    def debug(title, message=None):
        if Trace.is_debug():
            Trace.trace("DEBUG: %s" % title, message)

trace = Trace