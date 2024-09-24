import logging
import os
import platform
import re
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

# region environ
PYTHON_COMMAND: str = os.environ["PYTHON_COMMAND"]
PYTHON_MINIMUM_VERSION: str = os.environ["PYTHON_MINIMUM_VERSION"]

PLUGIN_DIR_PATH: Path = Path(os.environ["PLUGIN_DIR_PATH"])
PLUGIN_NAME: str = os.environ["PLUGIN_NAME"]
PLUGIN_LOGS_DIR_PATH: Path = Path(os.environ["PLUGIN_LOGS_DIR_PATH"])

PLUGIN_CODE_DIR_PATH: Path = Path(os.environ["PLUGIN_CODE_DIR_PATH"])
PLUGIN_CODE_REQUIREMENTS_PATH: Path = Path(os.environ["PLUGIN_CODE_REQUIREMENTS_PATH"])

PLUGIN_CODE_VENV_DIR_PATH: Path = Path(os.environ["PLUGIN_CODE_VENV_DIR_PATH"])
PLUGIN_CODE_VENV_ACTIVATE: Path = Path(os.environ["PLUGIN_CODE_VENV_ACTIVATE"])
# endregion environ

OS_NAME = platform.system()
MANIFEST_FILE_PATH = PLUGIN_DIR_PATH / "manifest.json"

# region logging settings
LOG_FILE_PATH: Path = PLUGIN_LOGS_DIR_PATH / Path("init.log")
LOG_LEVEL = logging.DEBUG
logger: logging.Logger = logging.getLogger(__name__)
# endregion logging settings

# region regex
PARSE_REQUIREMENTS_REGEX = re.compile(r"^\s*?(\S*).=", flags=re.MULTILINE)
BEGIN_S_REGEX = re.compile(r"^\s+|\s+$")
BEGIN_END_WHITESPACES_REGEX = re.compile(r"^ +| +$", flags=re.MULTILINE)
LINE_TRANSLATION_REGEX = re.compile(r"\n|\r$", flags=re.MULTILINE)
SPACES_REGEX = re.compile(r" +", flags=re.MULTILINE)


# endregion regex

class InitError(Exception):
    pass


def main():
    init_logger(log_file=LOG_FILE_PATH, log_level=LOG_LEVEL)
    logger.info("INIT STARTED")
    try:
        init_project()
        logger.info("INIT COMPLETED SUCCESSFULLY")
        init_result = True
    except BaseException as err:
        logger.exception(err)
        logger.error("INIT COMPLETED WITH ERRORS")
        init_result = False
    logger.info(f"{init_result=}")
    print(init_result)


def init_project():
    if check_venv_activate_exists():
        logger.info("Current venv found")
        try:
            check_requirements()
        except Exception as err:
            logger.exception(f"Current venv. Check requirements ERROR: {err}")
            try:
                install_requirements()
            except Exception as err:
                raise InitError(f"Current venv. Install requirements ERROR: {err}")
            logger.info("Current venv. Requirements are successfully installed")
            try:
                check_requirements()
            except Exception as err:
                raise InitError(f"Current venv. Second check requirements ERROR: {err}")
        logger.info("Current venv is correct")
        return
    else:
        logger.info("Current venv not found")

    try:
        check_python_version()
    except Exception as err:
        raise InitError(f"Check Python version ERROR: {err}")
    logger.info("Python version is correct")

    try:
        create_venv()
    except Exception as err:
        raise InitError(f"ERROR when creating a new venv: {err}")
    logger.info("New venv created successfully")

    try:
        install_requirements()
    except Exception as err:
        raise InitError(f"New venv. Install requirements ERROR: {err}")
    logger.info("New venv. Requirements are successfully installed")

    try:
        check_requirements()
    except Exception as err:
        raise InitError(f"New venv. Check requirements ERROR: {err}")
    logger.info("New venv is correct")


def check_requirements() -> None:
    requirements_packages_text = PLUGIN_CODE_REQUIREMENTS_PATH.read_text("utf-8")
    requirements_packages_names = PARSE_REQUIREMENTS_REGEX.findall(requirements_packages_text)

    installed_packages_names = get_installed_packages_names()
    installed_packages_names_underscore = [package_name.replace("-", "_") for package_name in installed_packages_names]
    installed_packages_names.extend(installed_packages_names_underscore)

    for requirements_package_name in requirements_packages_names:
        requirements_package_name_underscore = requirements_package_name.replace("-", "_")
        if not (requirements_package_name in installed_packages_names or
                requirements_package_name_underscore in installed_packages_names):
            message = f'Package "{requirements_package_name}" not installed'
            logger.error(message)
            raise InitError(message)


def create_venv() -> None:
    process = subprocess.run(
        [PYTHON_COMMAND, "-m", "venv", PLUGIN_CODE_VENV_DIR_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )
    if process.stderr:
        logger.error(process.stderr)
        raise InitError(process.stderr)


def install_requirements() -> None:
    if OS_NAME == "Darwin":
        command = f'''
        source "{PLUGIN_CODE_VENV_ACTIVATE}" &&\
        export PYTHONPATH="{PLUGIN_CODE_DIR_PATH}" &&\
        {PYTHON_COMMAND} -m pip install --upgrade pip &&\
        {PYTHON_COMMAND} -m pip install -r "{PLUGIN_CODE_REQUIREMENTS_PATH}"\
        '''
    elif OS_NAME == "Windows":
        command = f'''
        "{PLUGIN_CODE_VENV_ACTIVATE}" &&\
        {PYTHON_COMMAND} -m pip install --upgrade pip &&\
        {PYTHON_COMMAND} -m pip install -r "{PLUGIN_CODE_REQUIREMENTS_PATH}"\
        '''
    else:
        raise InitError("Unsupported Operation System.")
    process = subprocess.run(
        clean_up_shell_command(command=command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        shell=True,
    )
    if process.stderr:
        logger.error(process.stderr)
        raise InitError(process.stderr)


def get_installed_packages_names() -> List[str]:
    if OS_NAME == "Darwin":
        command = f'''
        source "{PLUGIN_CODE_VENV_ACTIVATE}" &&\
        {PYTHON_COMMAND} -m pip freeze\
        '''
    elif OS_NAME == "Windows":
        command = f'''
        "{PLUGIN_CODE_VENV_ACTIVATE}" &&\
        {PYTHON_COMMAND} -m pip freeze\
        '''
    else:
        raise InitError("Unsupported Operation System.")
    process = subprocess.run(
        clean_up_shell_command(command=command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        shell=True,
    )
    if process.stderr:
        logger.error(process.stderr)
        raise InitError(process.stderr)
    installed_packages_names = PARSE_REQUIREMENTS_REGEX.findall(process.stdout)
    return installed_packages_names


def clean_up_shell_command(command: str) -> str:
    r1 = BEGIN_S_REGEX.sub("", command)
    r2 = BEGIN_END_WHITESPACES_REGEX.sub("", r1)
    r3 = LINE_TRANSLATION_REGEX.sub(" ", r2)
    r4 = SPACES_REGEX.sub(" ", r3)
    return r4


def check_venv_activate_exists() -> bool:
    if PLUGIN_CODE_VENV_ACTIVATE.exists():
        logger.info(f'venv activate already exists in "{PLUGIN_CODE_VENV_ACTIVATE}"')
        return True
    logger.info(f'venv activate is not exists in "{PLUGIN_CODE_VENV_ACTIVATE}"')
    return False


def check_python_version() -> None:
    minimum_python_version_splitted = PYTHON_MINIMUM_VERSION.split(".")
    python_version_info = sys.version_info
    python_version_str = ".".join([str(item) for item in python_version_info[:3]])
    for index, minimum_python_version_item in enumerate(minimum_python_version_splitted):
        if python_version_info[index] > int(minimum_python_version_item):
            logger.info(f'Current python version "{python_version_str}" > "{PYTHON_MINIMUM_VERSION}"')
            return
        elif python_version_info[index] < int(minimum_python_version_item):
            message = f'Current python version "{python_version_str}" < "{PYTHON_MINIMUM_VERSION}"'
            logger.error(message)
            raise InitError(message)
    logger.info(f'Current python version "{python_version_str}" >= "{PYTHON_MINIMUM_VERSION}"')


def init_logger(log_file: Path, log_level: int = logging.DEBUG) -> None:
    logger.setLevel(log_level)
    logs_dir: Path = log_file.parent
    logs_dir.mkdir(parents=True, exist_ok=True)
    rfh = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=3 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
        delay=False,
    )
    rfh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d): %(message)s"
    )
    rfh.setFormatter(formatter)
    logger.addHandler(rfh)


if __name__ == '__main__':
    main()
