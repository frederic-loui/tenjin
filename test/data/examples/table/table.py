## create Engine object
import tenjin
from tenjin.helpers import *
engine = tenjin.Engine()

## render template with context data
context = { 'title': 'Bordered Table Example',
            'items': [ '<AAA>', 'B&B', '"CCC"' ] }
output = engine.render('table.pyhtml', context)
print(output)
