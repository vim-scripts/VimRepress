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
" Maintainer:	Adrien Friggeri <adrien@friggeri.net>
"               Pigeond <http://pigeond.net/blog/>
"               Preston M.[BOYPT] <pentie@gmail.com>
"               Justin Sattery <justin.slattery@fzysqr.com>
"
" URL:		http://www.friggeri.net/projets/vimblog/
"           http://pigeond.net/blog/2009/05/07/vimpress-again/
"           http://pigeond.net/git/?p=vimpress.git
"           http://apt-blog.net
"           http://fzysqr.com/
"
" VimRepress 
"    - A mod of a mod of a mod of Vimpress.   
"    - A vim plugin fot writting your wordpress blog.
"
" Version:	1.2.5
"
" Configure: Add blog configure into your .vimrc
"
" let VIMPRESS=[{'username':'user',
"               \'password':'pass',
"               \'blog_url':'http://your-first-blog.com/'
"               \},
"               \{'username':'user',
"               \'password':'pass',
"               \'blog_url':'http://your-second-blog.com/'
"               \}]
"
" Changes:  
" 2011 Mar. 15 [by Preston]
"               Fix: MarkdownNewPost may override original mkd source file.
"               Add: MarkdownNewPost command detects title begins with
"                   "#" in first 10 lines of markdown source, copy the line
"                   striped "#" to the new post view.
"
" 2011 Mar. 7  [by Preston]
"               Add: MarkdownPreview command to preiview markdown in browser.
"               Add: MarkdownNewPost command to convert a markdown
"               written post into html and set to the new post view.
"
"
" 2011 Mar. 4  [by Preston]
"               Add: Move blog config info to personal .vimrc
"               Add: Multiple blog config is now supported with :BlogSwitch
"               command.
"               Add: Show which blog your editing at :BlogList view.
"               Fix: bug running :BlogList in the List view got error.
"
" 2011 Feb. 15 [by Preston]
"                Add: BlogPreview Command.
"                Add: BlogCode command args to specify code type
"                Change: blog_url uses pure address.
"                Code: Some code pretty work.
"
" 2010 August 20 [by Justin] - Fixed a bug with BlogSave command, and added 
" feature to take an existing document and use the BlogNew command to 
" convert it to a blog post (which can be saved with the header intact). 
"
"#######################################################################

if !has("python")
    finish
endif

function! CompletionSave(ArgLead, CmdLine, CursorPos)
  return "publish\ndraft\n"
endfunction

command! -nargs=0 BlogNew exec('py blog_new_post()')
command! -nargs=? BlogList exec('py blog_list_posts(<f-args>)')
command! -nargs=? -complete=custom,CompletionSave BlogSave exec('py blog_send_post(<f-args>)')
command! -nargs=1 BlogOpen exec('py blog_open_post(<f-args>)')
command! -nargs=1 -complete=file BlogUpload exec('py blog_upload_media(<f-args>)')
command! -nargs=? BlogCode exec('py blog_append_code(<f-args>)')
command! -nargs=? -complete=custom,CompletionSave BlogPreview exec('py blog_preview(<f-args>)')
command! -nargs=0 BlogSwitch exec('py blog_config_switch()')
command! -nargs=0 MarkDownPreview exec('py markdown_preview()')
command! -nargs=0 MarkDownNewPost exec('py markdown_newpost()')

python <<EOF
# -*- coding: utf-8 -*-
import urllib , urllib2 , vim , xml.dom.minidom , xmlrpclib , sys , string , re, os, mimetypes, webbrowser, tempfile

image_template = '<img title="%(file)s" src="%(url)s" class="aligncenter" />'
blog_username = None
blog_password = None
blog_url = None
handler = None
blog_conf_index = 0
vimpress_view = 'edit'
vimpress_temp_dir = ''

class VimPressException(Exception):
    pass

def get_line(what):
    start = 0
    while not vim.current.buffer[start].startswith('"'+what):
        start +=1
    return start

def get_meta(what): 
    start = get_line(what)
    end = start + 1
    while not vim.current.buffer[end][0] == '"':
        end +=1
    return " ".join(vim.current.buffer[start:end]).split(":")[1].strip()

def blog_get_cats():
    if handler is None:
        raise VimPressException("Please at lease add a blog config in your .vimrc .")
    l = handler.getCategories('', blog_username, blog_password)
    return ", ".join([i["description"].encode("utf-8") for i in l])

def blog_fill_meta_area(meta_dict):
    meta_text = \
""""=========== Meta ============
"StrID : %(strid)s
"Title : %(title)s
"Slug  : %(slug)s
"Cats  : %(cats)s
"Tags  : %(tags)s
"========== Content ==========""" % meta_dict
    meta = meta_text.split('\n')
    vim.current.buffer[0] = meta[0]
    vim.current.buffer.append(meta[1:])

def __exception_check(func):
    def __check(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except VimPressException, e:
            sys.stderr.write(str(e))
        except xmlrpclib.Fault, e:
            sys.stderr.write("xmlrpc error: %s" % e.faultString.encode("utf-8"))
        except xmlrpclib.ProtocolError, e:
            sys.stderr.write("xmlrpc error: %s %s" % (e.url, e.errmsg))
        except IOError, e:
            sys.stderr.write("network error: %s" % e)

    return __check

@__exception_check
def blog_send_post(pub = "draft"):
    if vimpress_view != 'edit':
        raise VimPressException("Command not available at list view")
    if handler is None:
        raise VimPressException("Please at lease add a blog config in your .vimrc .")

    if pub == "publish":
        publish = True
    elif pub == "draft":
        publish = False
    else:
        raise VimPressException(":BlogSave draft|publish")

        
    strid = get_meta("StrID")
    title = get_meta("Title")
    slug = get_meta("Slug").replace(" ", "-")
    cats = [i.strip() for i in get_meta("Cats").split(",")]
    tags = get_meta("Tags")
  
    text_start = 0
    while not vim.current.buffer[text_start] == "\"========== Content ==========":
        text_start +=1
    text = '\n'.join(vim.current.buffer[text_start + 1:])

    post = dict(title = title, description = text,
            categories = cats, mt_keywords = tags,
            wp_slug = slug)

    if strid == '':
        strid = handler.newPost('', blog_username,
            blog_password, post, publish)
        vim.current.buffer[get_line("StrID")] = "\"StrID : %s" % strid
        notify = "Blog %s.   ID=%s" % ("Published" if publish else "Saved as draft", strid)
    else:
        handler.editPost(strid, blog_username,
            blog_password, post, publish)
        notify = "Blog Edited. %s.   ID=%s" %  ("Published" if publish else "Saved", strid)

    sys.stdout.write(notify)
    vim.command('set nomodified')

@__exception_check
def blog_new_post(**args):
    global vimpress_view

    if vimpress_view == "list":
        currentContent = ['']
    else:
        currentContent = vim.current.buffer[:]

    vim.command("set modifiable")
    vim.command(":bdelete!")
    vimpress_view = 'edit'
    vim.command("set syntax=blogsyntax")

    meta_dict = dict(\
        strid = "", 
        title = "", 
        slug = "", 
        cats = blog_get_cats(), 
        tags = "")

    meta_dict.update(args)

    blog_fill_meta_area(meta_dict)
    vim.current.buffer.append(currentContent)
    vim.current.window.cursor = (1, 0)
    vim.command('set nomodified')
    vim.command('set textwidth=0')

@__exception_check
def blog_open_post(post_id):
    if handler is None:
        raise VimPressException("Please at lease add a blog config in your .vimrc .")
    global vimpress_view
    vimpress_view = 'edit'

    post = handler.getPost(post_id, blog_username, blog_password)
    vim.command("set modifiable")
    vim.command(":bdelete!")
    vim.command("set syntax=blogsyntax")

    meta_dict = dict(\
            strid = str(post_id), 
            title = post["title"].encode("utf-8"), 
            slug = post["wp_slug"].encode("utf-8"), 
            cats = ",".join(post["categories"]).encode("utf-8"), 
            tags = (post["mt_keywords"]).encode("utf-8"))

    blog_fill_meta_area(meta_dict)
    content = (post["description"]).encode("utf-8")
    vim.current.buffer.append(content.split('\n'))
    text_start = 0

    while not vim.current.buffer[text_start] == "\"========== Content ==========":
        text_start +=1
    text_start +=1

    vim.current.window.cursor = (text_start+1, 0)
    vim.command('set nomodified')
    vim.command('set textwidth=0')

    if vim.eval("mapcheck('<enter>')"):
        vim.command('unmap <enter>')

def blog_list_edit():
    global vimpress_view
    vimpress_view = 'edit'
    row = vim.current.window.cursor[0]
    id = vim.current.buffer[row - 1].split()[0]
    vim.command(":bdelete!")
    blog_open_post(int(id))

@__exception_check
def blog_list_posts(count = "30"):
    if handler is None:
        raise VimPressException("Please at lease add a blog config in your .vimrc .")
    allposts = handler.getRecentPosts('',blog_username, 
            blog_password, int(count))

    global vimpress_view
    vimpress_view = 'list'

    vim.command("set modifiable")
    vim.command(":bdelete!")
    vim.command("set syntax=blogsyntax")
    vim.current.buffer[0] = "\"====== List of Posts in %s =========" % blog_url

    vim.current.buffer.append(\
        [(u"%(postid)s\t%(title)s" % p).encode('utf8') for p in allposts]
        )

    vim.command('set nomodified')
    vim.command("set nomodifiable")
    vim.current.window.cursor = (2, 0)
    if not vim.eval("mapcheck('<enter>')"):
        vim.command('map <enter> :py blog_list_edit()<cr>')

@__exception_check
def blog_upload_media(file_path):
    if vimpress_view != 'edit':
        raise VimPressException("Command not available at list view")
    if handler is None:
        raise VimPressException("Please at lease add a blog config in your .vimrc .")
    if not os.path.exists(file_path):
        raise VimPressException("File does not exist: %s" % file_path)

    name = os.path.basename(file_path)
    filetype = mimetypes.guess_type(file_path)[0]
    f = open(file_path, 'r')
    bits = xmlrpclib.Binary(f.read())
    f.close()

    result = handler.newMediaObject(1, blog_username, blog_password, 
            dict(name = name, type = filetype, bits = bits))

    ran = vim.current.range

    if filetype.startswith("image"):
        img = image_template % result
        ran.append(img)
    else:
        ran.append(result["url"])
    ran.append('')

@__exception_check
def blog_append_code(code_type = ""):
    if vimpress_view != 'edit':
        raise VimPressException("Command not available at list view")
    html = \
"""<pre escaped="True"%s>
</pre>"""
    if code_type != "":
        args = ' lang="%s" line="1"' % code_type
    else:
        args = ''

    row, col = vim.current.window.cursor 
    code_block = (html % args).split('\n')
    vim.current.range.append(code_block)
    vim.current.window.cursor = (row + len(code_block), 0)

@__exception_check
def blog_preview(pub = "draft"):
    if vimpress_view != 'edit':
        raise VimPressException("Command not available at list view")
    blog_send_post(pub)
    strid = get_meta("StrID")
    if strid == "":
        raise VimPressException("Save Post before Preview :BlogSave")
    url = "%s?p=%s&preview=true" % (blog_url, strid)
    webbrowser.open(url)
    if pub == "draft":
        sys.stdout.write("\nYou have to login in the browser to preview the post when save as draft.")


@__exception_check
def blog_update_config(wp_config):
    global blog_username, blog_password, blog_url, handler
    try:
        blog_username = wp_config['username']
        blog_password = wp_config['password']
        blog_url = wp_config['blog_url']
        handler = xmlrpclib.ServerProxy("%sxmlrpc.php" % blog_url).metaWeblog
    except vim.error:
        sys.stderr.write("No Wordpress confire for Vimpress.")
    except KeyError, e:
        sys.stderr.write("Configure Error: %s" % e)

@__exception_check
def blog_config_switch():
    global blog_conf_index
    try:
        blog_conf_index += 1
        wp = vim.eval("VIMPRESS")[blog_conf_index]
    except IndexError:
        blog_conf_index = 0
        wp = vim.eval("VIMPRESS")[blog_conf_index]

    blog_update_config(wp)
    if vimpress_view == 'list':
        blog_list_posts()
    sys.stdout.write("Vimpress switched to %s" % blog_url)


def markdown_preview():
    global vimpress_temp_dir
    if vimpress_temp_dir == '':
        vimpress_temp_dir = tempfile.mkdtemp(suffix="vimpress")
    temp_htm = os.path.join(vimpress_temp_dir, "vimpress_temp.htm")
    html_heads = \
"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
   <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body>
"""
    tmp_file = open(temp_htm, 'w')
    tmp_file.write(html_heads)
    tmp_file.close()
    
    vim.command(":w !markdown >>%s" % temp_htm)
    webbrowser.open("file://%s" % temp_htm)

def markdown_newpost():
    global vimpress_temp_dir
    if vimpress_temp_dir == '':
        vimpress_temp_dir = tempfile.mkdtemp(suffix="vimpress")
    temp_htm = os.path.join(vimpress_temp_dir, "vimpress_post.htm")

    title = ""
    title_s = 0
    try:
        while title_s < 10:
            if vim.current.buffer[title_s].startswith("#"):
                title = vim.current.buffer[title_s].strip('#')
                break
            title_s += 1
    except IndexError:
        pass

    cur_file = vim.eval('expand("%:p")')
    if cur_file is None: 
        cur_file = os.path.join(vimpress_temp_dir, "tmp_vimpress.mkd")
        sys.stdout.write("\n\nCurrent buffer saved to %s\n\n" % cur_file)
    vim.command(":w! %s" % cur_file)
    vim.command(":!markdown %s >%s" % (cur_file, temp_htm))
    sys.stdout.write("Press ENTER to continue.")
    vim.command(":bdelete")
    vim.command(":r %s" % temp_htm)
    blog_new_post(title = title)

if __name__ == "__main__":
    try:
        wp = vim.eval("VIMPRESS")[0]
    except IndexError:
        sys.stderr("Vimpress default configure index error. Check your .vimrc and review :help vimpress ")
    else:    
        blog_update_config(wp)



