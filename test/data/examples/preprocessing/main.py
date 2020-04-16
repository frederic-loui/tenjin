import helper

## create engine
import tenjin
from tenjin.helpers import *
engine = tenjin.Engine(postfix='.pyhtml', preprocess=True)

## render template with context data
params = { 'id': 1234, 'name': 'Foo', 'lang': 'ch' }
context = { 'params': params }
output = engine.render(':select', context);
print(output)
