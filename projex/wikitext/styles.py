""" Shell file for the projex.wikitext.commands module. """

# define standard templates
basic = {
    # overall page
    'wiki_open': '<{tag} class="wiki">',
    'wiki_close': '</{tag}>',

    # globals
    'newline': '<br>',
    'spacer': '<br><br>',
    'paragraph_open': '<br><div class="wiki">',
    'paragraph_close': '</div>',
    'hr': '<hr class="{style}">',
    'header': '<a name="{name}"></a><h{size} class="wiki">{title}</h{size}>',
    'underline': '<u>{text}</u>',
    'strikeout': '<s>{text}</s>',
    'bold': '<b>{text}</b>',
    'italic': '<i>{text}</i>',
    'inline_code': '<pre>{text}</pre>',
    'img': '<a href="{url}"><img class="thumb" alt="{title}" style="{style}" src="{url}"></a>',
    'color': '<span style="color:{color}">{text}</span>',
    'span': '<span style="{style}">{text}</span>',

    # alignment
    'align_center': '<div align="center">',
    'align_center_floated': '<div style="float:center">',
    'align_close': '</div>',
    'align_left': '<div align="left">',
    'align_left_floated': '<div style="float:right">',
    'align_right': '<div align="right">',
    'align_right_floated': '<div style="float:right">',

    # nowiki
    'nowiki_open': '<pre class="nowiki">',
    'nowiki_close': '</pre>',

    # links
    'link_class': '<a href="{url}" class="code-class">{text}</a>',
    'span_class': '<span class="type">{crumbs}</span>',
    'link_ext': '<a class="wiki_external" href="{url}">{text}</a>',
    'link_found': '<a class="wiki_standard" href="{url}">{text}</a>',
    'link_not_found': '<a class="wiki_missing" href="{url}">{text}</a>',

    # tables
    'table_open': '<table class="wiki">',
    'table_row': '<tr>{text}</tr>',
    'table_cell': '<{tag} style="{style}">{text}</{tag}>',
    'table_close': '</table>',

    # toc
    'toc_open': '<div class="toc"><h2>Contents</h2>',
    'toc_close': '</div>',

    # lists
    'ordered_list_open': '<ol class="wiki">',
    'ordered_list_close': '</ol>',
    'unordered_list_open': '<ul class="wiki">',
    'unordered_list_close': '</ul>',
    'list_item_open': '<li>',
    'list_item_close': '</li>',

    # sections
    'section_open': '<div class="wiki_section {name}"><strong>{title}</strong>',
    'section_close': '</div>',
    'section_alert_open': '<div class="wiki_section {name}"><strong>{title}</strong>',
    'section_alert_close': '</div>',

    # code
    'code_open': '<small><i>{lang}</i></small><pre class="prettyprint lang-{lang} code">',
    'code_close': '</pre>'
}

# define bootstrap templates
bootstrap = basic.copy()
bootstrap['header'] = '<a name="{name}"></a><h{size}>{title}</h{size}>'
bootstrap['align_center'] = '<div class="center-block"><p class="text-center">'
bootstrap['align_center_floated'] = '<div class="center-block"><p class="text-center">'
bootstrap['align_close'] = '</p></div>'
bootstrap['align_left'] = '<div class="center-block"><p class="text-left">'
bootstrap['align_left_floated'] = '<div class="pull-left"><p class="text-left">'
bootstrap['align_right'] = '<div class="center-block"><p class="text-right">'
bootstrap['align_right_floated'] = '<div class="pull-right"><p class="text-right">'
bootstrap['paragraph_open'] = '<p>'
bootstrap['paragraph_close'] = '</p>'
bootstrap['strikeout'] = '<strike>{text}</strike>'
bootstrap['italic'] = '<em>{text}</em>'
bootstrap['inline_code'] = '<code>{text}</code>'
bootstrap['bold'] = '<strong>{text}</strong>'
bootstrap['code_open'] = '<pre><code class="{lang}">'
bootstrap['code_close'] = '</code></pre>'
bootstrap['link_class'] = '<a class="link link-default" href="{url}">{text}</a>'
bootstrap['link_ext'] = '<a class="link link-default" href="{url}">{text}</a>'
bootstrap['link_found'] = '<a class="link link-success" href="{url}">{text}</a>'
bootstrap['link_not_found'] = '<a class="link link-danger" href="{url}">{text}</a>'
bootstrap['section_open'] = '<dl><dt>{title}</dt><dd>'
bootstrap['section_close'] = '</dd></dl>'
bootstrap['section_alert_open'] = '<div class="alert alert-{name}"><strong>{title}:</strong>'
bootstrap['section_alert_close'] = '</div>'
bootstrap['table_open'] = '<table class="table table-wiki">'

# define the styles dictionary
styles = {
    'basic': basic,
    'bootstrap': bootstrap
}
