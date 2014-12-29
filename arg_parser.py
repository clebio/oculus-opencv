import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    '-l',
    '--left',
    help='Left video device integer value (e.g. /dev/video1 is "1")',
    type=int,
    default=0,
)

parser.add_argument(
    '-r',
    '--right',
    help='Right video device integer value (e.g. /dev/video1 is "1")',
    type=int,
    default=1,
)

parser.add_argument(
    '-w',
    '--write',
    help='Whether to record video to file, off by default to save overhead',
    action='store_true',
)

parser.add_argument(
    '-O',
    '--oculus',
    help='Whether to enable Oculus setup',
    action='store_false',
)

parser.add_argument(
    '-f',
    '--fps',
    help='Frames per second (for recording)',
    default=15,
    type=float,
)
