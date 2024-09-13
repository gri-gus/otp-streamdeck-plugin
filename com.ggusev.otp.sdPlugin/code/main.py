import pyotp
import pyperclip
from streamdeck_sdk import (
    StreamDeck,
    Action,
    events_received_objs,
    logger,
)

import settings


class GetTOTPAction(Action):
    UUID = "com.ggusev.otp.gettotp"

    def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
        secret = obj.payload.settings["secret"]
        if not secret:
            self.show_alert(context=obj.context)
            return
        try:
            totp = pyotp.TOTP(s=secret)
            result = totp.now()
        except Exception as err:
            logger.exception(err)
            self.show_alert(context=obj.context)
            return
        pyperclip.copy(result)
        self.show_ok(context=obj.context)


if __name__ == '__main__':
    StreamDeck(
        actions=[
            GetTOTPAction(),
        ],
        debug=True,
        debug_port=5579,
        log_file=settings.LOG_FILE_PATH,
        log_level=settings.LOG_LEVEL,
        log_backup_count=1,
    ).run()
