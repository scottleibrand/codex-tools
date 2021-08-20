#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Find all defined functions that are not part of a docstring.
For each function:
 - Identify all the code up to and including the line defining that function
 - Construct a Codex prompt consisting of:
   - all that code
   - the comment '# With inline comments\n'
   - a repeat of the function definition line, and
   - an indented comment line without a trailing newline ('    #'):

 - Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function.

 - Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

    ```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 150,
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

import sys
import re
import json
import requests
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: {} <filename>".format(sys.argv[0]))
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename) as f:
        code = f.read()

    api_key = os.environ.get('GPT_API_KEY')
    if api_key is None:
        print("GPT_API_KEY environment variable not set")
        sys.exit(1)

    # Find all functions that are not part of a docstring
    functions = re.findall(r'^\s*def\s+(\w+)\s*\(.*\):', code, re.MULTILINE)
    for function in functions:
        print("Processing function {}".format(function))
        # Identify all the code up to and including the line defining that function. Include error checking.
        start_index = code.find("def {}(".format(function))
        if start_index == -1:
            print("Could not find function definition for {}".format(function))
            continue
        end_index = code.find("\ndef ", start_index)
        if end_index == -1:
            print("Could not find end of function definition for {}".format(function))
            continue

        # Construct a Codex prompt consisting of:
        # - all that code
        # - the comment '# With inline comments\n'
        # - a repeat of the function definition line, and
        # - an indented comment line without a trailing newline ('    #'):
        prompt = code[start_index:end_index] + "\n# With inline comments\n" + function + ":\n    #"
        print(prompt)

        # Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function.
        data = json.dumps({
            "prompt": prompt,
            "max_tokens": 150,
            "temperature": 0,
            "stop": "def "
        })
        print(data)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(api_key)
        }

        response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, data=data)

        # The response is json that looks like:
        # {"id": "cmpl-3XmVTLK9jvbny8CNcUmSqT8BNc6MC", "object": "text_completion", "created": 1629180295, "model": "davinci:2020-05-03", "choices": [{"text": " It is because of the scattering of the molecules in the air that make up the atmosphere. They scatter blue light more than any other color, making the sky appear blue.\n", "index": 0, "logprobs": null, "finish_reason": "stop"}]}

        result = json.loads(response.text)['choices'][0]['text']
        print(result)

        # Replace the original function with the commented one, move on to the next function, and repeat the same process.

        code = code[:start_index] + result + code[end_index:]
        print(code)

    print(code)

    with open(filename, 'w') as f:
        f.write(code)

    sys.exit(0)


if __name__ == '__main__':
    main()
