#Welcome
VimRepress is a plugin for managing wordpress blog from Vim, using Markdown syntax.

##Features
 * NEW/EDIT/DELETE wordpress Posts/Pages.
 * In both Markdown / HTML format.
 * Markdown text stored in the custom fields of wordpress.
 * Upload attachments.
 * Insert code highlight section.
 * Preview a posts in local compiled version, or remote draft.
 * wordpress.com account supported.
 * Multiple account supported.

##Commands Reference
 * BlogList     [post|page]
 * BlogNew      [post|page]
 * BlogSave     [publish|draft]
 * BlogPreview  [local|publish|draft]
 * BlogUpload   *[path/to/your/local/file]
 * BlogOpen     *[post id or full article URL]
 * BlogSwitch   [0,1,2 ... N, number of account in your config]
 * BlogCode     [type of lang for the \<pre\> element]
 
  (Commands with a `*`, argument must be present.)


##CONFIGURE

Create file `~/.vimpressrc` in the following format:

    [Blog0]
    blog_url = http://a-blog.com/
    username = admin
    password = 123456

    [BlogWhatEver]
    blog_url = https://someone.wordpress.com/
    username = someone
    password =

Hardcoding the password is optional. If a password is not provided the plugin will prompt for one the first time it's needed.

###For Upgraded Users

Defining account info in `.vimrc` is now obsolesced, if you have correspond defination in `.vimrc` (for older version vimpress), they will automaticly copied into `~/.vimpressrc`, now you're safe to remove the VIMPRESS defination in `.vimrc`.

Users from the 2.x.x versions of vimrepress, need to run the `markdown_posts_upgrade.py` to upgrade the their posts data to be compatible with the 3.x.x version of vimrepress, or their Markdown source can not be used to re-edit by a newer vimrepress. 


