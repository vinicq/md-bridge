---
title: "Markdown - Wikipedia"
date: "2026-06-02"
source: "wikipedia-markdown-en.pdf"
pages: 9
---

# Markdown

**Markdown**^\[9\]^ is a [lightweight](https://en.wikipedia.org/wiki/Lightweight_markup_language) [markup](https://en.wikipedia.org/wiki/Lightweight_markup_language) language for creating formatted text using a [plain-text](https://en.wikipedia.org/wiki/Text_editor) editor. [John](https://en.wikipedia.org/wiki/John_Gruber) Gruber created Markdown in 2004 as an easy-to-read markup language.\[9\] Markdown is widely used for blogging, [instant](https://en.wikipedia.org/wiki/Instant_messaging) messaging, and [large](https://en.wikipedia.org/wiki/Large_language_models) language models,\[10\] and also used elsewhere in online forums, collaborative software, documentation pages, and readme files.

### Markdown

`.md`, `.markdown`[^\[1\]\[2\]^](#page-5)

[**Filename**](https://en.wikipedia.org/wiki/Filename_extension) [**extensions**](https://en.wikipedia.org/wiki/Filename_extension)

```
text/markdown[2]
```

[**Internet**](https://en.wikipedia.org/wiki/Media_type) [**media type**](https://en.wikipedia.org/wiki/Media_type)

```
net.daringfireball.markdown
```

[**Uniform Type**](https://en.wikipedia.org/wiki/Uniform_Type_Identifier) [**Identifier (UTI)**](https://en.wikipedia.org/wiki/Uniform_Type_Identifier)

### The initial description of Markdown\[11\]

**UTI conformation** `public.plain-text` contained ambiguities and raised unanswered questions, causing implementations to both intentionally and accidentally diverge from the original version. This was addressed in 2014 when long-standing Markdown contributors released CommonMark, an unambiguous specification and test suite for Markdown.\[12\]

[**Magic number**](https://en.wikipedia.org/wiki/File_format#Magic_number) None

**Developed by** [John Gruber](https://en.wikipedia.org/wiki/John_Gruber)

**Initial release** March 9, 2004\[3\]\[4\]

[**Latest release**](https://en.wikipedia.org/wiki/Software_release_life_cycle) 1.0.1 December 17, 2004\[5\]

**Type of format** Open file format\[6\]

**Extended to** pandoc, MultiMarkdown, Markdown Extra, CommonMark,\[7\]

RMarkdown\[8\]

## History

**Website** [daringfireball.net/projects/markdown](https://daringfireball.net/projects/markdown/) [/ (https://daringfireball.net/projects/m](https://daringfireball.net/projects/markdown/) [arkdown/)](https://daringfireball.net/projects/markdown/)

Markdown was inspired by pre-existing conventions for marking up plain text in email and usenet posts,\[13\] such as the earlier markup languages setext (c. 1992), Textile (c. 2002), and reStructuredText (c. 2002).\[9\]

In 2002, Aaron Swartz created atx and referred to it as "the true structured text format". Gruber created the Markdown language in 2004 with Swartz as his "sounding board".\[14\] The goal of the language was to enable people "to write using an easy-to-read and easy-to-write plain text format, optionally convert it to structurally valid XHTML (or HTML)".\[5\]

Another key design goal was *readability*, that the language be readable as-is, without looking like it has been marked up with tags or formatting instructions,\[9\] unlike text formatted with "heavier" markup languages, such as Rich Text Format (RTF), HTML, or even wikitext, each of which have obvious in-line tags and formatting instructions which can make the text more difficult for humans to read.

Gruber wrote a Perl script, `Markdown.pl`, which converts marked-up text input to valid, well-formed XHTML or HTML, encoding angle brackets (`<`, `>`) and ampersands (`&`), which would be misinterpreted as special characters in those languages. It can take the role of a standalone script, a plugin for Blosxom or Movable Type, or of a text filter for BBEdit.\[5\]

## Rise and divergence

As Markdown's popularity grew rapidly, many Markdown implementations appeared, driven mostly by the need for additional features such as tables, footnotes, definition lists,\[note 1\] and Markdown inside HTML blocks.

The behavior of some of these diverged from the reference implementation, as Markdown was only characterised by an informal specification\[17\] and a Perl implementation for conversion to HTML.

At the same time, a number of ambiguities in the informal specification had attracted attention.\[18\] These issues spurred the creation of tools such as Babelmark\[19\]\[20\] to compare the output of various implementations,\[21\] and an effort by some developers of Markdown parsers for standardization. However, Gruber has argued that complete standardization would be a mistake: "Different sites (and people) have different needs. No one syntax would make all happy."\[22\]

Gruber avoided using curly braces in Markdown to unofficially reserve them for implementation-specific extensions.\[23\]

## CommonMark

### Standardization

### CommonMark

```
.md, .markdown[2]
```

[**Filename**](https://en.wikipedia.org/wiki/Filename_extension) [**extensions**](https://en.wikipedia.org/wiki/Filename_extension)

In 2012, a group of people, including Jeff Atwood and John MacFarlane, launched what Atwood characterised as a standardization effort.\[12\]

```
text/markdown;
variant=CommonMark[7]
```

[**Internet**](https://en.wikipedia.org/wiki/Media_type) [**media type**](https://en.wikipedia.org/wiki/Media_type)

*uncertain*[^\[24\]^](#page-7)

A community website now aims to "document various tools and resources available to document authors and developers, as well as implementors of the various Markdown implementations".\[26\]

[**Uniform Type**](https://en.wikipedia.org/wiki/Uniform_Type_Identifier) [**Identifier (UTI)**](https://en.wikipedia.org/wiki/Uniform_Type_Identifier)

**UTI conformation** public.plain-text

**Developed by** John MacFarlane, open source

### Name

**Initial release** October 25, 2014

[**Latest release**](https://en.wikipedia.org/wiki/Software_release_life_cycle) 0.31.2 January 28, 2024\[25\]

In September 2014, Gruber objected to the usage of "Markdown" in the name of this effort and it was rebranded as "CommonMark".\[13\]\[27\]\[28\]

**Type of format** [Open file format](https://en.wikipedia.org/wiki/Open_file_format)

**Extended from** Markdown

CommonMark.org published several versions of a specification, reference implementation, test suite, and " \[plans\] to announce a finalized 1.0 spec and test suite in 2019".\[29\] A finalized 1.0 spec has not been released, as major issues still remain unsolved.\[30\]

**Extended to** [GitHub Flavored](#page-3) [Markdown](#page-3)

**Website** [commonmark.org (https://](https://commonmark.org/) [commonmark.org/) spec](https://commonmark.org/) [.commonmark.org (http://s](http://spec.commonmark.org/) [pec.commonmark.org/)](http://spec.commonmark.org/)

### Adoption

Nonetheless, several websites and projects have adopted CommonMark, including Codeberg, Discourse, GitHub, GitLab, Reddit, Qt, Stack Exchange (Stack Overflow), and Swift.

In March 2016, two relevant informational Internet RFCs were published:

RFC 7763 (https://www.rfc-editor.org/rfc/rfc7763)  –  "The text/markdown Media Type,"\[2\]

*Informational.*

Introduces MIME type `text/markdown`. RFC 7764 (https://www.rfc-editor.org/rfc/rfc7764)  –  "Guidance on Markdown: Design Philosophies, Stability Strategies, and Select Registrations,"\[7\] *Informational.*

Discusses and registers the variants MultiMarkdown, GitHub Flavored Markdown (GFM), Pandoc, and Markdown Extra (among others).\[31\]

## Variants

Websites like Bitbucket, Diaspora, Discord,\[32\] GitHub,\[33\] OpenStreetMap, Reddit,\[34\] SourceForge\[35\]

and Stack Exchange\[36\] use variants of Markdown to make discussions between users easier.

### Depending on implementation, basic inline HTML tags may be supported.\[37\]

### Italic text may be implemented by `_underscores_` or `single-asterisks`.\[38\]

### GitHub Flavored Markdown

GitHub had been using its own variant of Markdown since as early as 2009,\[39\] which added support for additional formatting such as tables and nesting block content inside list elements, as well as GitHub- specific features such as auto-linking references to commits, issues, usernames, etc.

In 2017, GitHub released a formal specification of its GitHub Flavored Markdown (https://github.github.c om/gfm/) (GFM) that is based on CommonMark.\[33\] It is a strict superset of CommonMark, following its specification exactly except for tables, strikethrough, autolinks and task lists, which GFM adds as extensions.\[40\]

Accordingly, GitHub also changed the parser used on their sites, which required that some documents be changed. For instance, GFM now requires that the hash symbol that creates a heading be separated from the heading text by a space character.

### Markdown Extra

Markdown Extra is a lightweight markup language based on Markdown implemented in PHP (originally), Python and Ruby.\[41\] It adds the following features that are not available with regular Markdown:

Markdown markup inside HTML blocks Elements with id/class attribute "Fenced code blocks" that span multiple lines of code

Tables\[42\]

Definition lists Footnotes Abbreviations

Markdown Extra is supported in some content management systems such as Drupal,\[43\] Grav (CMS), Textpattern CMS\[44\] and TYPO3.\[45\]

## Examples

| Text using Markdown syntax | Corresponding HTML produced by a Markdown processor | Text viewed in a browser |
| --- | --- | --- |
| Heading ======= Sub-heading ----------- # Alternative heading ## Alternative sub- heading Paragraphs are separated by a blank line. Two spaces at the end of a line produce a line break. | <h1>Heading</h1> <h2>Sub-heading</h2> <h1>Alternative heading</h1> <h2>Alternative sub-heading</h2> <p>Paragraphs are separated by a blank line.</p> <p>Two spaces at the end of a line<br /> produce a line break.</p> | Heading Sub-heading Alternative heading Alternative sub-heading Paragraphs are separated by a blank line. Two spaces at the end of a line produce a line break. |
| Text attributes italic , **bold**, _ _ `monospace`. Horizontal rule: --- | <p>Text attributes <em>italic</em>, <strong>bold</strong>, <code>monospace</code>.</p> <p>Horizontal rule:</p> <hr /> | Text attributes italic, bold, monospace. Horizontal rule: |
| Bullet lists nested within numbered list: 1. fruits * apple * banana 2. vegetables - carrot - broccoli | <p>Bullet lists nested within numbered list:</p> <ol> <li>fruits <ul> <li>apple</li> <li>banana</li> </ul></li> <li>vegetables <ul> <li>carrot</li> <li>broccoli</li> </ul></li> </ol> | Bullet lists nested within numbered list: 1. fruits apple banana 2. vegetables carrot broccoli |
| A [link] (http://example.com). ![Image](Icon- pictures.png "icon") > Markdown uses email-style characters for | <p>A <a href="http://example.com">link</a>. </p> <p><img alt="Image" title="icon" src="Icon-pictures.png" /></p> <blockquote> <p>Markdown uses email-style | A link (http://example.com/). |

| blockquoting. > > Multiple paragraphs need to be prepended individually. Most inline <abbr title="Hypertext Markup Language">HTML</abbr> tags are supported. | characters for blockquoting.</p> <p>Multiple paragraphs need to be prepended individually.</p> </blockquote> <p>Most inline <abbr title="Hypertext Markup Language">HTML</abbr> tags are supported.</p> | Markdown uses email-style characters for blockquoting. Multiple paragraphs need to be prepended individually. Most inline HTML tags are supported. |
| --- | --- | --- |

## Implementations

Implementations of Markdown are available for over a dozen programming languages; in addition, many applications, platforms and frameworks support Markdown.\[46\] For example, Markdown plugins exist for every major blogging platform.\[13\]

While Markdown is a minimal markup language and is read and edited with a normal text editor, there are specially designed editors that preview the files with styles, which are available for all major platforms. Many general-purpose text and code editors have syntax highlighting plugins for Markdown built into them or available as optional download. Editors may feature a side-by-side preview window or render the code directly in a WYSIWYG fashion.

## See also

[Comparison of document markup languages](https://en.wikipedia.org/wiki/Comparison_of_document_markup_languages) [Comparison of documentation generators](https://en.wikipedia.org/wiki/Comparison_of_documentation_generators) [Comparison of wiki software](https://en.wikipedia.org/wiki/Comparison_of_wiki_software) [Lightweight markup language](https://en.wikipedia.org/wiki/Lightweight_markup_language) [List of markup languages](https://en.wikipedia.org/wiki/List_of_markup_languages) [List of text editors](https://en.wikipedia.org/wiki/List_of_text_editors) [Wiki markup](https://en.wikipedia.org/wiki/Wiki_markup)

## Explanatory notes

1. Technically HTML description lists

## References

1. Gruber, John (8 January 2014). "The Markdown File Extension" (https://daringfireball.net/link

    ed/2014/01/08/markdown-extension). The Daring Fireball Company, LLC. Archived (https://w [eb.archive.org/web/20200712120733/https://daringfireball.net/linked/2014/01/08/markdown-e](https://web.archive.org/web/20200712120733/https://daringfireball.net/linked/2014/01/08/markdown-extension) xtension) from the original on 12 July 2020. Retrieved 27 March 2022. "Too late now, I suppose, but the only file extension I would endorse is ".markdown", for the same reason

offered by Hilton Lipschitz: *We no longer live in a 8.3 world, so we should be using the most* *descriptive file extensions. It's sad that all our operating systems rely on this stupid* *convention instead of the better creator code or a metadata model, but great that they now* *support longer file extensions.*" 2. S. Leonard (March 2016). [*The text/markdown Media Type*](https://www.rfc-editor.org/rfc/rfc7763) [(https://www.rfc-editor.org/rfc/rfc77](https://www.rfc-editor.org/rfc/rfc7763)

63). Internet Engineering Task Force. doi:10.17487/RFC7763 (https://doi.org/10.17487%2FR FC7763). ISSN 2070-1721 (https://search.worldcat.org/issn/2070-1721). RFC 7763 (https://d atatracker.ietf.org/doc/html/rfc7763). *Informational.* 3. Swartz, Aaron (2004-03-19). "Markdown" (http://www.aaronsw.com/weblog/001189). *Aaron*

*Swartz: The Weblog*. Archived (https://web.archive.org/web/20171224200232/http://www.aar onsw.com/weblog/001189) from the original on 2017-12-24. Retrieved 2013-09-01. 4. Gruber, John. "Markdown" (https://web.archive.org/web/20040311230924/https://daringfirebal l.net/projects/markdown/index.text). [*Daring Fireball*](https://en.wikipedia.org/wiki/Daring_Fireball). Archived from the original (http://daringfir eball.net/projects/markdown/index.text) on 2004-03-11. Retrieved 2022-08-20. 5. Markdown 1.0.1 readme source code "Daring Fireball – Markdown" (https://web.archive.org/ web/20040402182332/http://daringfireball.net/projects/markdown/). 2004-12-17. Archived from the original (http://daringfireball.net/projects/markdown/) on 2004-04-02. 6. "Markdown: License" (http://daringfireball.net/projects/markdown/license). Daring Fireball.

[Archived (https://web.archive.org/web/20200218183533/https://daringfireball.net/projects/mar](https://web.archive.org/web/20200218183533/https://daringfireball.net/projects/markdown/license) kdown/license) from the original on 2020-02-18. Retrieved 2014-04-25. 7. S. Leonard (March 2016). [*Guidance on Markdown: Design Philosophies, Stability Strategies,*](https://www.rfc-editor.org/rfc/rfc7764)

[*and Select Registrations*](https://www.rfc-editor.org/rfc/rfc7764) (https://www.rfc-editor.org/rfc/rfc7764). Internet Engineering Task Force. doi:10.17487/RFC7764 (https://doi.org/10.17487%2FRFC7764). ISSN 2070-1721 (htt ps://search.worldcat.org/issn/2070-1721). RFC 7764 (https://datatracker.ietf.org/doc/html/rfc7 764). *Informational.* 8. "RMarkdown Reference site" (https://rmarkdown.rstudio.com/). Archived (https://web.archive.

org/web/20200303054734/https://rmarkdown.rstudio.com/) from the original on 2020-03-03. Retrieved 2019-11-21. 9. Markdown Syntax "Daring Fireball – Markdown – Syntax" (http://daringfireball.net/projects/ma rkdown/syntax#philosophy). 2013-06-13. "Readability, however, is emphasized above all else. A Markdown-formatted document should be publishable as-is, as plain text, without looking like it's been marked up with tags or formatting instructions. While Markdown's syntax has been influenced by several existing text-to-HTML filters — including Setext, atx, Textile, reStructuredText, Grutatext\[15\], and EtText\[16\] — the single biggest source of inspiration for Markdown's syntax is the format of plain text email." 10. Dillet, Romain (6 March 2025). "Mistral adds a new API that turns any PDF document into an

[AI-ready Markdown file" (https://techcrunch.com/2025/03/06/mistrals-new-ocr-api-turns-any-p](https://techcrunch.com/2025/03/06/mistrals-new-ocr-api-turns-any-pdf-document-into-an-ai-ready-markdown-file/) df-document-into-an-ai-ready-markdown-file/). *TechCrunch*. Retrieved 7 September 2025. 11. "Daring Fireball: Introducing Markdown" (https://daringfireball.net/2004/03/introducing\_markd own). *daringfireball.net*. Archived (https://web.archive.org/web/20200920182442/https://darin gfireball.net/2004/03/introducing\_markdown) from the original on 2020-09-20. Retrieved 2020-09-23. 12. Atwood, Jeff (2012-10-25). "The Future of Markdown" (https://web.archive.org/web/20140211

233513/http://www.codinghorror.com/blog/2012/10/the-future-of-markdown.html). CodingHorror.com. Archived from the original (http://www.codinghorror.com/blog/2012/10/the- future-of-markdown.html) on 2014-02-11. Retrieved 2014-04-25. 13. Gilbertson, Scott (October 5, 2014). "Markdown throwdown: What happens when FOSS

[software gets corporate backing?" (https://arstechnica.com/information-technology/2014/10/](https://arstechnica.com/information-technology/2014/10/markdown-throwdown-what-happens-when-foss-software-gets-corporate-backing/) markdown-throwdown-what-happens-when-foss-software-gets-corporate-backing/). [*Ars*](https://en.wikipedia.org/wiki/Ars_Technica) [*Technica*](https://en.wikipedia.org/wiki/Ars_Technica). Archived (https://web.archive.org/web/20201114231130/https://arstechnica.com/inf [ormation-technology/2014/10/markdown-throwdown-what-happens-when-foss-software-gets-](https://web.archive.org/web/20201114231130/https://arstechnica.com/information-technology/2014/10/markdown-throwdown-what-happens-when-foss-software-gets-corporate-backing/) corporate-backing/) from the original on November 14, 2020. Retrieved June 14, 2017. "CommonMark fork could end up better for users... but original creators seem to disagree."

14. @gruber (June 12, 2016). "I should write about it, but it's painful. More or less: Aaron was my

sounding board, my muse" (https://twitter.com/gruber/status/741989829173510145) (Tweet) – via Twitter. 15. "Un naufragio personal: The Grutatxt markup" (https://web.archive.org/web/2022063023054

6/https://triptico.com/docs/grutatxt\_markup.html). *triptico.com*. Archived from the original (http s://triptico.com/docs/grutatxt\_markup.html) on 2022-06-30. Retrieved 2022-06-30. 16. "EtText: Documentation: Using EtText" (http://ettext.taint.org/doc/ettext.html). *ettext.taint.org*.

Retrieved 2022-06-30. 17. "Markdown Syntax Documentation" (https://daringfireball.net/projects/markdown/syntax).

Daring Fireball. Archived (https://web.archive.org/web/20190909051956/https://daringfireball. net/projects/markdown/syntax) from the original on 2019-09-09. Retrieved 2018-03-09. 18. "GitHub Flavored Markdown Spec – Why is a spec needed?" (https://github.github.com/gfm/# why-is-a-spec-needed-). *github.github.com*. Archived (https://web.archive.org/web/20200203 204734/https://github.github.com/gfm/#why-is-a-spec-needed-) from the original on 2020-02- 03. Retrieved 2018-05-17. 19. "Babelmark 2 – Compare markdown implementations" (http://johnmacfarlane.net/babelmark

2/). Johnmacfarlane.net. Archived (https://web.archive.org/web/20170718113552/http://johnm acfarlane.net/babelmark2/) from the original on 2017-07-18. Retrieved 2014-04-25. 20. "Babelmark 3 – Compare Markdown Implementations" (https://babelmark.github.io/).

github.io. Archived (https://web.archive.org/web/20201112043521/https://babelmark.github.i o/) from the original on 2020-11-12. Retrieved 2017-12-10. 21. "Babelmark 2 – FAQ" (http://johnmacfarlane.net/babelmark2/faq.html). Johnmacfarlane.net.

[Archived (https://web.archive.org/web/20170728115918/http://johnmacfarlane.net/babelmark](https://web.archive.org/web/20170728115918/http://johnmacfarlane.net/babelmark2/faq.html) 2/faq.html) from the original on 2017-07-28. Retrieved 2014-04-25. 22. Gruber, John \[@gruber\] (4 September 2014). "@tobie @espadrine @comex @wycats

[Because different sites (and people) have different needs. No one syntax would make all](https://twitter.com/gruber/status/507670720886091776) happy" (https://twitter.com/gruber/status/507670720886091776) (Tweet) – via Twitter. 23. Gruber, John (19 May 2022). "Markdoc" (https://daringfireball.net/linked/2022/05/19/markdo c). *Daring Fireball*. Archived (https://web.archive.org/web/20220519202920/https://daringfireb all.net/linked/2022/05/19/markdoc) from the original on 19 May 2022. Retrieved May 19, 2022. "I love their syntax extensions — very true to the spirit of Markdown. They use curly braces for their extensions; I'm not sure I ever made this clear, publicly, but I avoided using curly braces in Markdown itself — even though they are very tempting characters — to unofficially reserve them for implementation-specific extensions. Markdoc's extensive use of curly braces for its syntax is exactly the sort of thing I was thinking about." 24. "UTI of a CommonMark document" (https://talk.commonmark.org/t/uti-of-a-commonmark-doc ument/2406). 12 April 2017. Archived (https://web.archive.org/web/20181122140119/https://t alk.commonmark.org/t/uti-of-a-commonmark-document/2406) from the original on 22 November 2018. Retrieved 29 September 2017. 25. "CommonMark specification" (http://spec.commonmark.org/). Archived (https://web.archive.or g/web/20170807052756/http://spec.commonmark.org/) from the original on 2017-08-07. Retrieved 2017-07-26. 26. "Markdown Community Page" (https://markdown.github.io/). GitHub. Archived (https://web.arc hive.org/web/20201026161924/http://markdown.github.io/) from the original on 2020-10-26. Retrieved 2014-04-25. 27. "Standard Markdown is now Common Markdown" (http://blog.codinghorror.com/standard-mar kdown-is-now-common-markdown/). Jeff Atwood. 4 September 2014. Archived (https://web.ar [chive.org/web/20141009181014/http://blog.codinghorror.com/standard-markdown-is-now-co](https://web.archive.org/web/20141009181014/http://blog.codinghorror.com/standard-markdown-is-now-common-markdown/) mmon-markdown/) from the original on 2014-10-09. Retrieved 2014-10-07. 28. "Standard Markdown Becomes Common Markdown then CommonMark" (http://www.infoq.co m/news/2014/09/markdown-commonmark). *InfoQ*. Archived (https://web.archive.org/web/202 00930150521/https://www.infoq.com/news/2014/09/markdown-commonmark/) from the original on 2020-09-30. Retrieved 2014-10-07.

29. "CommonMark" (http://commonmark.org/). Archived (https://web.archive.org/web/201604122

11434/http://commonmark.org/) from the original on 12 April 2016. Retrieved 20 Jun 2018. "The current version of the CommonMark spec is complete, and quite robust after a year of public feedback … but not quite final. With your help, we plan to announce a finalized 1.0 spec and test suite in 2019." 30. "Issues we MUST resolve before 1.0 release \[6 remaining\]" (https://talk.commonmark.org/t/is sues-we-must-resolve-before-1-0-release-6-remaining/1287). *CommonMark Discussion*. 2015-07-26. Archived (https://web.archive.org/web/20210414032229/https://talk.commonmar k.org/t/issues-we-must-resolve-before-1-0-release-6-remaining/1287) from the original on 2021-04-14. Retrieved 2020-10-02. 31. "Markdown Variants" (https://www.iana.org/assignments/markdown-variants/markdown-varia nts.xhtml). IANA. 2016-03-28. Archived (https://web.archive.org/web/20201027005128/http s://www.iana.org/assignments/markdown-variants/markdown-variants.xhtml) from the original on 2020-10-27. Retrieved 2016-07-06. 32. "Markdown Text 101 (Chat Formatting: Bold, Italic, Underline)" (https://support.discord.com/h c/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline). *Discord*. 2024-10-03. Retrieved 2025-02-07. 33. "GitHub Flavored Markdown Spec" (https://github.github.com/gfm/). GitHub. Archived (https:// web.archive.org/web/20200203204734/https://github.github.com/gfm/) from the original on 2020-02-03. Retrieved 2020-06-11. 34. "Reddit markdown primer. Or, how do you do all that fancy formatting in your comments, [anyway?" (https://www.reddit.com/r/reddit.com/comments/6ewgt/reddit\_markdown\_primer\_or](https://www.reddit.com/r/reddit.com/comments/6ewgt/reddit_markdown_primer_or_how_do_you_do_all_that/) \_how\_do\_you\_do\_all\_that/). Reddit. Archived (https://web.archive.org/web/20190611185827/ [https://www.reddit.com/r/reddit.com/comments/6ewgt/reddit\_markdown\_primer\_or\_how\_do\_](https://web.archive.org/web/20190611185827/https://www.reddit.com/r/reddit.com/comments/6ewgt/reddit_markdown_primer_or_how_do_you_do_all_that/) you\_do\_all\_that/) from the original on 2019-06-11. Retrieved 2013-03-29. 35. "SourceForge: Markdown Syntax Guide" (https://sourceforge.net/p/forge/documentation/mark down\_syntax/). SourceForge. Archived (https://web.archive.org/web/20190613130356/https:// sourceforge.net/p/forge/documentation/markdown\_syntax/) from the original on 2019-06-13. Retrieved 2013-05-10. 36. "Markdown Editing Help" (https://stackoverflow.com/editing-help). StackOverflow.com.

[Archived (https://web.archive.org/web/20140328061854/http://stackoverflow.com/editing-hel](https://web.archive.org/web/20140328061854/http://stackoverflow.com/editing-help) p) from the original on 2014-03-28. Retrieved 2014-04-11. 37. "Markdown Syntax Documentation" (https://daringfireball.net/projects/markdown/syntax#htm l). *daringfireball.net*. Archived (https://web.archive.org/web/20190909051956/https://daringfire ball.net/projects/markdown/syntax#html) from the original on 2019-09-09. Retrieved 2021-03-01. 38. "Basic Syntax: Italic" (https://www.markdownguide.org/basic-syntax/#italic). *The Markdown*

*Guide*. Matt Cone. Archived (https://web.archive.org/web/20220326234942/https://www.mark downguide.org/basic-syntax/#italic) from the original on 26 March 2022. Retrieved 27 March 2022. "To italicize text, add one asterisk or underscore before and after a word or phrase. To italicize the middle of a word for emphasis, add one asterisk without spaces around the letters." 39. Tom Preston-Werner. "GitHub Flavored Markdown Examples" (https://github.com/mojombo/gi thub-flavored-markdown/issues/1). *GitHub*. Archived (https://web.archive.org/web/202105131 54115/https://github.com/mojombo/github-flavored-markdown/issues/1) from the original on 2021-05-13. Retrieved 2021-04-02. 40. "A formal spec for GitHub Flavored Markdown" (https://githubengineering.com/a-formal-specfor-github-markdown/). *GitHub Engineering*. 14 March 2017. Archived (https://web.archive.or [g/web/20200203205138/https://githubengineering.com/a-formal-spec-for-github-markdown/)](https://web.archive.org/web/20200203205138/https://githubengineering.com/a-formal-spec-for-github-markdown/) from the original on 3 February 2020. Retrieved 16 Mar 2017.

41. Fortin, Michel (2018). "PHP Markdown Extra" (https://michelf.ca/projects/php-markdown/extr

a). *Michel Fortin website*. Archived (https://web.archive.org/web/20210117015819/https://mic helf.ca/projects/php-markdown/extra/) from the original on 2021-01-17. Retrieved 2018-12-26. 42. "PHP Markdown Extra" (https://michelf.ca/projects/php-markdown/extra). *Michel Fortin*.

[Archived (https://web.archive.org/web/20210117015819/https://michelf.ca/projects/php-mark](https://web.archive.org/web/20210117015819/https://michelf.ca/projects/php-markdown/extra/) down/extra/) from the original on 2021-01-17. Retrieved 2018-12-26. 43. "Markdown editor for BUEditor" (https://drupal.org/project/markdowneditor). 4 December

2008. Archived (https://web.archive.org/web/20200917172201/https://www.drupal.org/project/ markdowneditor) from the original on 17 September 2020. Retrieved 15 January 2017. 44. "Plugin: wet\_textfilter\_markdown" (https://plugins.textpattern.com/plugins/wet\_textfilter\_mark down). *Textpattern CMS plugins*. 2025-04-27. 45. "Markdown for TYPO3 (markdown\_content)" (https://extensions.typo3.org/extension/markdo wn\_content/). *extensions.typo3.org*. Archived (https://web.archive.org/web/20210201205749/ https://extensions.typo3.org/extension/markdown\_content/) from the original on 2021-02-01. Retrieved 2019-02-06. 46. "W3C Community Page of Markdown Implementations" (https://www.w3.org/community/mark down/wiki/MarkdownImplementations). *W3C Markdown Wiki*. Archived (https://web.archive.or [g/web/20200917231621/https://www.w3.org/community/markdown/wiki/MarkdownImplement](https://web.archive.org/web/20200917231621/https://www.w3.org/community/markdown/wiki/MarkdownImplementations) ations) from the original on 17 September 2020. Retrieved 24 March 2016.

## External links

Official website (https://daringfireball.net/projects/markdown/) for original John Gruber markup

Retrieved from "https://en.wikipedia.org/w/index.php?title=Markdown&oldid=1353541055"