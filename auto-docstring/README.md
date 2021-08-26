# Using OpenAI Codex to automatically add docstrings to functions

## Background

One difficulty humans often have working with code is interpreting what it’s trying to do, or specifically how it’s intended to work. OpenAI Codex can be prompted to add summaries explaining what a given function of code does, what arguments it requires, and what it returns. For Python, those can be formatted as PEP 257 docstrings. Adding such docstrings programatically improves the readability of the code, without requiring any additional work (or foresight) from the programmer. With auto-docstring, such comments can quickly and easily be added to any existing Python code.

## How it works

[auto-docstring.py](auto-docstring.py) is a script written with OpenAI codex. I prompted it to autocomplete a script starting with the following docstring:

```
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
```

Unlike auto-commenter.py (where output cleanup is done by auto-commenter.sh), I debugged and modified the auto-docstring code significantly to get it to directly provide the output I wanted.

## Example output

The first example of [auto-docstring.py](auto-docs.py)'s output is on the [oref0 repo](https://github.com/openaps/oref0/pull/1408/files).

## How to run it

You'll need to have an OpenAI Codex API key to be able to run auto-docstring yourself. You can learn more about Codex, and join the waitlist, [here](https://openai.com/blog/openai-codex/).

If you'd like to see what auto-docstring does with open source code you're working on, I'll be happy to process it myself while you're waiting to get access to the beta. Tag me on Twitter [https://twitter.com/scottleibrand](@scottleibrand) with a link to a specific file you'd like processed, and I'll clone the repo, run auto-comment on it, and send you back the processed file. If the output looks good and useful enough to PR, I can probably do entire directories or even repos as well.


# What's next?

First, I'd like to figure out whether this tool is something people would find valuable, get input on what you'd like to see from it, and find collaborators interested in working on this and similar tools.

If you have specific suggestions, feel free to reach out on Twitter as described above, or or [open an issue](https://github.com/scottleibrand/codex-tools/issues) on GitHub. Or you can fork and pull request this project on GitHub: [https://github.com/scottleibrand/codex-tools](https://github.com/scottleibrand/codex-tools).

Eventually, I'd like to [go live](https://beta.openai.com/docs/going-live) with some sort of demo (like a web page where people can submit links to code on GitHub they'd like processed). As noted at the link, this requires thinking through potential abuse and scaling issues. In particular, OpenAI doesn't allow [open-ended summarizer implementations](https://beta.openai.com/docs/use-case-guidelines/summarization) "that end-users can submit any content they wish to".

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
