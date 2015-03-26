import logging
import atexit
from tree_output.houtput import HierarchicalOutput
from tree_output.log_handler import HierarchicalOutputHandler
LOGGING_OPTIONS = ('silent', 'console', 'json')


def make_console_handler(level):
    console = logging.StreamHandler()
    console.setLevel(level)
    return console


def make_hierarchical_handler(format):
    houtput = HierarchicalOutput.factory(format='json')
    return HierarchicalOutputHandler(houtput=houtput)


# We always need a json handler for project reports.
json_handler = make_hierarchical_handler('json')
json_handler.setLevel(logging.INFO)


def output_json():
    print str(json_handler.houtput)


def setup_logging(option, level=logging.INFO):
    if option not in LOGGING_OPTIONS:
        raise Exception('Unknown logging option: %s' % option)

    logging.root.setLevel(level)
    logging.root.addHandler(json_handler)

    # 'silent handler is ignored'
    if option == 'console':
        console_handler = make_console_handler(level)
        format_str = '%(asctime)s %(name)-30s %(levelname)-8s %(message)s'
        datefmt_str = '%m-%d %H:%M'
        console_handler.setFormatter(
            logging.Formatter(format_str, datefmt_str))
        logging.root.addHandler(console_handler)
    elif option == 'json':
        atexit.register(output_json)
