# VimRepressPy3

### Edit your WordPress blog from Vim.

   - Write with Markdown, control posts format precisely.
   - Stores Markdown rawtext in WordPress custom fields.
   - Supports github-style fenced code-blocks.

### Requirements:

   - Vim 7.3+ with Python 3 support
   - Python Environment matched wtih Vim's support
   - requires `markdown` & `pygments` modules
   - WordPress 3.0.0+

### Configuration:

Create account configure as `~/.vimpressrc` in the following format (be sure to `chmod 600` this file):

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

### Pygments CSS

To get pygments higlighting for fenced codeblocks, you will need to generate pygments CSS for your preferred colorscheme, and include it with your site CSS:

```sh
pygmentize -f html -a .pygment -S <style_name>
```

To see the list of available pygments styles on your computer:

```sh
pygmentize -L styles
```

Or use their online demo at https://pygments.org/demo/.

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
