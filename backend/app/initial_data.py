import asyncio
import importlib
import pkgutil
import sys


async def execute_initial_data():
    package_name = "app.utils.init_data"

    # Import the package
    package = importlib.import_module(package_name)

    # Iterate over all modules in the package
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if not is_pkg:  # Ignore sub-packages
            # Import the module
            module = importlib.import_module(f"{package_name}.{module_name}")

            # Get the `main` function
            main_func = getattr(module, "main", None)

            if main_func:
                if asyncio.iscoroutinefunction(main_func):  # Check if it's async
                    print(f"Executing async main() in {module_name}")
                    await main_func()  # Await async main
                else:
                    print(f"Executing sync main() in {module_name}")
                    main_func()  # Call sync main
            else:
                print(f"No main() function found in {module_name}")


if __name__ == "__main__":
    # Apply the correct event loop policy depending on the OS
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )  # Windows only

    asyncio.run(execute_initial_data())  # Runs on both Windows & Linux
