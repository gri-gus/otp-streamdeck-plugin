import time
from enum import Enum

import pyotp
import pyperclip
from pynput.keyboard import Controller
from streamdeck_sdk import (
    StreamDeck,
    Action,
    events_received_objs,
    logger,
)

import settings


class OutputTypes(Enum):
    TYPE = "Type"
    CLIPBOARD = "Clipboard"


class GetTOTPAction(Action):
    UUID = "com.ggusev.otp.gettotp"

    def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
        secret = obj.payload.settings["secret"]
        output_types, output_type_selected = obj.payload.settings["output"]

        if not (secret and output_type_selected):
            self.show_alert(context=obj.context)
            return
        output_type = OutputTypes(output_type_selected)

        try:
            totp = pyotp.TOTP(s=secret)
            result = totp.now()
        except Exception as err:
            logger.exception(err)
            self.show_alert(context=obj.context)
            return

        if output_type is OutputTypes.TYPE:
            keyboard = Controller()
            keyboard.type(str(result))
            time.sleep(1)
        elif output_type is OutputTypes.CLIPBOARD:
            pyperclip.copy(result)
        else:
            self.show_alert(context=obj.context)
            return

        self.show_ok(context=obj.context)


class GetHOTPAction(Action):
    UUID = "com.ggusev.otp.gethotp"

    def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
        secret = obj.payload.settings["secret"]
        initial_count = obj.payload.settings["initial_count"]
        auto_increase = obj.payload.settings["auto_increase"]
        output_types, output_type_selected = obj.payload.settings["output"]

        if not (secret and initial_count and output_type_selected):
            self.show_alert(context=obj.context)
            return
        output_type = OutputTypes(output_type_selected)

        try:
            count = int(initial_count)
            totp = pyotp.HOTP(s=secret)
            result = totp.at(count)
        except Exception as err:
            logger.exception(err)
            self.show_alert(context=obj.context)
            return

        if output_type is OutputTypes.TYPE:
            keyboard = Controller()
            keyboard.type(str(result))
            time.sleep(1.5)
        elif output_type is OutputTypes.CLIPBOARD:
            pyperclip.copy(result)
        else:
            self.show_alert(context=obj.context)
            return

        if auto_increase:
            stngs = obj.payload.settings.copy()
            stngs["initial_count"] = str(count + 1)
            self.set_settings(context=obj.context, payload=stngs)

        self.show_ok(context=obj.context)


if __name__ == '__main__':
    StreamDeck(
        actions=[
            GetTOTPAction(),
            GetHOTPAction(),
        ],
        log_file=settings.LOG_FILE_PATH,
        log_level=settings.LOG_LEVEL,
        log_backup_count=1,
    ).run()
