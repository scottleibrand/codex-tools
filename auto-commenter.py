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
The algorithm above should be divided into modular functions. The top-level functions are:

- read_code_from_file
- get_functions
- get_function_code
- get_function_definition
- construct_prompt
- call_codex
- process_functions
"""


def read_code_from_file(filename):
    """Read the code to be processed from a file"""
    with open(filename, 'r') as f:
        return f.read()


def get_functions(code):
    """Find all defined functions in the code"""
    return re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(.*?\)\s*:', code, re.DOTALL)


def get_function_code(function, code):
    """Get the code for a function"""
    return re.search(r'def\s+{}\s*\(.*?\)\s*:((?:.|\n)*?)\n\s*return'.format(function), code, re.DOTALL).group(1)


def get_function_definition(function, code):
    """Get the definition line for a function"""
    return re.search(r'def\s+{}\s*\((.*?)\)\s*:'.format(function), code).group(0)


def construct_prompt(definition, code, verbose=True):
    """Construct a prompt for a function"""
    prompt = definition + '\n' + code + '\n' + ('# With verbose inline comments\n' if verbose else '') + definition + '\n' + ('    #' if verbose else '') + '\n'

    return prompt


def call_codex(prompt):
    """Call the Codex API with the constructed prompt"""

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

    return response


def process_functions(code):
    """Process all functions in the code"""

    functions = get_functions(code)

    for function in functions:
        print('Processing {}'.format(function))
        function_code = get_function_code(function, code)
        function_definition = get_function_definition(function, code)

        prompt = construct_prompt(function_definition, function_code)
        print(prompt)

        response = call_codex(prompt)

        if response.status_code == 200:
            print('Successfully processed {}'.format(function))
            print('Response: {}'.format(response.json()))

            # Replace the original function with the commented one, move on to the next function, and repeat the same process.

            # TODO: This is a hacky way to do this. It would be better to replace the function definition line with the commented version.
            code = re.sub(r'def\s+{}\s*\(.*?\)\s*:'.format(function), '# def {}('.format(function), code) + response.json()['choices'][0]['text'] + '\n' + re.search(r'def\s+{}\s*\(.*?\)\s*:'.format(function), code).group(0) + '\n'
            print(code)

    return code


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        code = read_code_from_file(filename)
    else:
        code = sys.stdin.read()

    processed_code = process_functions(code)

    print('Processed code:\n{}'.format(processed_code))

    # If processing a file, write the processed code to a .new copy of the original file.
    if len(sys.argv) > 1:
        with open(filename + '.new', 'w') as f:
            f.write(processed_code)
