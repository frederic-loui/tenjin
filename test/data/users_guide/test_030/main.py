## import modules and helper functions
import tenjin
from tenjin.helpers import *

## context data
context = {
    'title': 'Tenjin Example',
    'items': ['<AAA>', 'B&B', '"CCC"'],
}

## cleate engine object
engine = tenjin.Engine(path=['views'], layout='_layout.pyhtml')

## render template with context data
html = engine.render('page.pyhtml', context)
print(html)
