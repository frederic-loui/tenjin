# -*- coding: utf-8 -*-
import tenjin
from tenjin.helpers import *
import re

##
## message catalog to translate message
##
MESSAGE_CATALOG = {
    'en': { 'Hello': 'Hello',
            'Good bye': 'Good bye',
          },
    'fr': { 'Hello': 'Bonjour',
            'Good bye': 'Au revoir',
          },
}

##
## create translation function and return it.
## ex.
##    _ = create_m17n_func('fr')
##    print _('Hello')   #=> 'Bonjour'
##
def create_m17n_func(lang):
    dct = MESSAGE_CATALOG.get(lang)
    if not dct:
        raise ValueError("%s: unknown lang." % lang)
    def _(message_key):
        return dct.get(message_key)
    return _
    # or return dct.get

##
## test program
##
if __name__ == '__main__':

    ## render html for English
    engine_en = tenjin.Engine(preprocess=True, lang='en')
    context = { 'username': 'World' }
    context['_'] = create_m17n_func('en')
    html = engine_en.render('m17n.pyhtml', context)
    print("--- lang: en ---")
    print(html)

    ## render html for French
    engine_fr = tenjin.Engine(preprocess=True, lang='fr')
    context = { 'username': 'World' }
    context['_'] = create_m17n_func('fr')
    html = engine_fr.render('m17n.pyhtml', context)
    print("--- lang: fr ---")
    print(html)
