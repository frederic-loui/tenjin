## import modules and helper functions
import tenjin
from tenjin.helpers import *

## context data
context = {
    'title': 'Tenjin Example',
    'items': ['<AAA>', 'B&B', '"CCC"'],
}

## cleate engine object
engine = tenjin.Engine(path=['views'], postfix='.pyhtml', layout=':_layout')

## render template with context data
html = engine.render(':page', context)
print(html)
