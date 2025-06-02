import os

# Compute the root path (parent directory of this file)
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Limits
MAX_CORES_ALLOWED = 16  # avoid out of memory error

# Endpoints
ACOUSTID_LOOKUP_ENDPOINT = 'https://api.acoustid.org/v2/lookup'
ACOUSTID_TRACK_ENDPOINT = 'https://acoustid.org/track'
AUDIOTAG_ENDPOINT = 'https://audiotag.info/api'

# Folders
DATABASE_FOLDER    = os.path.join(ROOT_PATH, 'database')
INPUT_FOLDER       = os.path.join(ROOT_PATH, 'input')
LOGS_FOLDER        = os.path.join(ROOT_PATH, 'logs')
PRECOMPUTED_FOLDER = os.path.join(ROOT_PATH, 'precomputed')
PROCESSED_FOLDER   = os.path.join(ROOT_PATH, 'processed')
TEMP_FOLDER        = os.path.join(ROOT_PATH, 'temp')

# Files
AFPTS_FILE         = os.path.join(ROOT_PATH, 'temp', '_afpts.txt')
AUDFPRINT_PROGRAM  = os.path.join(ROOT_PATH, 'libs', 'audfprint', 'audfprint.py')
AUDFPRINT_SCRIPT   = os.path.join(ROOT_PATH, 'scripts', 'audfprint.js')
ENV_FILE           = os.path.join(ROOT_PATH, '.env')
EXAMPLE_ENV_FILE   = os.path.join(ROOT_PATH, '.env.example')
FILLER_FILE        = os.path.join(ROOT_PATH, 'resources', 'filler.mp3')
FPCALC_SCRIPT      = os.path.join(ROOT_PATH, 'scripts', 'fpcalc.js')
MUSICBRAINZ_SCRIPT = os.path.join(ROOT_PATH, 'scripts', 'musicbrainz.js')
PKLZS_FILE         = os.path.join(ROOT_PATH, 'temp', '_pklzs.txt')
RESULTS_FILE       = os.path.join(ROOT_PATH, 'temp', '_results.json')
SHAZAM_SCRIPT      = os.path.join(ROOT_PATH, 'scripts', 'shazam.py')
