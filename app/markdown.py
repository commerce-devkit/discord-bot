import re
from typing import NamedTuple

FENCED_CODEBLOCK_PATTERN = re.compile(r"```(?P<lang>[^\n`]*)\n(?P<body>[\s\S]*?)```")
CODEBLOCK_PATTERN = re.compile(r"```[\s\S]*?```|`[^`\n]+`")


class CodeBlock(NamedTuple):
    lang: str
    body: str


def extract_fenced_codeblocks(content: str) -> list[CodeBlock]:
    return [
        CodeBlock(match["lang"].strip(), match["body"].rstrip("\n"))
        for match in FENCED_CODEBLOCK_PATTERN.finditer(content)
    ]


def strip_codeblocks(content: str) -> str:
    return CODEBLOCK_PATTERN.sub("", content)
