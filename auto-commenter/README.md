# Using OpenAI Codex to automatically add inline code comments

## Background

One difficulty humans often have working with code is interpreting what it’s trying to do, or specifically how it’s intended to work. OpenAI Codex can be very easily prompted to add inline comments explaining what each section (or even line) of code is doing. Adding such comments improves the readability of the code, without requiring any additional work (or foresight) from the programmer. Such comments could easily be added to any existing code.

## How it’d work

Read in the code to be processed from a provided filename or from stdin.
Read in the user’s GTP_API_KEY from an environment variable.

For each function, construct a Codex prompt consisting of all the code up to and including that function, followed by:

```
# With inline comments
def function_name(arguments):
    """
    Original docstring
    """
    #
```

Use Temperature 0, with a Stop sequence of def, to make Codex stop after it finishes generating the commented function.

Call the Codex API with the constructed prompt using the user’s GTP_API_KEY.

Diff the generated function against the original, identify all the added comments, and inject them into the original code. (In most cases this will produce a commented function identical to the generated one, but we want to programmatically avoid introducing any changes to the original function other than adding comments.)

Replace the original function with the commented one, move on to the next function, and repeat the same process. The code up to and including the next function will include the now-commented code from all previously processed functions, thereby providing additional context for what we want Codex to do.

Once our prompt has grown larger than about 10KB, switch to only including the last few functions (few-shot mode). Include the original versions, preceded with:
```
# Original function
```
Followed by the commented version, starting with
```
# With inline comments
```
As before, end the prompt with:
```
# With inline comments
def function_name(arguments):
    """
    Original docstring
    """
    #
```

Once all functions have been commented, write out the resulting file, either to a provided filename or to stdout.


## Appendix 1 - Example Codex input/output

Auto-commenting https://github.com/openaps/oref0/blob/dev/bin/get_profile.py
```
#!/usr/bin/env python
"""
Module to ease work with nightscout profiles.
By default lists all profiles found, and supports following sub-commands:
* profiles - list defined profiles
* display - display named (or default) profile
    (in nightscout or OpenAPS format)
* write - write to disk profile in OpenAPS format

Bunch of things inspired by https://github.com/MarkMpn/AutotuneWeb/
"""

# Make it work on both python 2 and 3
from __future__ import absolute_import, with_statement, print_function, unicode_literals

# Built-in modules
import argparse
from datetime import datetime
import json
import os.path
import logging
import sys

# External modules
import requests

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

PROFILE_FILES = ['autotune.json', 'profile.json', 'pumpprofile.json']
PROFILE_KEYS = [
    'autosens_max', 'autosens_min', 'basalprofile', 'bg_targets', 'carb_ratio',
    'carb_ratios', 'dia', 'isfProfile', 'min_5m_carbimpact', 'timezone'
]
TIMED_ENTRIES = ['carbratio', 'sens', 'basal', 'target_low', 'target_high']


def get_profiles(nightscout, token):
    """
    Get profiles available in nightscout
    """
    r_url = nightscout + "/api/v1/profile.json"
    if token is not None:
        r_url = r_url + "?" + token
    r = requests.get(r_url)
    return r.json()


def get_current_profile(nightscout, token, profile_name):
    """
    Try to get the active profile
    """
    
    r_url = nightscout + "/api/v1/profile.json"
    if token is not None:
        r_url = r_url + "?" + token
    p_list = requests.get(r_url).json()
    logging.debug("profile list: %s", p_list)
    default_profile = p_list[0]["defaultProfile"]
    if profile_name is None:
        p_url = (
            nightscout +
            "/api/v1/treatments.json?find[eventType][$eq]=Profile Switch&count=1"
        )
        if token is not None:
            p_url = p_url + "?" + token
        p_switch = requests.get(p_url).json()
        logging.debug("p_switch: %s", p_switch)
        if p_switch:
            try:
                sw_prof = json.loads(p_switch[0]["profileJson"])
                logging.debug("sw_prof: %s", sw_prof)
                if sw_prof:
                    profile = sw_prof
                    profile["name"] = p_switch[0]["profile"]
                    if profile["timezone"] is not None:
                        return profile
                    else:
                        profile["timezone"] = default_profile["timezone"]
                        return profile
            except KeyError:
                logging.debug("default profile: %s", default_profile)
                profile["timezone"] = p_list[0]["store"][default_profile]["timezone"]
                return profile
        p_list[0]["store"][default_profile]["name"] = default_profile
        try:
            if not p_list[0]["store"][default_profile]["units"]:
                p_list[0]["store"][default_profile]["units"] = p_list[0][
                    "units"]
        except KeyError:
            p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
        return p_list[0]["store"][default_profile]
    p_list[0]["store"][profile_name]["name"] = profile_name
    try:
        if not p_list[0]["store"][profile_name]["units"]:
            p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
    except KeyError:
        p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
    return p_list[0]["store"][profile_name]

# With inline comments
def get_current_profile(nightscout, token, profile_name):
    """
    Try to get the active profile
    """
    
    # Get profiles from Nightscout
    r_url = nightscout + "/api/v1/profile.json"
    # Add token if present
    if token is not None:
        r_url = r_url + "?" + token
    p_list = requests.get(r_url).json()
    logging.debug("profile list: %s", p_list)
    # Get default profile
    default_profile = p_list[0]["defaultProfile"]
    # If profile name is not specified, try to get the active profile
    if profile_name is None:
        # Get the last profile switch
        p_url = (
            nightscout +
            "/api/v1/treatments.json?find[eventType][$eq]=Profile Switch&count=1"
        )
        if token is not None:
            p_url = p_url + "?" + token
        p_switch = requests.get(p_url).json()
        logging.debug("p_switch: %s", p_switch)
        # If there is a profile switch
        if p_switch:
            # Try to get the profile from the switch
            try:
                sw_prof = json.loads(p_switch[0]["profileJson"])
                logging.debug("sw_prof: %s", sw_prof)
                if sw_prof:
                    profile = sw_prof
                    profile["name"] = p_switch[0]["profile"]
                    if profile["timezone"] is not None:
                        return profile
                    else:
                        profile["timezone"] = default_profile["timezone"]
                        return profile
            except KeyError:
                logging.debug("default profile: %s", default_profile)
                profile["timezone"] = p_list[0]["store"][default_profile]["timezone"]
                return profile
        # If there is no profile switch, return the default profile
        p_list[0]["store"][default_profile]["name"] = default_profile
        try:
            if not p_list[0]["store"][default_profile]["units"]:
                p_list[0]["store"][default_profile]["units"] = p_list[0][
                    "units"]
        except KeyError:
            p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
        return p_list[0]["store"][default_profile]
    # If profile name is specified, try to get the profile
    p_list[0]["store"][profile_name]["name"] = profile_name
    try:
        if not p_list[0]["store"][profile_name]["units"]:
            p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
    except KeyError:
        p_list[0]["store"][profile_name]["units"] = p_list[0]["units"]
    return p_list[0]["store"][profile_name]



def profiles(nightscout, token):
    """
    print list of profiles available in nightscout
    """
    p_list = get_profiles(nightscout, token)
    default_profile = p_list[0]["defaultProfile"]
    profile_list = p_list[0]["store"].keys()
    print("Default profile: {}".format(default_profile))
    print("Available profiles:")
    for profile in profile_list:
        print("\t" + profile)

# With inline comments
def profiles(nightscout, token):
    """
    print list of profiles available in nightscout
    """
    
    # Get profiles from Nightscout
    p_list = get_profiles(nightscout, token)
    # Get default profile
    default_profile = p_list[0]["defaultProfile"]
    # Print default profile
    print("Default profile: {}".format(default_profile))
    # Print available profiles
    profile_list = p_list[0]["store"].keys()
    print("Available profiles:")
    for profile in profile_list:
        print("\t" + profile)


def display(nightscout, token, profile_name, profile_format):
    """
    Display contents of a profile, in requested format
    """
    profile = get_current_profile(nightscout, token, profile_name)
    if profile_format == "nightscout":
        # display_nightscout(p_list, profile_name)
        logging.debug("Displaying profile {}".format(profile["name"]))
        print(json.dumps(profile, indent=4))
    elif profile_format == "text":
        display_text(profile)
    else:
        print(json.dumps(ns_to_oaps(profile), indent=4))

# With inline comments
def display(nightscout, token, profile_name, profile_format):
    """
    Display contents of a profile, in requested format
    """
    
    # Get profile from Nightscout
    profile = get_current_profile(nightscout, token, profile_name)
    # If requested format is nightscout
    if profile_format == "nightscout":
        # Display profile in nightscout format
        logging.debug("Displaying profile {}".format(profile["name"]))
        print(json.dumps(profile, indent=4))
    # If requested format is text
    elif profile_format == "text":
        # Display profile in text format
        display_text(profile)
    # If requested format is OpenAPS
    else:
        # Display profile in OpenAPS format
        print(json.dumps(ns_to_oaps(profile), indent=4))


def write(nightscout, token, profile_name, directory):
    """
    Write profile in OpenAPS format to a directory
    """
    profile = ns_to_oaps(get_current_profile(nightscout, token, profile_name))
    logging.debug("Checking for directory: %s", directory)
    if not os.path.isdir(directory):
        sys.exit(
            "Please provide an existing directory to write profile files to")
    # Check whether there's already a profile file with settings we don't have
    for profile_file in PROFILE_FILES:
        try:
            with open(os.path.join(directory, profile_file), 'r') as p:
                old_profile = json.loads(p.read())
                for key in old_profile.keys():
                    logging.debug("Checking key %s from profile file %s", key,
                                  profile_file)
                    if key not in PROFILE_KEYS:
                        logging.error(
                            "Existing profile file %s contains key %s we wouldn't set!",
                            profile_file, key)
                        sys.exit(
                            "Existing profile contains a key we wouldn't set!")
        except IOError:
            pass
    for profile_file in PROFILE_FILES:
        with open(os.path.join(directory, profile_file), 'w') as f:
            f.write(json.dumps(profile, indent=4))

# With inline comments
def write(nightscout, token, profile_name, directory):
    """
    Write profile in OpenAPS format to a directory
    """
    # Get profile in OpenAPS format
    profile = ns_to_oaps(get_current_profile(nightscout, token, profile_name))
    # Check whether there's already a profile file with settings we don't have
    for profile_file in PROFILE_FILES:
        try:
            with open(os.path.join(directory, profile_file), 'r') as p:
                old_profile = json.loads(p.read())
                for key in old_profile.keys():
                    logging.debug("Checking key %s from profile file %s", key,
                                  profile_file)
                    if key not in PROFILE_KEYS:
                        logging.error(
                            "Existing profile file %s contains key %s we wouldn't set!",
                            profile_file, key)
                        sys.exit(
                            "Existing profile contains a key we wouldn't set!")
        except IOError:
            pass
    # Write profile to directory
    for profile_file in PROFILE_FILES:
        with open(os.path.join(directory, profile_file), 'w') as f:
            f.write(json.dumps(profile, indent=4))


def normalize_entry(entry):
    """
    Clean up an entry before further processing
    """
    try:
        if entry["timeAsSeconds"]:
            pass
    except KeyError:
        entry_time = datetime.strptime(entry["time"], "%H:%M")
        entry[
            "timeAsSeconds"] = 3600 * entry_time.hour + 60 * entry_time.minute
    try:
        if entry["time"]:
            pass
    except KeyError:
        entry_hour = int(entry['timeAsSeconds'] / 3600)
        entry_minute = int(entry['timeAsSeconds'] % 60)
        entry["time"] = str(entry_hour).rjust(
            2, '0') + ":" + str(entry_minute).rjust(2, '0')

    entry["start"] = entry["time"] + ":00"
    entry["minutes"] = int(entry["timeAsSeconds"]) / 60
    return entry

# With inline comments
def normalize_entry(entry):
    """
    Clean up an entry before further processing
    """
    # Try to get the time as seconds
    try:
        if entry["timeAsSeconds"]:
            pass
    except KeyError:
        # Get the time
        entry_time = datetime.strptime(entry["time"], "%H:%M")
        # Set the time as seconds
        entry["timeAsSeconds"] = 3600 * entry_time.hour + 60 * entry_time.minute
    # Try to get the time
    try:
        if entry["time"]:
            pass
    except KeyError:
        # Get the time as seconds
        entry_hour = int(entry['timeAsSeconds'] / 3600)
        entry_minute = int(entry['timeAsSeconds'] % 60)
        # Set the time
        entry["time"] = str(entry_hour).rjust(
            2, '0') + ":" + str(entry_minute).rjust(2, '0')

    # Set the start time
    entry["start"] = entry["time"] + ":00"
    # Set the minutes
    entry["minutes"] = int(entry["timeAsSeconds"]) / 60
    return entry



```
