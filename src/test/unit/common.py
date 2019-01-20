from app.app import CONFIG


def config_for_tests():
    CONFIG.set('Runtime', 'testing', 'true')
    return CONFIG
