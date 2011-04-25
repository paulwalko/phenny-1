#!/usr/bin/env python
"""
archwiki.py - Phenny ArchWiki Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

modified from Wikipedia module
author: mutantmonkey <mutantmonkey@gmail.com>
"""

import re, urllib
import web

wikiuri = 'https://wiki.archlinux.org/index.php/%s'
wikisearch = 'https://wiki.archlinux.org/index.php/Special:Search?' \
                    + 'search=%s&fulltext=Search'

r_tr = re.compile(r'(?ims)<tr[^>]*>.*?</tr>')
r_content = re.compile(r'(?ims)</p>\n</div>.*?<!-- end content -->')
r_paragraph = re.compile(r'(?ims)<p[^>]*>.*?</p>|<li(?!n)[^>]*>.*?</li>')
r_tag = re.compile(r'<(?!!)[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')
r_redirect = re.compile(
   r'(?ims)class=.redirectText.>\s*<a\s*href=./wiki/([^"/]+)'
)

abbrs = ['etc', 'ca', 'cf', 'Co', 'Ltd', 'Inc', 'Mt', 'Mr', 'Mrs', 
         'Dr', 'Ms', 'Rev', 'Fr', 'St', 'Sgt', 'pron', 'approx', 'lit', 
         'syn', 'transl', 'sess', 'fl', 'Op'] \
   + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') \
   + list('abcdefghijklmnopqrstuvwxyz')
t_sentence = r'^.{5,}?(?<!\b%s)(?:\.(?=[\[ ][A-Z0-9]|\Z)|\Z)'
r_sentence = re.compile(t_sentence % r')(?<!\b'.join(abbrs))

def unescape(s): 
   s = s.replace('&gt;', '>')
   s = s.replace('&lt;', '<')
   s = s.replace('&amp;', '&')
   s = s.replace('&#160;', ' ')
   return s

def text(html): 
   html = r_tag.sub('', html)
   html = r_whitespace.sub(' ', html)
   return unescape(html).strip()

def search(term): 
   try: import search
   except ImportError, e: 
      print e
      return term

   if isinstance(term, unicode): 
      term = term.encode('utf-8')
   else: term = term.decode('utf-8')

   term = term.replace('_', ' ')
   try: uri = search.result('site:wiki.archlinux.org %s' % term)
   except IndexError: return term
   if uri: 
      return uri[len('https://wiki.archlinux.org/index.php/'):]
   else: return term

def archwiki(term, last=False): 
   global wikiuri
   if not '%' in term: 
      if isinstance(term, unicode): 
         t = term.encode('utf-8')
      else: t = term
      q = urllib.quote(t)
      u = wikiuri % q
      bytes = web.get(u)
   else: bytes = web.get(wikiuri % term)
   bytes = r_tr.sub('', bytes)

   if not last: 
      r = r_redirect.search(bytes[:4096])
      if r: 
         term = urllib.unquote(r.group(1))
         return archwiki(term, last=True)

   # kind of hacky fix to deal with Arch wiki template, should be cleaned up a bit
   content = r_content.findall(bytes)
   if not content or len(content) < 1:
      return None
   paragraphs = r_paragraph.findall(content[0])
   print paragraphs

   if not paragraphs: 
      if not last: 
         term = search(term)
         return archwiki(term, last=True)
      return None

   # Pre-process
   paragraphs = [para for para in paragraphs 
                 if (para and 'technical limitations' not in para 
                          and 'window.showTocToggle' not in para 
                          and 'Deletion_policy' not in para 
                          and 'Template:AfD_footer' not in para 
                          and not (para.startswith('<p><i>') and 
                                   para.endswith('</i></p>'))
                          and not 'disambiguation)"' in para) 
                          and not '(images and media)' in para
                          and not 'This article contains a' in para 
                          and not 'id="coordinates"' in para
                          and not 'class="thumb' in para
                          and not 'There is currently no text in this page.' in para]
                          # and not 'style="display:none"' in para]

   for i, para in enumerate(paragraphs): 
      para = para.replace('<sup>', '|')
      para = para.replace('</sup>', '|')
      paragraphs[i] = text(para).strip()

   # Post-process
   paragraphs = [para for para in paragraphs if 
                 (para and not (para.endswith(':') and len(para) < 150))]

   para = text(paragraphs[0])
   m = r_sentence.match(para)

   if not m: 
      if not last: 
         term = search(term)
         return archwiki(term, last=True)
      return None
   sentence = m.group(0)

   maxlength = 275
   if len(sentence) > maxlength: 
      sentence = sentence[:maxlength]
      words = sentence[:-5].split(' ')
      words.pop()
      sentence = ' '.join(words) + ' [...]'

   if (('using the Article Wizard if you wish' in sentence)
    or ('or add a request for it' in sentence)): 
      if not last: 
         term = search(term)
         return archwiki(term, last=True)
      return None

   sentence = '"' + sentence.replace('"', "'") + '"'
   sentence = sentence.decode('utf-8').encode('utf-8')
   wikiuri = wikiuri.decode('utf-8').encode('utf-8')
   term = term.decode('utf-8').encode('utf-8')
   return sentence + ' - ' + (wikiuri % term)

def awik(phenny, input): 
   origterm = input.groups()[1]
   if not origterm: 
      return phenny.say('Perhaps you meant ".awik dwm"?')
   origterm = origterm.encode('utf-8')

   term = urllib.unquote(origterm)
   term = term[0].upper() + term[1:]
   term = term.replace(' ', '_')

   try: result = archwiki(term)
   except IOError: 
      error = "Can't connect to wiki.archlinux.org (%s)" % (wikiuri % term)
      return phenny.say(error)

   if result is not None: 
      phenny.say(result)
   else: phenny.say('Can\'t find anything in the ArchWiki for "%s".' % origterm)

awik.commands = ['awik']
awik.priority = 'high'

if __name__ == '__main__': 
   print __doc__.strip()