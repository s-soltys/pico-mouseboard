try:
    import sys
except ImportError:
    sys = None

try:
    import traceback
except ImportError:
    traceback = None


LOG_HISTORY_LIMIT = 8
_log_history = []


def log(message):
    text = str(message)
    _log_history.append(text)
    if len(_log_history) > LOG_HISTORY_LIMIT:
        _log_history.pop(0)
    try:
        print("[main]", text)
    except Exception:
        pass


def print_exception(exc):
    if sys is not None and hasattr(sys, "print_exception"):
        sys.print_exception(exc)
        return
    if traceback is not None:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return
    log(repr(exc))


def show_exception_on_lcd(exc, stage="runtime", runtime=None):
    if runtime is not None and hasattr(runtime, "show_error"):
        try:
            runtime.show_error(exc, stage)
            return
        except Exception as screen_exc:
            log("runtime error screen failed: " + repr(screen_exc))
    try:
        from core.display import show_fatal_error
        show_fatal_error(exc, stage=stage, log_lines=_log_history)
    except Exception as display_exc:
        log("panic LCD unavailable: " + repr(display_exc))


runtime = None
try:
    try:
        from core.launcher import Mouseboard as Runtime
    except ImportError:
        from core.launcher import Launcher as Runtime
    log("starting runtime")
    runtime = Runtime()
    runtime.run()
except KeyboardInterrupt:
    log("stopped by keyboard interrupt")
    raise
except Exception as exc:
    log("fatal: " + exc.__class__.__name__)
    print_exception(exc)
    show_exception_on_lcd(exc, getattr(runtime, "error_stage", "boot"), runtime)
    log("runtime halted")
