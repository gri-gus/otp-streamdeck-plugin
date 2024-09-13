from pathlib import Path

from streamdeck_sdk.property_inspector import *

OUTPUT_DIR = Path(__file__).parent
TEMPLATE = Path(__file__).parent / "pi_template.html"


def main():
    pi = PropertyInspector(
        action_uuid="com.ggusev.otp.gettotp",
        elements=[
            Textfield(
                label="Secret",
                uid="secret",
                required=True,
                placeholder="JBSWY3DPEHPK3PXP",
            ),
        ]
    )
    pi.build(output_dir=OUTPUT_DIR, template=TEMPLATE)


if __name__ == '__main__':
    # Run to generate Property Inspector
    main()