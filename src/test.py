import os
import sys

restart = input(f"\nDo you want to restart the program? [y/N] ({sys.argv}) > ")

if restart == "y":
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)  # works if not compiled
    except Exception as exc:
        print(exc)
        os.execv(sys.argv[0], sys.argv)  # works if compiled
else:
    print(__file__, __name__, sys.executable)
    for k, v in os.environ.items():
        print(f'{k}:\t{v}')
    print("\nThe program will be closed...")
    sys.exit(0)
