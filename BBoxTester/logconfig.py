import os
import json
import logging.config
import inspect

def setup_logging(
    default_path='./config/logconfig.json', 
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
    
def logFuncName():
    logger.debug("Function called: [%s] from [%s]" % (inspect.currentframe().f_back.f_code.co_name, inspect.currentframe().f_back.f_back.f_code.co_name))    

setup_logging()
logger=logging.getLogger("console")