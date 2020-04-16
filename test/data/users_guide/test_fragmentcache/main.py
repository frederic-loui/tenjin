import os, tenjin
from tenjin.helpers import *

## create key-value store object
if not os.path.isdir('cache.d'): os.mkdir('cache.d')
kv_store = tenjin.FileBaseStore('cache.d')      # file based

## set key-value store into tenjin.helpers.fagment_cache object
tenjin.helpers.fragment_cache.store = kv_store

## context data
## (it is strongly recommended to create function object
##  to provide pull-style context data)
def get_items():   # called only when cache is expired
    return ['AAA', 'BBB', 'CCC']
context = {'get_items': get_items}

## render html
engine = tenjin.Engine(path=['views'])
html = engine.render('items.pyhtml', context)
print(html)
