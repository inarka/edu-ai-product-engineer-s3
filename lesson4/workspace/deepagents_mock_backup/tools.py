"""Mock deepagents.tools module for testing.

This provides a mock @tool decorator that wraps functions with an
object that has the .invoke() method, mimicking LangChain/deepagents
tool behavior.
"""

from functools import wraps


class ToolWrapper:
    """Wrapper that provides .invoke() method for tool functions.

    This mimics the behavior of LangChain/deepagents tool wrappers
    which allow calling tools with a dict of parameters via .invoke().
    """

    def __init__(self, func):
        self._func = func
        # Preserve function attributes
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        wraps(func)(self)

    def invoke(self, input_dict: dict):
        """Call the tool with a dict of parameters.

        This is the standard LangChain/deepagents tool interface.

        Args:
            input_dict: Dict mapping parameter names to values

        Returns:
            The result of calling the underlying function
        """
        return self._func(**input_dict)

    def __call__(self, *args, **kwargs):
        """Allow direct function calls as well."""
        return self._func(*args, **kwargs)

    def __repr__(self):
        return f"<Tool: {self.__name__}>"


def tool(func):
    """Mock @tool decorator that wraps the function with ToolWrapper.

    This provides the .invoke() method that tests expect.

    Usage:
        @tool
        def my_tool(param: str) -> dict:
            '''Tool docstring.'''
            return {"result": param}

        # Can call via .invoke()
        result = my_tool.invoke({"param": "value"})

        # Or directly
        result = my_tool(param="value")
    """
    return ToolWrapper(func)
