#!/usr/bin/env python
"""
Script to automatically add PEP 257 Google style doctrings to Python code

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Split out the preamble code before the first function definition.
Split the code into chunks beginning with each function definition line.
For each non-preamble chunk:
 - Construct a Codex prompt consisting of:
  - the contents of autodocstring-example.txt
  - the code chunk
  - the line '#autodoc: A comprehensive PEP 257 Google style doctring, including a brief one-line summary of the function.'.
  
 - Use Temperature 0, with a Stop sequence of "#autodoc", to make Codex stop after it finishes generating the docstring.

 - Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "#autodoc"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    ```

    The response is json, and the output we want is in ['choices'][0]['text'].

 - Format the response text as a docstring by:
  - adding triple " quotes immediately before it without a trailing newline
  - adding triple " quotes on a new line after it.
 - Remove any existing docstring in the original function code.
 - Replace the original function definition with the function definition line, the docstring, and the original function code.

If the script was called with a filename, output the commented code to a .new file. Otherwise output it to stdout.

Functions called by main:

- get_api_key
    Get the user’s GTP_API_KEY from the environment.

- get_code
    Read in the code to be processed from a provided filename or from stdin.

- get_code_chunks
    Split the code into chunks beginning with each function definition line.

- get_prompt
    Construct a Codex prompt consisting of:
    - the contents of autodocstring-example.txt
    - the code chunk
    - the line '#autodoc: A comprehensive PEP 257 Google style doctring, including a brief one-line summary of the function.'.

- get_response
    Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "#autodoc"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    ```

    The response is json, and the output we want is in ['choices'][0]['text'].

- extract_function_code
    Returns only the code of the function, without the funciton definition line or the docstring

- replace_function_definition
    Replace the original function definition with the response and the original function code.

- output_code
    If the script was called with a filename, output the commented code to a .new file. Otherwise output it to stdout.

- main
    Call output_code with the processed code.

"""

import json
import os
import re
import requests
import sys

GPT_API_KEY = os.environ['GPT_API_KEY']

def get_api_key():
    """
    Get the user’s GTP_API_KEY from the environment.

    Parameters:
        None

    Returns:
        GPT_API_KEY (str): The user’s GPT_API_KEY.

    """
    return GPT_API_KEY

def get_code():
    """
    Read in the code to be processed from a provided filename or from stdin.

    Parameters:
        None

    Returns:
        code (str): The code to be processed.

    """
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            code = f.read()
    else:
        code = sys.stdin.read()
    return code

def get_code_chunks(code):
    """
    Split the code into chunks beginning with each function definition line.

    Parameters:
        code (str): The code to be processed.

    Returns:
        chunks (list): The code split into chunks beginning with each function definition line.

    """
    chunks = []
    for chunk in code.split('\n\n'):
        #print("Chunk:\n",chunk)
        if re.match(r'\s*\n*def ', chunk):
        # If the function definition line is indented (starts with whitespace), skip it.
            if re.match(r'\s+def ', chunk):
                pass
            else:
                chunks.append(chunk)

    return chunks

def get_prompt(code_chunk):
    """
    Construct a Codex prompt consisting of:
    - the contents of autodocstring-example.txt
    - the code chunk
    - the line '#autodoc: A comprehensive PEP 257 Google style doctring, including a brief one-line summary of the function.'.

    Parameters:
        code_chunk (str): A chunk of code.

    Returns:
        prompt (str): A prompt for the user.

    """
    #print(code_chunk.split('\n')[0])
    prompt = '\n\n'.join([
        open('autodocstring-example.txt').read(),
        code_chunk,
        '#autodoc: A comprehensive PEP 257 Google style doctring, including a brief one-line summary of the function.',
    ])
    return prompt

def get_response(prompt):
    """
    Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "#autodoc"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    ```

    The response is json, and the output we want is in ['choices'][0]['text'].

    Parameters:
        prompt (str): A prompt for the user.

    Returns:
        response (str): The response from the API.

    """
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "#autodoc"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    try:
        response = response.json()['choices'][0]['text']
    except KeyError:
        print(response.json(), file=sys.stderr)
        #sys.exit(1)
    return response


def extract_function_code(code_chunk):
    """
    Returns only the code of the function, without the funciton definition line or the docstring

    Parameters:
        code_chunk (str): A chunk of code.

    Returns:
        function_code (str): The code of the function.

    """
    # Remove the function definition line
    #print(code_chunk)
    function_code = re.sub(r'^\s*def .+\n', '', code_chunk)
    # Split the function code by triple "s into a function chunks variable
    function_chunks = re.split(r'\"\"\"', function_code)
    # If the first chunk contains anything besides newlines and whitespace, return the function_code unchanged
    if not re.match(r'^\s*$', function_chunks[0]):
        print(function_chunks[0])
        return function_code
    #print(function_code)
    # Remove the first docstring
    function_code = re.sub(r'""".*?"""', '', function_code, 1, flags=re.DOTALL)
    #function_code = re.sub(r'\):\n*\s*""".*?"""', '\):\n', function_code, flags=re.DOTALL)

    #print(function_code)
    return function_code


def output_code(code):
    """
    If the script was called with a filename, output the commented code to a .new file. Otherwise output it to stdout.

    Parameters:
        code (str): The code to be processed.

    Returns:
        None

    """
    if len(sys.argv) > 1:
        with open(sys.argv[1] + '.new', 'w') as f:
            f.write(code)
    else:
        print(code)

def main():
    """
    Call output_code with the processed code.

    Parameters:
        None

    Returns:
        None

    """
    code = get_code()
    chunks = get_code_chunks(code)
    for chunk in chunks:
        prompt = get_prompt(chunk)
        #print(prompt)
        try:
            response = get_response(prompt)
        except json.decoder.JSONDecodeError:
            continue
        # If the response is empty, continue to the next chunk
        if not response:
            continue
        #print("response:",response)
        function_code = extract_function_code(chunk)
        #print("function_code:",function_code)
        new_chunk = '\n'.join([
            response,
            function_code
        ])
        # Remove any repeated blank lines
        new_chunk = re.sub(r'\n+\s*\n+\s*\n+', '\n\n', new_chunk)

        #print("new_chunk:",new_chunk)
        print(new_chunk)
        #sys.exit()
        code = code.replace(chunk, new_chunk)
    output_code(code)

if __name__ == '__main__':
    main()
