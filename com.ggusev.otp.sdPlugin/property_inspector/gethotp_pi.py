from pathlib import Path

from streamdeck_sdk.property_inspector import *

OUTPUT_DIR = Path(__file__).parent
TEMPLATE = Path(__file__).parent / "pi_template.html"


def main():
    pi = PropertyInspector(
        action_uuid="com.ggusev.otp.gethotp",
        elements=[
            Textfield(
                label="Secret",
                uid="secret",
                required=True,
                placeholder="JBSWY3DPEHPK3PXP",
            ),
            Textfield(
                label="Initial count",
                uid="initial_count",
                required=True,
                placeholder="0",
                default_value="0",
                pattern=r"^\d*$"
            ),
            Checkbox(
                label="Auto increase",
                items=[
                    CheckboxItem(
                        uid="auto_increase",
                        checked=False,
                    ),
                ],
            ),
        ]
    )
    pi.build(output_dir=OUTPUT_DIR, template=TEMPLATE)


if __name__ == '__main__':
    # Run to generate Property Inspector
    main()
