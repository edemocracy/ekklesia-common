from markdown import Markdown
from mdx_gfm import GithubFlavoredMarkdownExtension


MARKDOWN_EXTENSIONS = [GithubFlavoredMarkdownExtension()]


def markdown():
    return Markdown(extensions=MARKDOWN_EXTENSIONS)


def convert(text):
    md = markdown()
    return md.convert(text)
