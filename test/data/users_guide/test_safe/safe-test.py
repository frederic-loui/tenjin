import tenjin
from tenjin.helpers import *
from tenjin.escaped import is_escaped, as_escaped, to_escaped

## both are same notation
input = r"""
a = ${a}
b = ${b}
"""

## but passed different data type
context = {
    "a": "<b>SOS</b>",
    "b": as_escaped("<b>SOS</b>"),
}

## SafeTemplate will escape 'a' but not 'b'
template = tenjin.SafeTemplate(input=input)
print(template.script)
print("---------------------")
print(template.render(context))
