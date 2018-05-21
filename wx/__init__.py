
from flask import Blueprint



wx = Blueprint('wx', __name__,
                        template_folder='templates')

import view