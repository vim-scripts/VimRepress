"####################################################################
"
" VimRepressPy3
"
" Forked from Vimpress, Copyright (C) 2007 Adrien Friggeri.
"
" See ../LICENSE for GPL conditions
"
" https://github.com/BourgeoisBear/VimRepressPy3
"
" Version:  3.3.0b
"
"####################################################################

if !has("python3")
	echoerr "VimRepress requires Python 3"
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
      echoerr "findstart"
      " locate the start of the word
      let line = getline('.')
      let start = col('.') - 1
      while start > 0 && line[start - 1] =~ '\a'
        let start -= 1
      endwhile
      return start
   else
      echoerr "findstart-else"
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
      exec("py3file " . s:pyfile)
      let s:py_loaded = 1
   endif
   exec('python3 ' . a:pyfunc)
endfunction

command! -nargs=? -complete=custom,s:CompEditType BlogList    call s:PyCMD('blog_list(<f-args>)')
command! -nargs=? -complete=custom,s:CompNewType  BlogNew     call s:PyCMD('blog_new(<f-args>)')
command! -nargs=? -complete=custom,s:CompSave     BlogSave    call s:PyCMD('blog_save(<f-args>)')
command! -nargs=? -complete=custom,s:CompPrev     BlogPreview call s:PyCMD('blog_preview(<f-args>)')
command! -nargs=1 -complete=file                  BlogUpload  call s:PyCMD('blog_upload_media(<f-args>)')
command! -nargs=1                                 BlogOpen    call s:PyCMD('blog_guess_open(<f-args>)')
command! -nargs=?                                 BlogSwitch  call s:PyCMD('blog_config_switch(<f-args>)')
command! -nargs=?                                 BlogCode    call s:PyCMD('blog_append_code(<f-args>)')
