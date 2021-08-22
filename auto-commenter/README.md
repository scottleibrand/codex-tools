# Using OpenAI Codex to automatically add inline code comments

## Background

One difficulty humans often have working with code is interpreting what it’s trying to do, or specifically how it’s intended to work. OpenAI Codex can be prompted to add inline comments explaining what each section (or even line) of code is doing. Adding such comments improves the readability of the code, without requiring any additional work (or foresight) from the programmer. With auto-commenter, Such comments can quickly and easily be added to any existing code.

## How it works

[auto-commenter.py](auto-commenter.py) is a script written by OpenAI codex. I prompted it to autocomplete a script starting with the following docstring:

```
#!/usr/bin/env python
"""
Script to automatically add inline code comments

Read in the code to be processed from a provided filename or from stdin. Read in the user’s GTP_API_KEY from an
environment variable.

Split out the preamble code before the first /^def / function definition.
Split the code into chunks beginning with each /^def / function definition line.
For each non-preamble chunk, construct a Codex prompt consisting of the contents of autocomment-example.txt followed by
the code chunk and the line "# With verbose inline comments".

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
```

The generated python code works exactly as described. In most cases auto-commenter.py will produce a commented function identical to the generated one, but often Codex will decide the most likely completion is different from what was in the prompt in some way.

To avoid introducing such unwanted changes to the original function, I strung together some diff, grep, and patch commands to diff the generated function against the original, identify all the added comments, and patch them into the original code.

[auto-commenter.sh](auto-commenter.sh) first runs [auto-commenter.py](auto-commenter.py) to prompt OpenAI Codex add comments to $file. It then programmatically parses the resulting changes to keep only the added comments, to avoid introducing any other changes to the original function.


