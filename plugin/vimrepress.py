# -*- coding: utf-8 -*-
import vim
import urllib.request, urllib.parse, urllib.error
import xmlrpc.client
import re
import os
import pprint
import sys
import mimetypes
import webbrowser
import tempfile
from configparser import SafeConfigParser

# -------------------------------- CONSTANTS --------------------------------

class VRP_CONST:
    @staticmethod
    def MARKER():
        return dict(
            bg         = "====================== Meta =========================",
            mid        = "=====================================================",
            ed         = "===================== Content =======================",
            more       = '" =============== Press Here for More ===============',
            list_title = '" ====== %(edit_type)s List in %(blog_url)s =========',
        )

    @staticmethod
    def APP_NAME():
        return "VimRepressPy3"

    @staticmethod
    def IMAGE_TEMPLATE():
        return '<a href="%(url)s">' \
               '<img title="%(file)s" alt="%(file)s" src="%(url)s"' \
               ' class="aligncenter" /></a>'

    @staticmethod
    def LIST_VIEW_KEY_MAP():
        return dict(enter="<enter>", delete="<delete>")

    @staticmethod
    def DEFAULT_LIST_COUNT():
        return str(vim.current.window.height)

    @staticmethod
    def CUSTOM_FIELD_KEY():
        return "mkd_text"

# -------------------------------- /CONSTANTS --------------------------------

# ---------------------------------- UTLILS ----------------------------------

class VRP_Exception(Exception):
    pass

class VRP_AssertException(Exception):
    pass

def VRP_Assert(bCond, szMsg, bInfo = False):
    if not bCond:
        if bInfo:
            raise VRP_AssertException(szMsg)
        else:
            raise VRP_Exception(szMsg)

# 2016-12-07: JSTEWART: USE STDIN / STDOUT FOR REPORTING. HAS SAME EFFECT PER
#                       DOCS AT http://vimdoc.sourceforge.net/htmldoc/if_pyth.html
#                       UNDER *python-output*
def echomsg(s, bNewline = True):
    sys.stdout.write(s)

    if bNewline:
        sys.stdout.write("\n")

def echoerr(s):
    sys.stderr.write("ERROR: %s\n" % s)

def exception_check(func):
    def __check(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (VRP_AssertException) as e:
            echomsg(str(e))
        except (VRP_Exception) as e:
            echoerr(str(e))
        except (xmlrpc.client.Fault, xmlrpc.client.ProtocolError) as e:
            if getattr(e, "faultString", None) is None:
                echoerr("(XMLRPC) %s" % e)
            else:
                echoerr("(XMLRPC) %s" % e.faultString)
        except IOError as e:
            echoerr("(NETWORK) %s" % e)

        # 2016-12-07: JSTEWART: LET UNHANDLED EXCEPTIONS BUBBLE-UP, PREVIOUS echoerr()
        #                       DUPLICATED MESSAGE AND ABBREVIATED STACK TRACE

    return __check

# ---------------------------------- /UTLILS ----------------------------------

try:
    import markdown
except ImportError:
    try:
        import markdown2 as markdown
    except ImportError:
        class markdown_stub(object):
            def markdown(self, n):
                raise VRP_Exception("The package python-markdown is "
                        "required and is either not present or not properly "
                        "installed.")

        markdown = markdown_stub()

class DataObject(object):

    # TEMP VARIABLES
    __oXMLRPC    = None
    __conf_index = 0
    __config     = None

    view = 'edit'
    vimpress_temp_dir = ''

    blog_username   = property(lambda self: self.oXMLRPC.username)
    blog_url        = property(lambda self: self.oXMLRPC.blog_url)
    conf_index      = property(lambda self: self.__conf_index)
    post_cache      = property(lambda self: self.oXMLRPC.post_cache)
    current_post_id = property(
        lambda self: self.oXMLRPC.current_post_id,
        lambda self, d: setattr(self.oXMLRPC, "current_post_id", d))

    @property
    def current_post(self):
        post_id = self.current_post_id
        post = self.post_cache.get(post_id)
        if post is None and post_id == '':
            post = ContentStruct()
            if post.post_id != '':
                self.current_post_id = post.post_id
                self.current_post = post
            else:
                self.post_cache[''] = post

        VRP_Assert(post is not None, "current_post, no way to return None")

        return post

    @current_post.setter
    def current_post(self, data):
        post_id = str(data.post_id)

         # New post, just post first time
        if self.current_post_id == '' and \
                post_id != '' and '' in self.post_cache:
            self.post_cache.pop('')
        self.current_post_id = post_id
        if post_id not in self.post_cache:
            self.post_cache[post_id] = data

    @conf_index.setter
    def conf_index(self, index):
        try:
            index = int(index)
        except ValueError:
            raise VRP_Exception("Invalid Index: %s" % index)

        # auto increase
        if index < 0:
            self.__conf_index += 1
            if self.__conf_index >= len(self.config):
                self.__conf_index = 0

        # user enter index
        else:
            VRP_Assert(index < len(self.config), "Invalid Index: %d" % index)
            self.__conf_index = index

        self.__oXMLRPC = None

    @property
    def oXMLRPC(self):
        if self.__oXMLRPC is None:
            conf_index = self.conf_index
            config = self.config[conf_index]

            if "xmlrpc_obj" not in config:
                try:
                    blog_username = config['username']
                    blog_password = config.get('password', '')
                    blog_url = config['blog_url']
                except KeyError as e:
                    raise VRP_Exception("Configuration error: %s" % e)

                echomsg("Connecting to '%s'... " % blog_url, False)

                if blog_password == '':
                    blog_password = vim_input("Enter password for %s" % blog_url, True)

                config["xmlrpc_obj"] = wp_xmlrpc(blog_url, blog_username, blog_password)

            self.__oXMLRPC = config["xmlrpc_obj"]

            # Setting tags and categories for completefunc
            categories = []
            for i in self.__oXMLRPC.get_categories():
                categories.append(i["categoryName"])

            szCats = "|".join(categories)
            vim.command('let s:completable = "%s"' % szCats)
            echomsg("done.")

        return self.__oXMLRPC

    @property
    def config(self):
        if self.__config is None or len(self.__config) == 0:

            confpsr = SafeConfigParser()
            confile = os.path.expanduser("~/.vimpressrc")
            conf_options = ("blog_url", "username", "password")

            if os.path.exists(confile):
                conf_list = []
                confpsr.read(confile)
                for sec in confpsr.sections():
                    values = [confpsr.get(sec, i) for i in conf_options]
                    conf_list.append(dict(list(zip(conf_options, values))))

                if len(conf_list) > 0:
                    self.__config = conf_list

            if self.__config is None or len(self.__config) == 0:
                raise VRP_Exception("Could not find ~/.vimpressrc "
                        "configuration. Please read ':help vimpress' "
                        "for more information.")

        return self.__config


class wp_xmlrpc(object):

    blog_url = None
    username = None
    password = None
    mw_api   = None
    wp_api   = None
    mt_api   = None
    demo_api = None

    def __init__(self, blog_url, username, password):
        self.blog_url = blog_url
        self.username = username
        self.password = password
        p = xmlrpc.client.ServerProxy(os.path.join(blog_url, "xmlrpc.php"))
        self.mw_api = p.metaWeblog
        self.wp_api = p.wp
        self.mt_api = p.mt
        self.demo_api = p.demo

        VRP_Assert(
            self.demo_api.sayHello() == "Hello!", \
            "XMLRPC Error with communication with '%s'@'%s'" % (username, blog_url) \
        )

        self.cache_reset()
        self.post_cache = dict()

        self.current_post_id = ''

    def cache_reset(self):
        self.__cache_post_titles = []
        self.__post_title_max = False

    def cache_remove_post(self, postid):
        for p in self.__cache_post_titles:
            if p["postid"] == str(postid):
                self.__cache_post_titles.remove(p)
                break

    is_reached_title_max = property(lambda self: self.__post_title_max)

    new_post = lambda self, post_struct: self.mw_api.newPost('',
            self.username, self.password, post_struct)

    get_post = lambda self, post_id: self.mw_api.getPost(post_id,
            self.username, self.password)

    edit_post = lambda self, post_id, post_struct: \
            self.mw_api.editPost(post_id, self.username,
                    self.password, post_struct)

    delete_post = lambda self, post_id: self.mw_api.deletePost('',
            post_id, self.username, self.password, '')

    def get_recent_post_titles(self, retrive_count=0):
        if retrive_count > len(self.__cache_post_titles) and \
                not self.is_reached_title_max:
            self.__cache_post_titles = self.mt_api.getRecentPostTitles('',
                    self.username, self.password, retrive_count)
            if len(self.__cache_post_titles) < retrive_count:
                self.__post_title_max = True

        return self.__cache_post_titles

    get_categories = lambda self: self.mw_api.getCategories('',
            self.username, self.password)

    new_category = lambda self, category: self.wp_api.newCategory('',
            self.username, self.password, category)

    new_media_object = lambda self, object_struct: \
            self.mw_api.newMediaObject('', self.username,
            self.password, object_struct)

    get_page = lambda self, page_id: self.wp_api.getPage('',
            page_id, self.username, self.password)

    delete_page = lambda self, page_id: self.wp_api.deletePage('',
            self.username, self.password, page_id)

    get_page_list = lambda self: self.wp_api.getPageList('',
            self.username, self.password)


class ContentStruct(object):

    buffer_meta = None
    post_struct_meta = None
    EDIT_TYPE = ''

    @property
    def META_TEMPLATE(self):
        KEYS_BASIC = ("StrID", "Title", "Slug")
        KEYS_EXT   = ("Cats", "Tags")
        KEYS_BLOG  = ("EditType", "EditFormat", "BlogAddr")

        pt = ['"{k:<6}: {{{t}}}'.format(k=p, t=p.lower()) for p in KEYS_BASIC]
        if self.EDIT_TYPE == "post":
            pt.extend(['"{k:<6}: {{{t}}}'.format(k=p, t=p.lower())
                    for p in KEYS_EXT])
        pm = "\n".join(pt)
        bm = "\n".join(['"{k:<11}: {{{t}}}'.format(k=p, t=p.lower())
            for p in KEYS_BLOG])
        return '"{bg}\n{0}\n"{mid}\n{1}\n"{ed}\n'.format(pm, bm, **VRP_CONST.MARKER())

    POST_BEGIN = property(lambda self: len(self.META_TEMPLATE.splitlines()))
    raw_text = ''
    html_text = ''

    def __init__(self, edit_type=None, post_id=None):

        self.EDIT_TYPE = edit_type
        self.buffer_meta = dict(strid='', edittype=edit_type,
                blogaddr=g_data.blog_url)

        self.post_struct_meta = dict(title='',
                wp_slug='',
                post_type=edit_type,
                description='',
                custom_fields=[],
                post_status='draft')

        if post_id is not None:
            self.refresh_from_wp(post_id)

        if self.EDIT_TYPE is None:
            self.parse_buffer()

    def parse_buffer(self):
        start = 0
        while not vim.current.buffer[start][1:].startswith(VRP_CONST.MARKER()['bg']):
            start += 1

        end = start + 1
        while not vim.current.buffer[end][1:].startswith(VRP_CONST.MARKER()['ed']):
            if not vim.current.buffer[end].startswith('"===='):
                line = vim.current.buffer[end][1:].strip().split(":")
                k, v = line[0].strip().lower(), ':'.join(line[1:])
                self.buffer_meta[k.strip().lower()] = v.strip()
            end += 1

        if self.EDIT_TYPE != self.buffer_meta["edittype"]:
            self.EDIT_TYPE = self.buffer_meta["edittype"]

        self.buffer_meta["content"] = '\n'.join(
                vim.current.buffer[end + 1:])

    def fill_buffer(self):
        meta = dict(strid="", title="", slug="",
                cats="", tags="", editformat="HTML", edittype="")
        meta.update(self.buffer_meta)
        meta_text = self.META_TEMPLATE.format(**meta).splitlines()
        vim.command("set ft=html")
        vim.current.buffer[0] = meta_text[0]
        vim.current.buffer.append(meta_text[1:])
        content = self.buffer_meta.get("content", ' ').splitlines()
        vim.current.buffer.append(content)

    def update_buffer_meta(self):
        """
        Updates the meta data region of a blog editing buffer.
        @params **kwargs - keyworded arguments
        """
        kw = self.buffer_meta
        start = 0
        while not vim.current.buffer[start][1:].startswith(VRP_CONST.MARKER()['bg']):
            start += 1

        end = start + 1
        while not vim.current.buffer[end][1:].startswith(VRP_CONST.MARKER()['ed']):
            if not vim.current.buffer[end].startswith('"===='):
                line = vim.current.buffer[end][1:].strip().split(":")
                k, v = line[0].strip().lower(), ':'.join(line[1:])
                if k in kw:
                    new_line = "\"%s: %s" % (line[0], kw[k])
                    vim.current.buffer[end] = new_line
            end += 1

    def refresh_from_buffer(self):
        self.parse_buffer()

        meta = self.buffer_meta
        struct = self.post_struct_meta

        struct.update(title=meta["title"],
                wp_slug=meta["slug"], post_type=self.EDIT_TYPE)

        if self.EDIT_TYPE == "post":
            struct.update(categories=meta["cats"].split(','),
                    mt_keywords=meta["tags"].split(','))

        self.rawtext = rawtext = meta["content"]

        #Translate markdown and save in custom fields.
        if meta["editformat"].lower() == "markdown":
            for f in struct["custom_fields"]:
                if f["key"] == VRP_CONST.CUSTOM_FIELD_KEY():
                    f["value"] = rawtext
                    break
             # Not found, add new custom field.
            else:
                field = dict(key=VRP_CONST.CUSTOM_FIELD_KEY(), value=rawtext)
                struct["custom_fields"].append(field)

            struct["description"] = self.html_text = markdown.markdown(rawtext)
        else:
            struct["description"] = self.html_text = rawtext

    def refresh_from_wp(self, post_id):

        # get from wp
        self.post_struct_meta = struct = getattr(g_data.oXMLRPC,
                "get_" + self.EDIT_TYPE)(post_id)

        # struct buffer meta
        meta = dict(editformat="HTML",
                title=struct["title"],
                slug=struct["wp_slug"])

        if self.EDIT_TYPE == "post":
            meta.update(strid=str(struct["postid"]),
            cats=", ".join(struct["categories"]),
            tags=struct["mt_keywords"])
            MORE_KEY = "mt_text_more"
        else:
            meta.update(strid=str(struct["page_id"]))
            MORE_KEY = "text_more"

        self.html_text = content = struct["description"]

        # detect more text
        post_more = struct.get(MORE_KEY, '')
        if len(post_more) > 0:
            content += '<!--more-->' + post_more
            struct[MORE_KEY] = ''
            self.html_text = struct["description"] = content

        # Use Markdown text if exists in custom fields
        for field in struct["custom_fields"]:
            if field["key"] == VRP_CONST.CUSTOM_FIELD_KEY():
                meta['editformat'] = "Markdown"
                self.raw_text = content = field["value"]
                vim.command("set ft=markdown")
                break
        else:
            self.raw_text = content

        meta["content"] = content

        self.buffer_meta.update(meta)

    def save_post(self):
        ps = self.post_struct_meta
        if self.EDIT_TYPE == "post":
            if ps.get("postid", '') == '' and self.post_id == '':
                post_id = g_data.oXMLRPC.new_post(ps)
            else:
                post_id = ps["postid"] if "postid" in ps \
                        else int(self.post_id)
                g_data.oXMLRPC.edit_post(post_id, ps)
        else:
            if ps.get("page_id", '') == '' and self.post_id == '':
                post_id = g_data.oXMLRPC.new_post(ps)
            else:
                post_id = ps["page_id"] if "page_id" in ps \
                        else int(self.post_id)
                g_data.oXMLRPC.edit_post(post_id, ps)

        self.refresh_from_wp(post_id)

    post_status = property(lambda self:
            self.post_struct_meta[self.EDIT_TYPE + "_status"])

    @post_status.setter
    def post_status(self, data):
        if data is not None:
            self.post_struct_meta[self.EDIT_TYPE + "_status"] = data

    post_id = property(lambda self: self.buffer_meta["strid"])

    def html_preview(self):
        """
        Opens a browser with a local preview of the content.
        @params text_html - the html content
                meta      - a dictionary of the meta data
        """
        if g_data.vimpress_temp_dir == '':
            g_data.vimpress_temp_dir = tempfile.mkdtemp(suffix="vimpress")

        html = \
                """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"> <title>Vimpress Local Preview: %(title)s</title> <style type="text/css"> ul, li { margin: 1em; } :link,:visited { text-decoration:none } h1,h2,h3,h4,h5,h6,pre,code { font-size:1.1em; } h1 {font-size: 1.8em;} h2 {font-size: 1.5em;} h3{font-size: 1.3em;} h4{font-size: 1.2em;} h5 {font-size: 1.1em;} a img,:link img,:visited img { border:none } body { margin:0 auto; width:770px; font-family: Helvetica, Arial, Sans-serif; font-size:12px; color:#444; } </style> </meta> </head> <body> %(content)s </body> </html>
""" % dict(content=self.html_text, title=self.buffer_meta["title"])
        with open(os.path.join(
                g_data.vimpress_temp_dir, "vimpress_temp.html"), 'w') as f:
            f.write(html)
        webbrowser.open("file://%s" % f.name)

    def remote_preview(self, pub="draft"):
        self.post_status = pub
        self.save_post()
        webbrowser.open("%s?p=%s&preview=true" %
                (g_data.blog_url, self.post_id))


#################################################
# Global Variables
#################################################
g_data = DataObject()

#################################################
# Helper Functions
#################################################

"""
    Decorator.
    Check vim environment. wordpress via xmlrpc only support unicode data,
    setting vim to utf-8 for all data compatible.
"""

def vim_encoding_check(func):

    def __check(*args, **kw):
        orig_enc = vim.eval("&encoding")
        if orig_enc is None:
            echomsg("Failed to detect current text encoding.")
            echomsg("%s expects utf-8 encoded text." % VRP_CONST.APP_NAME())
        elif orig_enc != "utf-8":
            modified = vim.eval("&modified")

            # CONVERTS CURRENT BUFFER TO UTF-8
            buf_list = '\n'.join(vim.current.buffer).decode(orig_enc, 'strict').splitlines()
            del vim.current.buffer[:]
            vim.command("setl encoding=utf-8")

            # 2016-12-05: JSTEWART: FIXED INDEX ERROR BY CHANGING FROM 1 TO 0
            # REFILL BUFFER AFTER CONVERSION
            if len(buf_list) > 0:
                vim.current.buffer.append(buf_list[0:])

            if modified == '0':
                vim.command('setl nomodified')

        return func(*args, **kw)
    return __check

"""
    Decorator.
    For commands to switch between edit/list view, data/status need to be configured.
"""
def view_switch(view = "", assert_view = "", reset = False):

    def switch(func):
        def __run(*args, **kw):
            if assert_view != '':
                if g_data.view != assert_view:
                    raise VRP_Exception("Command only available at '%s' view." % assert_view)

            if func.__name__ == "blog_new":
                if g_data.view == "list":
                    kw["currentContent"] = ['']
                else:
                    kw["currentContent"] = vim.current.buffer[:]
            elif func.__name__ == "blog_config_switch":
                if g_data.view == "list":
                    kw["refresh_list"] = True

            if reset:
                g_data.oXMLRPC.cache_reset()

            if view != '':
                # Switching view
                if g_data.view != view:

                    # from list view
                    if g_data.view == "list":
                        for v in list(VRP_CONST.LIST_VIEW_KEY_MAP().values()):
                            if vim.eval("mapcheck('%s')" % v):
                                vim.command('unmap <buffer> %s' % v)

                    g_data.view = view

            return func(*args, **kw)
        return __run
    return switch

"""
    Wisely decides whether to wipe out the content of current buffer or open a new splited window.
"""
def blog_wise_open_view():

    curBuf  = vim.current.buffer
    bufname = curBuf.name
    bEmpty  = False
    bNoMod  = False

    if( vim.eval('&modified') == '0' ):
       bNoMod = True

    if( (len(curBuf) <= 1) and (len(curBuf[0]) <= 1) ):
       bEmpty = True

    # 2016-12-05: JSTEWART: BUFFER NAME LENGTH CHECK IN ADDITION TO None CHECK
    #                       WINDOWS WERE MULTIPLYING LIKE RABBITS SINCE
    #                       buffer.name NEVER SEEMS TO EVALUATE TO None
    if( ((bufname is None) or (len(bufname) == 0)) and (bNoMod or bEmpty) ):
        vim.command('setl modifiable')
        del vim.current.buffer[:]
        vim.command('setl nomodified')
    else:
        vim.command(":new")

    vim.command('setl syntax=blogsyntax')
    vim.command('setl completefunc=vimrepress#CateComplete')


@vim_encoding_check
def vim_input(message = 'input', secret = False):
    CONST_VAR_INPUT = "g:vimpressInput"
    vim.command('call inputsave()')
    szCmd = "let %s = %s('%s :')" % (CONST_VAR_INPUT, ("inputsecret" if secret else "input"), message)
    vim.command(szCmd)
    valRet = vim.eval(CONST_VAR_INPUT)
    vim.command('call inputrestore()')
    echomsg("\n \n", False)
    return valRet


#################################################
# Command Functions
#################################################

"""
    Saves the current editing buffer.
    @params pub - either "draft" or "publish"
"""
@exception_check
@vim_encoding_check
@view_switch(assert_view = "edit", reset = True)
def blog_save(pub = None):

    if pub not in ("publish", "draft", None):
        raise VRP_Exception(":BlogSave draft|publish")
    cp = g_data.current_post
    VRP_Assert(cp is not None, "Can't get current post obj.")
    cp.refresh_from_buffer()

    if cp.buffer_meta["blogaddr"] != g_data.blog_url and cp.post_id != '':
        confirm = vim_input("Are u sure saving it to \"%s\" ? BlogAddr in current buffer does NOT matched. \nStill saving it ? (may cause data lost) [yes/NO]" % g_data.blog_url)
        VRP_Assert(confirm.lower() == 'yes', "Aborted.", True)

    cp.post_status = pub
    cp.save_post()
    cp.update_buffer_meta()
    g_data.current_post = cp
    notify = "%s ID=%s saved with status '%s'" % (cp.post_status, cp.post_id, cp.post_status)
    echomsg(notify)
    vim.command('setl nomodified')

"""
    Creates a new editing buffer of specified type.
    @params edit_type - either "post" or "page"
"""
@exception_check
@vim_encoding_check
@view_switch(view = "edit")
def blog_new(edit_type = "post", currentContent = None):

    if edit_type.lower() not in ("post", "page", "category"):
        raise VRP_Exception("Invalid option: %s " % edit_type)

    if edit_type.lower() == "category":
        category_name = vim_input("New Category name")
        category_slug = vim_input("Category slug (optional)")
        ret = g_data.oXMLRPC.new_category(dict(name = category_name, slug = category_slug))

        if type(ret) is int:
            echomsg("Category '%s' created with ID %d. Updating local cache ... "
                    % (category_name, ret))
            categories = [i["categoryName"]
                    for i in g_data.oXMLRPC.get_categories()]
            vim.command('let s:completable = "%s"' % '|'.join(categories))
            echomsg("Done.")
        else:
            echoerr("(CATEGORY CREATE) %s" % str(ret))

    else:
        blog_wise_open_view()
        g_data.current_post = ContentStruct(edit_type = edit_type)
        cp = g_data.current_post
        cp.fill_buffer()

"""
    Opens a new editing buffer with blog content of specified type and id.
    @params edit_type - either "post" or "page"
            post_id   - the id of the post or page
"""
@view_switch(view = "edit")
def blog_edit(edit_type, post_id):

    blog_wise_open_view()
    if edit_type.lower() not in ("post", "page"):
        raise VRP_Exception("Invalid option: %s " % edit_type)
    post_id = str(post_id)

    if post_id in g_data.post_cache:
        cp = g_data.current_post = g_data.post_cache[post_id]
    else:
        cp = g_data.current_post = ContentStruct(edit_type = edit_type, post_id = post_id)

    cp.fill_buffer()
    vim.current.window.cursor = (cp.POST_BEGIN, 0)
    vim.command('setl nomodified')
    vim.command('setl textwidth=0')
    for v in list(VRP_CONST.LIST_VIEW_KEY_MAP().values()):
        if vim.eval("mapcheck('%s')" % v):
            vim.command('unmap <buffer> %s' % v)


"""
    Deletes a page or post of specified id.
    @params edit_type - either "page" or "post"
            post_id   - the id of the post or page
"""
@view_switch(assert_view = "list")
def blog_delete(edit_type, post_id):
    if edit_type.lower() not in ("post", "page"):
        raise VRP_Exception("Invalid option: %s " % edit_type)
    deleted = getattr(g_data.oXMLRPC, "delete_" + edit_type)(post_id)
    VRP_Assert(deleted is True, "There was a problem deleting the %s." % edit_type)
    echomsg("Deleted %s id %s." % (edit_type, str(post_id)))
    g_data.oXMLRPC.cache_remove_post(post_id)
    blog_list(edit_type)

"""
    Calls blog open on the current line of a listing buffer.
"""
@exception_check
@view_switch(assert_view = "list")
def blog_list_on_key_press(action, edit_type):
    if action.lower() not in ("open", "delete"):
        raise VRP_Exception("Invalid option: %s" % action)

    row = vim.current.window.cursor[0]
    line = vim.current.buffer[row - 1]
    id = line.split()[0]
    title = line[len(id):].strip()

    try:
        int(id)
    except ValueError:
        if line.find("More") != -1:
            VRP_Assert(g_data.oXMLRPC.is_reached_title_max is False, "No more posts.", True)
            vim.command("setl modifiable")
            del vim.current.buffer[len(vim.current.buffer) - 1:]
            append_blog_list(edit_type)
            vim.current.buffer.append(VRP_CONST.MARKER()['more'])
            vim.command("setl nomodified")
            vim.command("setl nomodifiable")
            return
        else:
            raise VRP_Exception("Move cursor to a post/page line and press Enter.")

    if len(title) > 30:
        title = title[:30] + ' ...'

    if action.lower() == "delete":
        confirm = vim_input("Confirm Delete [%s]: %s? [yes/NO]" % (id, title))
        VRP_Assert(confirm.lower() == 'yes', "Delete Aborted.", True)

    vim.command("setl modifiable")
    del vim.current.buffer[:]
    vim.command("setl nomodified")

    if action == "open":
        blog_edit(edit_type, int(id))
    elif action == "delete":
        blog_delete(edit_type, int(id))


def append_blog_list(edit_type, count = VRP_CONST.DEFAULT_LIST_COUNT()):
    if edit_type.lower() == "post":
        current_posts = len(vim.current.buffer) - 1
        retrive_count = int(count) + current_posts
        posts_titles = g_data.oXMLRPC.get_recent_post_titles(retrive_count)

        vim.current.buffer.append(
                [("%(postid)s\t%(title)s" % p)
                    for p in posts_titles[current_posts:]])
    else:
        pages = g_data.oXMLRPC.get_page_list()
        vim.current.buffer.append(
            [("%(page_id)s\t%(page_title)s" % p) for p in pages])

def objDump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

"""
    Creates a listing buffer of specified type.
    @params edit_type - either "post(s)" or "page(s)"
"""
@exception_check
@vim_encoding_check
@view_switch(view = "list")
def blog_list(edit_type = "post", keep_type = False):

    if keep_type:
        first_line = vim.current.buffer[0]
        VRP_Assert(first_line.find("List") != -1, "Failed to detect current list type.")
        edit_type = first_line.split()[1].lower()

    blog_wise_open_view()
    vim.current.buffer[0] = VRP_CONST.MARKER()["list_title"] % \
                                dict(edit_type = edit_type.capitalize(), blog_url = g_data.blog_url)

    if edit_type.lower() not in ("post", "page"):
        raise VRP_Exception("Invalid option: %s " % edit_type)

    append_blog_list(edit_type, VRP_CONST.DEFAULT_LIST_COUNT())

    if edit_type == "post":
        vim.current.buffer.append(VRP_CONST.MARKER()['more'])

    vim.command("setl nomodified")
    vim.command("setl nomodifiable")
    vim.current.window.cursor = (2, 0)

    vim.command("map <silent> <buffer> %(enter)s :py3 blog_list_on_key_press('open', '%%s')<CR>"
            % VRP_CONST.LIST_VIEW_KEY_MAP() % edit_type)
    vim.command("map <silent> <buffer> %(delete)s :py3 blog_list_on_key_press('delete', '%%s')<CR>"
            % VRP_CONST.LIST_VIEW_KEY_MAP() % edit_type)

    echomsg("Press <Enter> to edit. <Delete> to move to trash.")


"""
    Uploads a file to the blog.
    @params file_path - the file's path
"""
@exception_check
@vim_encoding_check
@view_switch(assert_view = "edit")
def blog_upload_media(file_path):

    if not os.path.exists(file_path):
        raise VRP_Exception("File does not exist: %s" % file_path)

    name = os.path.basename(file_path)
    filetype = mimetypes.guess_type(file_path)[0]
    with open(file_path, mode='rb') as f:
        bits = xmlrpc.client.Binary(f.read())

    result = g_data.oXMLRPC.new_media_object(dict(name = name, type = filetype, bits = bits))

    ran = vim.current.range
    if filetype.startswith("image"):
        img = VRP_CONST.IMAGE_TEMPLATE() % result
        ran.append(img)
    else:
        ran.append(result["url"])
    ran.append('')


@exception_check
@vim_encoding_check
@view_switch(assert_view = "edit")
def blog_append_code(code_type = ""):
    html = \
"""<pre lang="%s"%s>
</pre>"""
    if code_type == "":
        code_type = ("text", "")
    else:
        code_type = (code_type, ' line="1"')
    html = html % code_type
    row, col = vim.current.window.cursor
    code_block = html.splitlines()
    vim.current.range.append(code_block)
    vim.current.window.cursor = (row + len(code_block), 0)


@exception_check
@vim_encoding_check
@view_switch(assert_view = "edit")
def blog_preview(pub = "local"):
    """
    Opens a browser window displaying the content.
    @params pub - If "local", the content is shown in a browser locally.
                  If "draft", the content is saved as a draft and previewed remotely.
                  If "publish", the content is published and displayed remotely.
    """
    cp = g_data.current_post
    cp.refresh_from_buffer()
    if pub == "local":
        cp.html_preview()
    elif pub in ("publish", "draft"):
        cp.remote_preview(pub)
        if pub == "draft":
            echomsg("You have to login in the browser to preview the post when save as draft.")
    else:
        raise VRP_Exception("Invalid option: %s " % pub)


@exception_check
def blog_guess_open(what):
    """
    Tries several methods to get the post id from different user inputs, such as args, url, postid etc.
    """
    post_id    = ''
    blog_index = -1

    if type(what) is str:

        for ix, oCfg in enumerate(g_data.config):
            if what.startswith(oCfg["blog_url"]):
                blog_index = ix

        # User input a url contained in the profiles
        if blog_index != -1:
            guess_id = re.search(r"\S+?p=(\d+)$", what)

            # permalinks
            if guess_id is None:

                # try again for /archives/%post_id%
                guess_id = re.search(r"\S+/archives/(\d+)", what)

                # fail,  try get full link from headers
                if guess_id is None:

                    httpResp = urllib.request.urlopen(what)
                    links = httpResp.getheaders()

                    for key, val in links:
                        if key == 'Link':
                            oFind = re.search(r"<\S+?p=(\d+)>", val)
                            if oFind is not None:
                                post_id = oFind.group(1)

                else:
                    post_id = guess_id.group(1)

            # full link with ID (http://blog.url/?p=ID)
            else:
                post_id = guess_id.group(1)

            # detected something ?
            VRP_Assert(post_id != '', "Failed to get post/page id from '%s'." % what)

            # switch view if needed.
            if blog_index != -1 and blog_index != g_data.conf_index:
                blog_config_switch(blog_index)

        # User input something not a usable URL, try numeric
        else:
            try:
                post_id = str(int(what))
            except ValueError:
                raise VRP_Exception("Failed to get post/page id from '%s'." % what)

        blog_edit("post", post_id)


@exception_check
@vim_encoding_check
@view_switch()
def blog_config_switch(index = -1, refresh_list = False):
    """
    Switches the blog to the 'index' of the configuration array.
    """
    g_data.conf_index = index
    if refresh_list:
        blog_list(keep_type = True)
    echomsg("%s switched to '%s'@'%s'" % (VRP_CONST.APP_NAME(), g_data.blog_username, g_data.blog_url))
