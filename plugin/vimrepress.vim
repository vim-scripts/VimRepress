"#######################################################################
" Copyright (C) 2007 Adrien Friggeri.
"
" This program is free software; you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation; either version 2, or (at your option)
" any later version.
"
" This program is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with this program; if not, write to the Free Software Foundation,
" Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  
" 
" Contributors:	Adrien Friggeri <adrien@friggeri.net>
"               Pigeond <http://pigeond.net/blog/>
"               Justin Sattery <justin.slattery@fzysqr.com>
"               Lenin Lee <lenin.lee@gmail.com>
"               Conner McDaniel <connermcd@gmail.com>
"
" Forked By: Preston M.[BOYPT] <pentie@gmail.com>
" Repository: https://bitbucket.org/pentie/vimrepress
"
" URL:		http://www.friggeri.net/projets/vimblog/
"           http://pigeond.net/blog/2009/05/07/vimpress-again/
"           http://pigeond.net/git/?p=vimpress.git
"           http://fzysqr.com/
"           http://apt-blog.net
"
" VimRepress 
"    - A mod of a mod of a mod of Vimpress.   
"    - A vim plugin fot writting your wordpress blog.
"    - Write with Markdown, control posts format precisely.
"    - Stores Markdown rawtext in wordpress custom fields.
"
" Version:	3.2.1
"
" Config: Create account configure as `~/.vimpressrc' in the following
" format:
"
"[Blog0]
"blog_url = http://a-blog.com/
"username = admin
"password = 123456
"
"[Blog1]
"blog_url = https://someone.wordpress.com/
"username = someone
"password =
"
"#######################################################################

if !has("python")
    finish
endif

let s:py_loaded = 0
let s:vimpress_dir = fnamemodify(expand("<sfile>"), ":p:h")

function! s:CompSave(ArgLead, CmdLine, CursorPos)
  return "publish\ndraft\n"
endfunction

function! s:CompPrev(ArgLead, CmdLine, CursorPos)
  return "local\npublish\ndraft\n"
endfunction

function! s:CompEditType(ArgLead, CmdLine, CursorPos)
  return "post\npage\n"
endfunction

function! s:CompNewType(ArgLead, CmdLine, CursorPos)
  return "post\npage\ncategory\n"
endfunction

function! vimrepress#CateComplete(findstart, base)
  if a:findstart
    " locate the start of the word
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\a'
      let start -= 1
    endwhile
    return start
  else
    " find matching items
    let res = []
    for m in split(s:completable,"|")
      if m =~ '^' . a:base
        call add(res, m)
      endif
    endfor
    return res
  endif
endfun

function! s:PyCMD(pyfunc)
    if (s:py_loaded == 0)
        exec("cd " . s:vimpress_dir)
        let s:pyfile = fnamemodify("vimrepress.py", ":p")
        exec("cd -")
        exec("pyfile " . s:pyfile)
        let s:py_loaded = 1
    endif
    exec('python ' . a:pyfunc)
endfunction

command! -nargs=? -complete=custom,s:CompEditType BlogList call s:PyCMD('blog_list(<f-args>)')
command! -nargs=? -complete=custom,s:CompNewType BlogNew call s:PyCMD('blog_new(<f-args>)')
command! -nargs=? -complete=custom,s:CompSave BlogSave call s:PyCMD('blog_save(<f-args>)')
command! -nargs=? -complete=custom,s:CompPrev BlogPreview call s:PyCMD('blog_preview(<f-args>)')
command! -nargs=1 -complete=file BlogUpload call s:PyCMD('blog_upload_media(<f-args>)')
command! -nargs=1 BlogOpen call s:PyCMD('blog_guess_open(<f-args>)')
command! -nargs=? BlogSwitch call s:PyCMD('blog_config_switch(<f-args>)')
command! -nargs=? BlogCode call s:PyCMD('blog_append_code(<f-args>)')
