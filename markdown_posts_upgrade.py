#!/usr/bin/env python2
import urllib2, xmlrpclib, re, os, sys
import getpass

class VimPressException(Exception):
    pass

class VimPressFailedGetMkd(VimPressException):
    pass


class DataObject(object):

    #CONST
    DEFAULT_LIST_COUNT = "15"
    IMAGE_TEMPLATE = '<a href="%(url)s"><img title="%(file)s" alt="%(file)s" src="%(url)s" class="aligncenter" /></a>'
    MARKER = dict(bg = "=========== Meta ============", 
                  mid = "=============================", 
                  ed = "========== Content ==========",
                  more = '"====== Press Here for More ======',
                  list_title = '"====== %(edit_type)s List in %(blog_url)s =========')
    LIST_VIEW_KEY_MAP = dict(enter = "<enter>", delete = "<delete>")
    DEFAULT_META = dict(strid = "", title = "", slug = "", 
                        cats = "", tags = "", editformat = "Markdown", 
                        edittype = "post", textattach = '')
    TAG_STRING = "<!-- #VIMPRESS_TAG# %(url)s %(file)s -->"
    TAG_RE = re.compile(TAG_STRING % dict(url = '(?P<mkd_url>\S+)', file = '(?P<mkd_name>\S+)'))
    CUSTOM_FIELD_KEY = "mkd_text"

    #Temp variables.
    __xmlrpc = None
    __conf_index = 0
    __config = None

    view = 'edit'
    vimpress_temp_dir = ''

    blog_username = property(lambda self: self.xmlrpc.username)
    blog_url = property(lambda self: self.xmlrpc.blog_url)
    conf_index = property(lambda self:self.__conf_index)

    xmlrpc = None


class wp_xmlrpc(object):

    def __init__(self, blog_url, username, password):
        self.blog_url = blog_url
        self.username = username
        self.password = password
        p = xmlrpclib.ServerProxy(os.path.join(blog_url, "xmlrpc.php"))
        self.mw_api = p.metaWeblog
        self.wp_api = p.wp
        self.mt_api = p.mt
        self.demo_api = p.demo

        assert self.demo_api.sayHello() == "Hello!", "XMLRPC Error with communication with '%s'@'%s'" % \
                (username, blog_url)

        self.cache_reset()

    def cache_reset(self):
        self.__cache_post_titles = []
        self.__post_title_max = False

    def cache_remove_post(self, postid):
        for p in self.__cache_post_titles:
            if p["postid"] == str(postid):
                self.__cache_post_titles.remove(p)
                break

    is_reached_title_max = property(lambda self: self.__post_title_max)

    new_post = lambda self, post_struct, is_publish: self.mw_api.newPost('',
            self.username, self.password, post_struct, is_publish)

    get_post = lambda self, post_id: self.mw_api.getPost(post_id,
            self.username, self.password) 

    edit_post = lambda self, post_id, post_struct: self.mw_api.editPost(post_id,
            self.username, self.password, post_struct )

    delete_post = lambda self, post_id: self.mw_api.deletePost('', post_id, self.username,
            self.password, '') 

    def get_recent_post_titles(self, retrive_count = 0):
        if retrive_count > len(self.__cache_post_titles) and not self.is_reached_title_max:
            self.__cache_post_titles = self.mt_api.getRecentPostTitles('',
                    self.username, self.password, retrive_count)
            if len(self.__cache_post_titles) < retrive_count:
                self.__post_title_max = True

        return self.__cache_post_titles

    get_categories = lambda self:self.mw_api.getCategories('', self.username, self.password)

    new_media_object = lambda self, object_struct: self.mw_api.newMediaObject('', self.username,
            self.password, object_struct)

    get_page = lambda self, page_id: self.wp_api.getPage('', page_id, self.username, self.password) 

    delete_page = lambda self, page_id: self.wp_api.deletePage('',
            self.username, self.password, page_id) 

    get_page_list = lambda self: self.wp_api.getPageList('', self.username, self.password) 

def blog_get_mkd_attachment(post):
    """
    Attempts to find a vimpress tag containing a URL for a markdown attachment and parses it.
    @params post - the content of a post
    @returns a dictionary with the attachment's content and URL
    """
    attach = dict()
    try:
        lead = post.rindex("<!-- ")
        data = re.search(g_data.TAG_RE, post[lead:])
        if data is None:
            raise VimPressFailedGetMkd("Attached markdown not found.")
        attach.update(data.groupdict())
        attach["mkd_rawtext"] = urllib2.urlopen(attach["mkd_url"]).read()
    except (IOError, ValueError):
        raise VimPressFailedGetMkd("The attachment URL was found but was unable to be read.")

    return attach

def blog_update(post, content, attach):
    lead = content.rindex("<!-- ")
    new_content = content[:lead]
    markdown_text = attach["mkd_rawtext"]
    post_struct = post

    try:
        strid = post["postid"]
    except KeyError:
        strid = post["page_id"]

    if len(new_content.strip()) == 0:
        new_content = 'Empty Post'

    post_struct["description"] = new_content

    if len(markdown_text) > 0:
        for f in post_struct["custom_fields"]:
            if f["key"] == g_data.CUSTOM_FIELD_KEY:
                f["value"] = markdown_text
                break
        else:
            post_struct["custom_fields"].append(dict(key = g_data.CUSTOM_FIELD_KEY, value = markdown_text))

    try:
        g_data.xmlrpc.edit_post(strid, post_struct )
    except xmlrpclib.Fault, e:
        raise


def post_struct_get_content(data):
    content = data["description"]
    post_more = data.get("mt_text_more", '')
    page_more = data.get("text_more", '')

    if len(post_more) > 0:
        content += '<!--more-->' + post_more
    elif len(page_more) > 0:
        content += '<!--more-->' + page_more

    return content

def loop_proccess_posts(posts, edit_type):
    print "ID           Title"
    for post in posts:
        if edit_type == "page":
            print u"%(page_id)s\t%(page_title)s" % post, '... ',
            sys.stdout.flush()
            page_id = post["page_id"].encode("utf-8")
            data = g_data.xmlrpc.get_page(page_id)
        elif edit_type == "post":
            print u"%(postid)s\t%(title)s  ... " % post, 
            sys.stdout.flush()
            post_id = post["postid"].encode("utf-8")
            data = g_data.xmlrpc.get_post(post_id)

        content = post_struct_get_content(data)
        try:
            attach = blog_get_mkd_attachment(content)
        except VimPressFailedGetMkd:
            print "No Markdown Attached."
        else:
            blog_update(data, content, attach)
            attachements_proccessed.append(attach["mkd_name"])
            print "Updated."

    print "\n\n"

print """

Vimrepress 3.x upgrade script

WHY:

    The older (2.x) vimrepress stores your originally
    written markdown text in an attachment with the
    post on wordpress.

    A better way is implemented in the new (3.x)
    vimrepress, the markdown texts stores in the custom
    field of a post.

    If you used vimrepress 2.x to write your blog before,
    and want the 3.x to be able to edit your old posts,
    this script is needed to convert the attachments 
    content into the custom field.

HOW:
    
    Fillin the address/username/password as asked, script 
    will scan through your posts, when a markdown attached
    post found, it will download and read it into the
    database.

I tested this script works flawlessly to my own blog,
but I don't guarantee no exceptions in other circumstance,
I don't respons for any data lost.

Backup your wordpress with this plugin: WP-DB-Backup  
 ( http://wordpress.org/extend/plugins/wp-db-backup/ )

or phpmyadmin/adminer/mysqldump anything you like it most.

                          WARNNING
#########################################################
Warnning: Backup your wordpress database before procceed.
Warnning: Backup your wordpress database before procceed.
Warnning: Backup your wordpress database before procceed.
#########################################################
"""

URL = raw_input("Blog URL: ")
USER = raw_input("USERNAME: ")
PASS = getpass.getpass()

i = raw_input("Have you backed up your wordpress database? [y/N]")
if i.lower() == 'n' or i == '':
    print "----> Go and do that, don't risk your data."
    sys.exit(1)

g_data = DataObject()
g_data.xmlrpc = wp_xmlrpc(URL, USER, PASS)

attachements_proccessed = []

i = raw_input("Upgrade pages ?[Y/n]")
if i.lower() == 'y' or i == '':
    print "Upgrade pages ..." 
    pages = g_data.xmlrpc.get_page_list()
    loop_proccess_posts(pages, "page")

i = raw_input("Upgrade Posts ?[Y/n]")
if i.lower() == 'y' or i == '':
    count = raw_input("How many recent posts to process? [100]")
    if count == '':
        count = '100'
    assert isinstance(int(count), int), "input a integer please."
    posts = g_data.xmlrpc.get_recent_post_titles(count)
    loop_proccess_posts(posts, "post")

if len(attachements_proccessed) > 0:
    print "All Done. Congras."
    print "You may now delete this attachments from wordpress panel."
    print URL+"/wp-admin/upload.php"
    print 
    print "\n".join(attachements_proccessed)


