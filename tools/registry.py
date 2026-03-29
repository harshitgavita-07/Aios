import importlib
import pkgutil
import os

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.discover_tools()

    def discover_tools(self):
        package_dir = os.path.dirname(__file__)
        for _, module_name, _ in pkgutil.iter_modules([package_dir]):
            if module_name.startswith('_'):
                continue
            module = importlib.import_module(f'.{module_name}', package=__name__)
            # Expect each module to expose a ``run`` function
            if hasattr(module, 'run_think'):
                self.tools[module_name] = module.run_think
            elif hasattr(module, 'run'):
                self.tools[module_name] = module.run

    def run(self, name, payload):
        if name not in self.tools:
            raise ValueError(f"Tool {name} not registered")
        return self.tools[name](payload)
