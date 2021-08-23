#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Split out the preamble code before the first function definition, such as /^def / for python or /^\s*(public|private) / for java.
Split the code into chunks beginning with each function definition line.
For each non-preamble chunk, construct a Codex prompt consisting of the contents of autocomment-example.txt followed by the code chunk and the line "Same function with verbose inline comments:".

 - Use Temperature 0, with a Stop sequence of "Original code:", to make Codex stop after it finishes generating the commented code.

 - Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "Original code:"
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
    # If filename is not None, open it for reading
    if filename:
        with open(filename, 'r') as f:
            # Read the code from the file
            code = f.read()
    # Otherwise read the code from stdin
    else:
        code = sys.stdin.read()
    # Return the code
    return code

def split_into_chunks(code):
    """
    Split code into chunks, each chunk being a function definition
    """
    # Create an empty list to store chunks
    chunks = []
    # Create a string to store the current chunk
    chunk = ''
    # For each line in the code
    for line in code.splitlines():
        # If the line is a python or java function definition
        if re.match(r'^\s*(def|public|private)\s', line):
            # Add the current chunk to the list of chunks
            chunks.append(chunk)
            # And reset the current chunk
            chunk = ''
        # Add the line to the current chunk
        chunk += line + '\n'
    # Add the last chunk to the list of chunks
    chunks.append(chunk)
    # Return the list of chunks
    return chunks

def comment_chunk(chunk):
    """
    Comment a single chunk of code
    """
    prompt = open('autocomment-example.txt', 'r').read()
    prompt += '\n' + chunk + '\nSame function with verbose inline comments:\n'
    #print(prompt)
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "Original code:"
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
    # Split code into chunks
    chunks = split_into_chunks(code)
    # Comment each chunk
    commented_chunks = [comment_chunk(chunk) for chunk in chunks]
    # Return the joined chunks
    return '\n'.join(commented_chunks)

def comment_code_from_file(filename):
    """
    Comment code from a file, outputting to a .new file.
    """
    # Read the code from the file
    code = read_code(filename)
    # Comment the code
    commented_code = comment_code(code)
    # Open the new file
    with open(filename + '.new', 'w') as f:
        # Write the commented code to the file
        f.write(commented_code)

def comment_code_from_stdin():
    """
    Comment code from stdin
    """
    # Read code from stdin
    code = read_code(None)
    # Comment code
    commented_code = comment_code(code)
    # Print commented code
    print(commented_code)

if __name__ == '__main__':
    # If there is only one argument
    if len(sys.argv) == 1:
        # Call the function to comment code from stdin
        comment_code_from_stdin()
    # If there is more than one argument
    else:
        # Call the function to comment code from file
        comment_code_from_file(sys.argv[1])
