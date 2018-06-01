# VimRepressPy3: Edit your WordPress blog from Vim.

   - A mod of a mod of a mod of Vimpress, updated for Python 3.
   - A vim plugin for writting your WordPress blog.
   - Write with Markdown, control posts format precisely.
   - Stores Markdown rawtext in WordPress custom fields.

### Requirements:

   - Vim 7.3+ with Python 3 support
   - Python Environment matched wtih Vim's support
   - `python-markdown` / `python-markdown2` installed
   - WordPress 3.0.0+

### Configuration:

Create account configure as `~/.vimpressrc` in the following format:

```
[Blog0]
blog_url = http://a-blog.com/
username = admin
password = 123456

[Blog1]
blog_url = https://someone.wordpress.com/
username = someone
password =
```

### Command Examples:

```

   :BlogList             -  List 30 recent posts.
   :BlogList page        -  List 30 recent pages.
   :BlogList post 100    -  List 100 recent posts.

   :BlogNew post         -  Write a new post.
   :BlogNew page         -  Write a new page.

   :BlogSave             -  Save (defautely published.)
   :BlogSave draft       -  Save as draft.

   :BlogPreview local    -  Preview page/post locally in your browser.
   :BlogPreview publish  -  Same as `:BlogSave publish' with browser opened.

   :BlogOpen 679
   :BlogOpen http://your-first-blog.com/archives/679
   :BlogOpen http://your-second-blog.com/?p=679
   :BlogOpen http://your-third-blog.com/with-your-custom-permalink

```

For more details, type `:help vimpress` after this plugin has been loaded.

### Contributors:

   - Adrien Friggeri <adrien@friggeri.net>
   - Pigeond <http://pigeond.net/blog/>
   - Justin Sattery <justin.slattery@fzysqr.com>
   - Lenin Lee <lenin.lee@gmail.com>
   - Conner McDaniel <connermcd@gmail.com>
   - Preston M.[BOYPT] <pentie@gmail.com>
   - Jason Stewart <support@eggplantsd.com>
