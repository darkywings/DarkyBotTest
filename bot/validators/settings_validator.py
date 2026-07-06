import re
import logging

logger = logging.getLogger("prm-validtr")

class SettingsParamValidator:

    def validate(value: str):
        '''
        Преобразует строковый параметр переданный в команде бота в нужный тип данных
        '''
        logger.debug(f"Validating value: {value}")

        if re.findall(r"true|false", value.lower()):
            return True if value == "true" else False

        if re.findall(r"(\d+)", value.lower()):
            return int(value[0])
        
        if re.findall(r"(\d+\.\d+)", value.lower()):
            return float(value[0])
        
        if match := re.findall(r"(?:https://)?(?:www\.)?vk.(?:com|ru)/(\w+)(?=,|, |$|\s)", value):
            return match
        
        if re.findall(r"null", value.lower()):
            return None

        return value