---
title: "Markdown - Wikipedia"
date: "2026-06-02"
source: "wikipedia-markdown-ja.pdf"
pages: 7
---

# Markdown

### 出典: フリー百科事典『ウィキペディア（Wikipedia）』

**Markdown**（マークダウン）とは、プレーンテキ スト形式で書式付きテキストを記述する軽量マー クアップ言語である。

### Markdown

テキストエディタで手軽に書いた文書からHTML を生成するために開発されたが、PowerPoint形式 やLaTeX形式のファイルへ変換するソフトウェア （コンバータ）も開発されている。各コンバータ の開発者によって拡張が施された各種の方言が存 在する。

MIMEタイプ text/markdown\[1\]

開発者 [ジョン・グルーバー](https://ja.wikipedia.org/wiki/%E3%82%B8%E3%83%A7%E3%83%B3%E3%83%BB%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%90%E3%83%BC)

初版 2004年3月19日\[2\]

最新版 1.0.1 (2004年12月17日\[3\])

種別 軽量マークアップ言語

拡張 [MultiMarkdown](https://ja.wikipedia.org/wiki/MultiMarkdown?action=edit&redlink=1) [Markdown Extra](https://ja.wikipedia.org/wiki/Markdown_Extra?action=edit&redlink=1) [CommonMark](https://ja.wikipedia.org/wiki/CommonMark?action=edit&redlink=1)

## オリジナルのMarkdown

ウェブサイト daringfireball.net/projects /markdown/ (https://daringfir [eball.net/projects/markdow](https://daringfireball.net/projects/markdown/) [n/)](https://daringfireball.net/projects/markdown/)

「書きやすくて読みやすいプレーンテキストとし て記述した文書を、妥当なXHTML（もしくは HTML）文書へと変換できるフォーマット」とし て、ジョン・グルーバーにより作成された。アー ロン・スワーツも大きな貢献をしている\[4\]。 Markdownの記法の多くは、電子メールにおいてプレーンテキストを装飾する際の慣習から着想 を得ている。

Markdownはグルーバーによって書かれたMarkdown.plというPerlプログラムを指すこともある。 このスクリプトは、Markdownの形式でマークアップされたテキストをXHTML文書もしくは HTML文書に変換するものである。Markdown.plはスクリプト単体として利用することができる と同時に、BlosxomやMovable Typeのプラグインなどからも利用できる\[4\]。

Markdown.plは、その後第三者によってCPANのPerlモジュール (Text::Markdown) として再実装 され、さらにPython等の他のプログラミング言語でも実装された。MarkdownはBSDライセンス の下で配布され、いくつかのコンテンツ管理システム (CMS) でもプラグインとして利用でき る\[5\]\[6\]。

## 利用例と方言

有名なMarkdown方言としてCommonMark (https://commonmark.org/)、Markdown Extra (https://mic helf.ca/projects/php-markdown/extra/)やGitHub Flavored Markdown (https://github.github.com/gfm/)、 Marukuなどがある。その他のサービス・コンバータにおいても表やソースコードの記法などで 独自の拡張が加えられていることが多い。以下にMarkdownの利用例を挙げる。

Stack Overflowや他のStack Exchange Networkサイトは、Markdownを改変した方言をデフ ォルトのフォーマットシステムとして利用している\[7\]\[8\]。

### PosterousはMarkdownをマークアップの選択肢として提供している\[9\]。

### RedditはMarkdownを利用している\[10\]。

GitHubはMarkdownの方言をコメント・メッセージ・その他のフォーマットに利用してい る\[11\]\[12\]。John Gruber has described this dialect as a "superior variant" for "situations like user-submitted comments".\[13\]。のちに、CommonMarkベースの仕様に更新している\[14\]。

### Bitbucketは、README記述用のマークアップ言語の選択肢としてMarkdownを提供してい る\[15\]。

### InstikiはMarkdown拡張を使ってウィキ構文を提供している。この拡張構文はMarukuと呼ば れる\[16\]。

### Squarespaceはブログエントリ記述用のマークアップの選択肢としてMarkdownを提供して いる\[17\]。

### TumblrはMarkdownでポストを編集できる\[18\]。

Discordは独自のMarkdown方言でテキストを装飾できる。これはほとんどMarkdownと同 じ記法だが、H4~H6が存在しない。(-# を先頭につけることでプレーンテキストより小さく する記法が代わりに存在する)\[19\]\[20\]

[MultiMarkdown](https://ja.wikipedia.org/wiki/MultiMarkdown?action=edit&redlink=1)

[CommonMark](https://ja.wikipedia.org/wiki/CommonMark?action=edit&redlink=1)

StackEdit (https://stackedit.io/)はオンラインMarkdownエディタの一つ。GitHub Flavored Markdownに、数式記述（MathJaxによる）とUMLシーケンス図、フローチャー トを記述できる拡張が加えられている。

## 記法の例

以下の例はMarkdownの記法の包括的なリストではないし、ひとつの効果を実現するために複数 の記法が利用できる場合も多い。詳細はfull Markdown syntax (https://daringfireball.net/projects/ma rkdown/syntax)に記載されている。

### 段落

### 段落は1つ以上の連続したテキストであり、空行によって分けられる。通常の段落をスペースや タブでインデントしてはならない。

これは段落です。2つの文があります。

これは別の段落です。ここにも2つの文があります。

### 改行

テキストに挿入された改行は取り除かれる。これは、画面の大きさに応じて改行を行う処理は Webブラウザが担当すべきであるという設計思想による。強制的に改行したい場合は、2つ以上 のスペースを行末に残した上で改行すると <br> になる。

### 見出し

### テキストの前にいくつかの'#'を置くことで見出しを作ることができる。'#'の数が見出しのレベ ルに対応する。HTMLは見出しのレベルを6まで提供している。

\# レベル1の見出し

\## レベル2の見出し

\### レベル3の見出し

\#### レベル4の見出し

\##### レベル5の見出し

\###### レベル6の見出し

### 最初の2つのレベルには代替の記法が存在する。

レベル1の見出し ===============

レベル2の見出し ---------------

### 引用

\> "このテキストは、HTMLのblockquote要素に囲まれます。 blockquote要素はreflowableです。テキストを好きなように 改行することができます。改行したとしても、変換後はひとつの blockquote要素として扱われます。"

### 上記は次のようなHTMLに変換される。

<blockquote> <p>このテキストは、HTMLのblockquote要素に囲まれます。 blockquote要素はreflowableです。テキストを好きなように 改行することができます。改行したとしても、変換後はひとつの blockquote要素として扱われます。</p> </blockquote>

### リスト

\* 順序無しリストのアイテム \* サブアイテムはタブもしくは4つのスペースでインデントする \* 順序無しリストの別のアイテム

\+ 順序無しリストのアイテム + サブアイテムはタブもしくは4つのスペースでインデントする

\+ 順序無しリストの別のアイテム

\- 順序無しリストのアイテム - サブアイテムはタブもしくは4つのスペースでインデントする - 順序無しリストの別のアイテム

  1. 順序付きリストのアイテム 1. サブアイテムはタブもしくは4つのスペースでインデントする 2. 順序付きリストの別のアイテム

### コード

### コード（等幅フォントで整形される）を含める場合、インラインコードは「\`some code\`」のよ うにバッククオート (U+0060) で囲むことになる。

これは段落です。文中に\`コードテキスト\`を含みます。

複数行にまたがるコードは、タブもしくは4つ以上のスペースを行頭に書くか、3つずつのバッ ククオートでコード全体をくくる。 開始を表すバッククオートの3つ目に続けて、任意で言語名を明記することができる。

1行目 2行目 3行目

\`\`\`javascript (() => { 'use strict';

console.log('Hello world'); })(); \`\`\`

Markdownは通常、改行や連続したスペースを削除するため、インデントやコードのレイアウト を壊す可能性があるが、この場合 Markdownは空白をすべて保持する。

### 水平線

1行の中に、3つ以上のハイフンやアスタリスク・アンダースコアだけを並べると水平線が作ら れる。ハイフンやアスタリスクのあいだには空白を入れてもよい。以下の行はすべて水平線を 生成する。

\* \* \*

\*\*\*

\*\*\*\*\*

\- - -

---------------------------------------

### リンク

### リンクは次のように記述できる。

\[リンクのテキスト\](リンクのアドレス "リンクのタイトル")

### 参照目的のリンクとして、脚注として段落外に含めることもできる。

\[リンクのテキスト\]\[linkref\]

### 段落外もしくは文書の最後に次のような記述があれば、それは参照リンクとして機能する。

\[linkref\]: リンクのアドレス "リンクのタイトル"

### 強調

\*強調\* もしくは \_強調\_（斜体として表現されることが多い）

\*\*強い強調\*\* もしくは \_\_強い強調\_\_（太字として表現されることが多い）

### 画像

### 画像は以下のように埋め込める。リンクの冒頭に ! が付いている形式である。

!\[Altのテキスト\](/path/to/img.jpg) !\[Altのテキスト\](/path/to/img.png "タイトル")

### バックスラッシュによるエスケープ

Markdownが書式化コマンドとして解釈する文字は、バックスラッシュ（U+005C, 日本語環境で は円記号として表示される場合もある）を加えることによって、その文字そのものとして解釈 させることができる。例えば \\\* は、テキスト強調の開始ではなくアスタリスクとして出力され る。バックスラッシュ自身を出力したい場合は、\\\\とする。

なお、Microsoft Windowsのファイルシステムではパスの区切り文字にバックスラッシュ\\が使わ れ、ネットワークリソースには2つのバックスラッシュ\\\\で始まるUNC (Universal Naming Convention) パスが使われる\[21\]が、Markdownの文書内にそのようなパス文字列を含める場合は 配慮が必要である。

### インラインHTML

生のHTMLのブロックレベル要素の中にあるテキストに対してMarkdownはいかなる変換も行わ ないので、HTMLのブロックレベル要素のタグでテキストを囲むことによって、Markdownのソ ース文章の中にHTMLのセクションを加えることもできる。

<font color="red">赤</font>

## 脚注

1. “RFC 7763 (https://www.rfc-editor.org/info/rfc7763)”. IETF. 2018年12月12日閲覧。
1. Aaron Swartz (2004年3月19日). “Markdown (http://www.aaronsw.com/weblog/00118

    9)”. 2018年12月12日閲覧。

1. John Gruber (2004年12月17日). “Markdown 1.0.1 (https://daringfireball.net/2004/12/ma

    rkdown\_101)”. 2018年12月12日閲覧。

1. Markdown 1.0.1 readme source code“Daring Fireball - Markdown (https://daringfireball.ne

    t/projects/markdown/)” (2004年12月17日). 2011年11月13日閲覧。

1. “MarsEdit 2.3 ties the knot with Tumblr support - Ars Technica (https://arstechnica.com/ga

    dgets/2009/03/marsedit-23-ties-the-knot-with-tumblr-support/)”. 2009年8月11日閲覧。

1. “Review: Practical Django Projects - Ars Technica (https://arstechnica.com/information-te

    chnology/2008/07/review-practical-django-projects/)”. 2009年8月11日閲覧。

1. “Markdown Editing Help - Stack Overflow (https://stackoverflow.com/editing-help)”. 2010

    年4月29日閲覧。

1. “Three Markdown Gotchas - Blog – Stack Overflow (https://stackoverflow.blog/2008/06/2

    5/three-markdown-gotcha/)”. 2010年4月29日閲覧。

1. “Markdown - Posterous Help (https://web.archive.org/web/20110217153554/http://poste

    rous.com/help/markdown)”. 2011年2月17日時点のオリジナル (http://posterous.com/hel p/markdown)よりアーカイブ。2010年6月26日閲覧。

1. “Reddit's help document on Markdown (https://www.reddit.com/wiki/commenting/)”.

    2010年7月20日閲覧。

1. “Making GitHub More Open: Git-backed Wikis - GitHub (https://github.blog/2010-08-12-m

    aking-github-more-open-git-backed-wikis/)”. 2010年9月1日閲覧。

1. “GitHub Flavored Markdown - Introduction (https://github.com/github-flavored-markdow

    n/)”. 2011年1月3日閲覧。

1. “Daring Fireball Linked List: GitHub Flavored Markdown (https://daringfireball.net/linked/

    2009/10/23/github-flavored-markdown)”. 2011年1月3日閲覧。

1. “A formal spec for GitHub Flavored Markdown (https://github.blog/2017-03-14-a-formal-

    spec-for-github-markdown/)”. The GitHub Blog (2017年3月14日). 2019年3月16日閲覧。

1. “README content (https://support.atlassian.com/bitbucket-cloud/docs/readme-conten

    t/)”. 2023年3月28日閲覧。

1. “Markup Choices in Instiki (https://golem.ph.utexas.edu/wiki/instiki/show/Markup+Choic

    es)”. 2010年8月24日閲覧。

1. “Markdown Syntax Reference (https://five.squarespace.com/display/ShowHelp?section=

    Markdown)”. 2023年3月28日閲覧。

1. “Tumblr Preferences (https://www.tumblr.com/preferences)”. 2011年1月3日閲覧。

19. “Markdown Text 101 (Chat Formatting: Bold, Italic, Underline) (https://support.discord.c

    [om/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Unde](https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline) rline)” (英語). Discord (2025年4月23日). 2026年5月6日閲覧。

1. “How to Make Your Discord Messages Bold, Italic, Underlined & Tons More (https://discor

    d.com/blog/make-your-discord-messages-bold-italic-underlined-and-more)”. discord.com. 2026年5月6日閲覧。

1. File path formats on Windows systems - .NET | Microsoft Learn (https://learn.microsoft.c

    om/en-us/dotnet/standard/io/file-path-formats#unc-paths)

## 関連項目

### コンピュータ言語

### データ記述言語

### マークアップ言語

### 軽量マークアップ言語

## 外部リンク

公式ウェブサイト (https://daringfireball.net/projects/markdown/)（英語）

CommonMark (https://commonmark.org/)（英語）

MarkdownSharp (https://code.google.com/archive/p/markdownsharp/)（英語）

PHP Markdown (https://michelf.ca/projects/php-markdown/)（英語）

「https://ja.wikipedia.org/w/index.php?title=Markdown&oldid=109410601」から取得