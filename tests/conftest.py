def pytest_configure(config):
    for name, plugin in list(config.pluginmanager.list_name_plugin()):
        module = getattr(plugin, "__module__", "")
        if module.startswith("_pytest.cacheprovider"):
            config.pluginmanager.unregister(plugin)
