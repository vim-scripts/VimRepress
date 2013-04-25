#Welcome
VimRepress is a plugin for managing WordPress blog from Vim, using Markdown syntax.

##Features
 * NEW/EDIT/DELETE WordPress Posts/Pages.
 * In both Markdown / HTML format.
 * Markdown text can be configured to be stored in the custom fields of WordPress.
 * Upload attachments.
 * Insert code highlight section.
 * Preview a posts in local compiled version, or remote draft.
 * WordPress.com account supported.
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

    [Blog1]
    blog_url = https://blog1.wordpress.com/
    username = someone
    password =
    store_markdown = n

    [BlogWhatEver]
    blog_url = https://someone.wordpress.com/
    username = someone
    password =

Hardcoding the password is optional. If a password is not provided the plugin will prompt for one the first time it's needed.

`store_markdown` is also optional. If not specified then Markdown text will be stored in custom fields of WordPress. If set to `n` then the Markdown text will not be stored.

###For Upgraded Users

Defining account info in `.vimrc` is now obsolesced, if you have correspond defination in `.vimrc` (for older version vimpress), they will automaticly copied into `~/.vimpressrc`, now you're safe to remove the VIMPRESS defination in `.vimrc`.

Users from the 2.x.x versions of vimrepress, need to run the `markdown_posts_upgrade.py` to upgrade the their posts data to be compatible with the 3.x.x version of vimrepress, or their Markdown source can not be used to re-edit by a newer vimrepress. 


