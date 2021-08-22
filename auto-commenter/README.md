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

## Example output

[auto-commenter.py](auto-commenter.py) itself is both the source code and its own example output. (The commit where I added add auto-commenter's comments about its own code is [here](https://github.com/scottleibrand/codex-tools/commit/2846c297c32096a66110924f39a54857842df72b).)

Another example is [oref0/bin/get_profile.py](https://github.com/openaps/oref0/pull/1407/files).

## How to run it

You'll need to have an OpenAI Codex API key to be able to run auto-commenter yourself. You can learn more about Codex, and join the waitlist, [here](https://openai.com/blog/openai-codex/).

If you'd like to see what auto-commenter does with open source code you're working on, I'll be happy to process it myself while you're waiting to get access to the beta. Tag me on Twitter [https://twitter.com/scottleibrand](@scottleibrand) with a link to the file you'd like processed, and I'll clone the repo, run auto-comment on it, and send you back the processed file.


# What's next?

First, I'd like to figure out whether this tool is something people would find valuable, get input on what you'd like to see from it, and find collaborators interested in working on this and similar tools.

A few ideas for things we could do to improve auto-commenter:
 - Test it out with languages other than Python, and tweak the prompt and/or script to work well with them.
 - Make it easier to recursively process all the code in a directory.
 - Figure out if it could be integrated into something like a Vim or IDE plugin to allow developers to auto-comment the code they're working on in real time.
  - Figure out how to make it easy to run as a commit hook to automatically comment code as it's being committed.
  - Make it work with [GitHub's Gists](https://developer.github.com/v3/gists/#create-a-gist).

If you have specific suggestions, feel free to reach out on Twitter as described above, or or [open an issue](https://github.com/scottleibrand/codex-tools/issues) on GitHub. Or you can fork and pull request this project on GitHub: [https://github.com/scottleibrand/codex-tools](https://github.com/scottleibrand/codex-tools).

Eventually, I'd like to [go live](https://beta.openai.com/docs/going-live) with some sort of demo (like a web page where people can submit links to code on GitHub they'd like processed). As noted at the link, this requires thinking through potential abuse and scaling issues. In particular, OpenAI doesn't allow [open-ended summarizer implementations](https://beta.openai.com/docs/use-case-guidelines/summarization) "that end-users can submit any content they wish to".

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
