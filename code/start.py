import argparse
from main import propositionTester 

def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(description="",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-device_serial_1', action='store', dest="device_serial_1", required=False, default="emulator-5554",
                        help="Serial of the device")
    parser.add_argument('-device_serial_2', action='store', dest="device_serial_2", required=False, default="emulator-5556",
                        help="Serial of the device")
    parser.add_argument("-root_path", action="store", dest="root_path", required=False, default="",
                        help="The root path")
    parser.add_argument("-app_path", action="store", dest="app_path", required=True,
                        help="The path of the app you want to test")
    parser.add_argument("-choice", action="store", dest="choice", required=False, default="0",
                        help="")
    parser.add_argument("-testcase_count", action="store", dest="testcase_count", required=False, default=1, type=int,
                        help="How many testcases are generated for each strategy")
    parser.add_argument("-start_testcase", action="store", dest="start_testcase", required=False, default=0, type=int,
                        help="The start testcase num")
    parser.add_argument("-event_num", action="store", dest="event_num", required=False, default=200, type=int,
                        help="How many events are in each test case")
    parser.add_argument("-max_time", action="store", dest="max_time", required=False, default=86400, type=int,
                        help="Max time")
    parser.add_argument("-rule_name", action="store", dest="rule_name", required=False, default="1", 
                        help="Name of rule")
    parser.add_argument("-tesseract_path", action="store", dest="tesseract_path", required=False, default="C:\\Program Files\\Tesseract-OCR\\tesseract.exe", 
                        help="Path to tesseract (need to download in https://github.com/tesseract-ocr/tesseract)")

    options = parser.parse_args()
    # print options
    return options

def main():
    opts = parse_args()
    import os
    # if not os.path.exists(opts.app_path):
    #     print("APK does not exist.")
    #     return

    tester = propositionTester(
        device_serial_1=opts.device_serial_1,
        device_serial_2=opts.device_serial_2,
        root_path=opts.root_path,
        app_path=opts.app_path,
        choice = opts.choice,
        testcase_count = opts.testcase_count,
        start_testcase = opts.start_testcase,
        event_num = opts.event_num,
        max_time = opts.max_time,
        rule_name = opts.rule_name,
        tesseract_path = opts.tesseract_path
    )
    tester.start()

if __name__ == "__main__":
    main()