def log(message):
    try:
        print("[boot]", message)
    except Exception:
        pass


log("startup handled by main.py")
