## name: 
## desc: extend (bound)
_buf = []; _extend = _buf.extend; _extend(('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title>Stock Prices</title>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta http-equiv="Content-Style-Type" content="text/css" />
  <meta http-equiv="Content-Script-Type" content="text/javascript" />
  <link rel="shortcut icon" href="/images/favicon.ico" />
  <link rel="stylesheet" type="text/css" href="/css/style.css" media="all" />
  <script type="text/javascript" src="/js/util.js"></script>
  <style type="text/css">
  /*<![CDATA[*/

body {
    color: #333333;
    line-height: 150%;
}

thead {
    font-weight: bold;
    background-color: #CCCCCC;
}

.odd {
    background-color: #FFCCCC;
}

.even {
    background-color: #CCCCFF;
}

.minus {
    color: #FF0000;
}

  /*]]>*/
  </style>

 </head>

 <body>

  <h1>Stock Prices</h1>

  <table>
   <thead>
    <tr>
     <th>#</th><th>symbol</th><th>name</th><th>price</th><th>change</th><th>ratio</th>
    </tr>
   </thead>
   <tbody>\n''', ));

n = 0
for item in items:
    n += 1

    _extend(('''    <tr class="''', (n % 2 and 'odd' or 'even'), '''">
     <td style="text-align: center">''', str(n), '''</td>
     <td>
      <a href="/stocks/''', (item.symbol), '''">''', (item.symbol), '''</a>
     </td>
     <td>
      <a href="''', (item.url), '''">''', (item.name), '''</a>
     </td>
     <td>
      <strong>''', (item.s_price), '''</strong>
     </td>\n''', ));
    if item.change < 0.0:
        _extend(('''     <td class="minus">''', (item.s_change), '''</td>
     <td class="minus">''', (item.s_ratio), '''</td>\n''', ));
    else:
        _extend(('''     <td>''', (item.s_change), '''</td>
     <td>''', (item.s_ratio), '''</td>\n''', ));
    #endif
    _extend(('''    </tr>\n''', ));

#endfor

_extend(('''   </tbody>
  </table>

 </body>
</html>\n''', ));
_result = ''.join(_buf)
