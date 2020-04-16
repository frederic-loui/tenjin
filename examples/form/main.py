## create Engine object
import tenjin
from tenjin.helpers import *
engine = tenjin.Engine(postfix='.pyhtml', layout='layout.pyhtml')

## render template with context data
params = { 'name': 'Foo', 'gender': 'M' }
context = { 'params': params }
output = engine.render(':update', context)   # ':update' == 'update'+postfix
print(output)
