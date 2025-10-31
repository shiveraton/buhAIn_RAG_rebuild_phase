import importlib

def verify_module(module_path: str, required_params: list = None) -> bool:
    try:
        module_name, func_name = module_path.rsplit(".", 1)
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)

        if required_params:
            import inspect
            sig = inspect.signature(func)
            for param in required_params:
                if param not in sig.parameters:
                    return False
        return callable(func)
    except Exception as e:
        print(f"Module verification failed: {e}")
        return False
