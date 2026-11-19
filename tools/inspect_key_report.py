"""Inspect pasted HID report bytes offline. Never opens a mouse."""
import argparse
import json
import pathlib


def inspect_report(text):
    report = bytes.fromhex(text.replace(':', ' '))
    if len(report) != 32:
        raise ValueError('Expected 32 report bytes, including report ID 06; exclude USB headers.')
    if report[:2] != bytes((6, 1)) or report[3] not in (2, 0x12):
        raise ValueError('Expected report 06, mapping command 01, subcommand 02 or 12.')
    expected = (sum(report[:4]) + sum(report[5:])) & 255
    if report[4] != expected:
        raise ValueError(f'Checksum mismatch: stored {report[4]:02X}, expected {expected:02X}.')
    start = 0 if report[3] == 2 else 9
    slots = {str(start+i): report[5+3*i:8+3*i].hex(' ').upper() for i in range(9)}
    return dict(report_id=6, command=1, sequence=report[2], subcommand=report[3],
                checksum_valid=True, slots=slots,
                normal_wheel=(slots.get('16') == '10 20 00' and
                              slots.get('17') == '10 40 00') if start == 9 else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--hex', help='Quoted 32-byte HID report, including leading 06')
    source.add_argument('--file', type=pathlib.Path, help='Text file containing one hex report')
    args = parser.parse_args()
    try:
        print(json.dumps(inspect_report(args.hex if args.hex is not None else
                                        args.file.read_text(encoding='utf-8-sig')), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    main()
