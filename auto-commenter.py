#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Find all defined functions.
Split the code as follows:
 - code prior to the first function (top code)
 - each function's definition line 
 - each function's code
 - code after the end of the last function (bottom code)
For each function, construct a Codex prompt consisting of:
 - the function's definition line
 - the function's code
 - the comment '\n# With verbose inline comments\n'
 - a repeat of the function definition line, and
 - an indented comment line without a trailing newline ('    #'):

 - Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function.

 - Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "def "
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
    ```

    The response is json that looks like:
    ```
    {"id": "cmpl-3XmVTLK9jvbny8CNcUmSqT8BNc6MC", "object": "text_completion", "created": 1629180295, "model": "davinci:2020-05-03", "choices": [{"text": " It is because of the scattering of the molecules in the air that make up the atmosphere. They scatter blue light more than any other color, making the sky appear blue.\n", "index": 0, "logprobs": null, "finish_reason": "stop"}]}
    ```
    
 - Replace the original function with the commented one, move on to the next function, and repeat the same process.
"""

import json
import os
import re
import requests
import sys

GPT_API_KEY = os.environ['GPT_API_KEY']

"""
List of all the functions called by main():

def get_code(filename):
    Read in the code to be processed from a provided filename or from stdin.

def get_functions(code):
    Find all defined functions.

def split_code(code):
    Split the code as follows:
        - code prior to the first function (top code)
        - each function's definition line 
        - each function's code
        - code after the end of the last function (bottom code)
"""


def get_code(filename):
    """Read in the code to be processed from a provided filename or from stdin."""

    if filename:
        with open(filename, 'r') as f:
            code = f.read()

    else:
        print('Reading from stdin...')

        # read in all lines from stdin, then join them into one string. This is done because sys.stdin.read() returns a list of lines.
        code = ''.join(sys.stdin.readlines())

    return code


def get_functions(code):
    """Find all defined functions."""

    # find all function definitions, which look like: 'def <function name>():' and return a list of them.
    functions = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(\s*\)\s*:', code)

    return functions


def split_code(code):
    """Split the code as follows:

        - code prior to the first function (top code)
        - each function's definition line 
        - each function's code
        - code after the end of the last function (bottom code)"""

    # find all function definitions, which look like: 'def <function name>():' and return a list of them. This is used to find the start and end of each function's code block.
    functions = get_functions(code)

    # find the index of the first function in the code.
    start_index = code.find('def ' + functions[0] + '():')

    # find the index of the last function in the code.
    end_index = code.rfind('def ' + functions[-1] + '():')

    # split the code into top, functions, and bottom.
    top = code[:start_index]
    bottom = code[end_index:]

    # split each function into definition and code.
    functions = [f.split('\n') for f in functions]

    # split each function's definition line from its code.
    for i, f in enumerate(functions):
        f[0] = f[0].replace('def ', '').replace(':', '')
        f[1:] = '\n'.join(f[1:]).split('\n')

    # split each function's code from the next function's definition line.
    for i, f in enumerate(functions):
        if i < len(functions) - 1:
            f[1:] = '\n'.join(f[1:]).split('\n' + functions[i + 1][0])

        else:
            f[1:] = '\n'.join(f[1:]).split('\n' + bottom)

        """
        # remove any empty lines at the end of each function's code block.
        while not f[-1]:
            del f[-1]

        # remove any empty lines at the start of each function's code block.
        while not f[1]:
            del f[1]

        # remove any empty lines between each function's definition line and its code block.
        while not f[2]:
            del f[2]
        """

    return top, functions, bottom


def construct_prompt(function):
    """Construct a Codex prompt consisting of:

        - the function's definition line
        - the function's code
        - the comment '\n# With verbose inline comments\n'
        - a repeat of the function definition line, and
        - an indented comment line without a trailing newline ('    #'):

        Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function."""

    # construct the prompt by joining together all the parts.
    prompt = '\n'.join(function) + '\n# With verbose inline comments\n' + function[0] + '\n    #'

    return prompt


def call_codex(prompt):
    """Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

        ```
        data = json.dumps({
            "prompt": prompt,
            "max_tokens": 1500,
            "temperature": 0,
            "stop": "def "
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(GPT_API_KEY)
        }
        response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)
        ```
     """

    # construct the data to be sent to the API.
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0,
        "stop": "def "
    })

    # construct the headers to be sent to the API.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(GPT_API_KEY)
    }

    # send the request to the API.
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)

    # return the response from the API.
    return response


def process_code(code):
    """Process the code by:

        - splitting it into top, functions, and bottom;
        - constructing a Codex prompt for each function; and
        - calling the Codex API with each prompt."""

    # split the code into top, functions, and bottom.
    top, functions, bottom = split_code(code)

    # construct a Codex prompt for each function.
    prompts = [construct_prompt(f) for f in functions]

    # call the Codex API with each prompt.
    responses = [call_codex(p) for p in prompts]

    # return all of the responses from the API calls.
    return responses


def main():
    """Read in the code to be processed from a provided filename or from stdin."""

    # read in the code to be processed from a provided filename or from stdin.
    code = get_code(sys.argv[1] if len(sys.argv) > 1 else None)

    # process the code by: splitting it into top, functions, and bottom; constructing a Codex prompt for each function; and calling the Codex API with each prompt.
    responses = process_code(code)

    # print out all of the responses from the API calls. This is just for debugging purposes and can be removed later.
    print('\n'.join([r.text for r in responses]))


if __name__ == '__main__':
    main()
