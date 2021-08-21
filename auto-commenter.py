#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Split out the preamble code before the first /^def / function definition.
Split the code into chunks beginning with each /^def / function definition line.
For each non-preamble chunk, construct a Codex prompt consisting of the contents of fewshot-example.txt followed by the code chunk and the line "# With verbose inline comments".

 - Use Temperature 0, with a Stop sequence of "# Original", to make Codex stop after it finishes generating the commented code.

 - Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "# Original"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    ```

    The response is json, and the output we want is in ['choices'][0]['text'].

 - Replace the original code chunk with the commented one, move on to the next chunk, and repeat the same process.
 
 - If the script was called with a filename, output the commented code to a .new file. Otherwise output it to stdout.
"""

import json
import os
import re
import requests
import sys

GPT_API_KEY = os.environ['GPT_API_KEY']

"""
The algorithm above should be divided into modular functions. The top-level functions are:

- read_code
- split_into_chunks
- comment_chunk
- comment_code
- comment_code_from_file
- comment_code_from_stdin
"""

def read_code(filename):
    """
    Read code from a file or stdin and return it as a string
    """
    if filename:
        with open(filename, 'r') as f:
            code = f.read()
    else:
        code = sys.stdin.read()
    return code

def split_into_chunks(code):
    """
    Split code into chunks, each chunk being a function definition
    """
    chunks = []
    chunk = ''
    for line in code.splitlines():
        if re.match(r'^def ', line):
            chunks.append(chunk)
            chunk = ''
        chunk += line + '\n'
    chunks.append(chunk)
    return chunks

def comment_chunk(chunk):
    """
    Comment a single chunk of code
    """
    prompt = open('fewshot-example.txt', 'r').read()
    prompt += '\n' + chunk + '\n# With verbose inline comments\n'
    print(prompt)
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "# Original"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    print(response.json()['choices'][0]['text'])
    return response.json()['choices'][0]['text']

def comment_code(code):
    """
    Comment code, given as a string.
    """
    chunks = split_into_chunks(code)
    commented_chunks = [comment_chunk(chunk) for chunk in chunks]
    return '\n'.join(commented_chunks)

def comment_code_from_file(filename):
    """
    Comment code from a file, outputting to a .new file.
    """
    code = read_code(filename)
    commented_code = comment_code(code)
    with open(filename + '.new', 'w') as f:
        f.write(commented_code)

def comment_code_from_stdin():
    """
    Comment code from stdin
    """
    code = read_code(None)
    commented_code = comment_code(code)
    print(commented_code)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        comment_code_from_stdin()
    else:
        comment_code_from_file(sys.argv[1])
