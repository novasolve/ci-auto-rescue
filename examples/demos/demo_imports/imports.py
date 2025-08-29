"""Imports module with intentional bugs for Nova CI-Rescue demo."""


# BUG: Missing imports that are used
def get_current_time():
    """Get current time - missing import."""
    return datetime.now()  # BUG: datetime not imported


def parse_json_data(json_string):
    """Parse JSON - missing import."""
    return json.loads(json_string)  # BUG: json not imported


def calculate_square_root(n):
    """Calculate square root - missing import."""
    return math.sqrt(n)  # BUG: math not imported


def get_random_number():
    """Get random number - missing import."""
    return random.randint(1, 100)  # BUG: random not imported


def join_path(base, *parts):
    """Join path parts - missing import."""
    return os.path.join(base, *parts)  # BUG: os not imported


def compile_regex(pattern):
    """Compile regex - missing import."""
    return re.compile(pattern)  # BUG: re not imported


def get_system_info():
    """Get system info - missing import."""
    return {"platform": sys.platform, "version": sys.version}  # BUG: sys not imported


def encode_base64(data):
    """Encode to base64 - missing import."""
    return base64.b64encode(data.encode()).decode()  # BUG: base64 not imported


def sleep_seconds(seconds):
    """Sleep for seconds - missing import."""
    time.sleep(seconds)  # BUG: time not imported


def format_decimal(value):
    """Format as decimal - missing import."""
    return Decimal(str(value))  # BUG: Decimal not imported


# BUG: Circular import issues
def process_data(data):
    """Process data using utilities."""
    from utilities import clean_data  # BUG: utilities imports this module

    return clean_data(data)


# BUG: Import from wrong module
def create_dataframe(data):
    """Create dataframe - wrong import."""
    from numpy import DataFrame  # BUG: DataFrame is from pandas, not numpy

    return DataFrame(data)


# BUG: Star import issues
from collections import *  # BUG: Should be specific imports


def create_counter(items):
    """Create counter - relies on star import."""
    return Counter(items)  # Works but bad practice


# BUG: Import in except block
def safe_import_function():
    """Try to use optional library."""
    try:
        import optional_lib  # BUG: Import should be at top

        return optional_lib.process()
    except ImportError:
        return None
