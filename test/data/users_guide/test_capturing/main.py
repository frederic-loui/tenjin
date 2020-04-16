## context data
blog_post = {
  'title': 'Tenjin is Great',
  'content': """
Tenjin has great features.
- Very Fast
- Full Featured
- Easy to Use
"""[1:]
}
recent_posts = [
  {'id': 1, 'title': 'Tenjin is Fast' },
  {'id': 2, 'title': 'Tenjin is Full-Featured' },
  {'id': 3, 'title': 'Tenjin is Easy-to-Use' },
]
context = {
  'blog_post': blog_post,
  'recent_posts': recent_posts,
}

## render template
import tenjin
from tenjin.helpers import *
from tenjin.html import text2html
engine = tenjin.Engine(path=['views'], layout='_layout.pyhtml')
html = engine.render('blog-post.pyhtml', context)
print(html)
