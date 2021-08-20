#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an environment variable.

Find all defined functions that are not part of a docstring.
For each function, construct a Codex prompt consisting of all the code up to and including that function, followed by:

```
# With inline comments
def function_name(arguments):
    #
```

Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function.

Call the Codex API with the constructed prompt using the user’s GTP_API_KEY. API calls look like:

```
    data = json.dumps({
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7,
        "stop": "Q:"
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

Diff the generated function against the original, identify all the added comments, and inject them into the original code. (In most cases this will produce a commented function identical to the generated one, but we want to programmatically avoid introducing any changes to the original function other than adding comments.)

Replace the original function with the commented one, move on to the next function, and repeat the same process. The code up to and including the next function will include the now-commented code from all previously processed functions, thereby providing additional context for what we want Codex to do.
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
        code_before_function = re.search(r'^.*{}\('.format(function), code, re.MULTILINE).group(0)
        prompt = code_before_function + '\n    # With inline comments\n' + function + '('
        print(prompt)
        response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(api_key)
            },
            data=json.dumps({
                "prompt": prompt,
                "max_tokens": 150,
                "temperature": 0.7,
                "stop": "Q:"
            })
        )
        response_json = response.json()
        if response.status_code != 200:
            print("Error: {}".format(response_json))
            sys.exit(1)
        completion = response_json['choices'][0]['text']
        completion = completion.replace('\n', '\n    ')
        completion = completion.replace('Q:', '# Q:')
        completion = completion.replace('\n    # With inline comments\n', '\n')
        code = re.sub(r'^\s*def\s+{}\(.*\):'.format(function), completion, code, flags=re.MULTILINE)

    with open(filename + ".new", 'w') as f:
        f.write(code)

if __name__ == '__main__':
    main()
