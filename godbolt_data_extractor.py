import csv
import json
import os
import time

import requests

X86_COMPILER = "cg121"
ARM_COMPILER = "carm64g1210"
X86_URL = "https://godbolt.org/api/compiler/" + X86_COMPILER + "/compile"
ARM_URL = "https://godbolt.org/api/compiler/" + ARM_COMPILER + "/compile"

REQUEST_HEADERS = {"content-type": "application/json; charset=utf-8",
                   "accept": "application/json, text/javascript, */*; q=0.01"}

# Header also requires "source" and "compiler" fields in json
COMPILER_HEADER = {
    "source": None,
    "compiler": None,
    "options": {
        "userArguments": "",
        "compilerOptions": {
            "producePp": None,
            "produceGccDump": {},
            "produceOptInfo": False,
            "produceCfg": False,
            "produceLLVMOptPipeline": None,
            "produceDevice": False
        },
        "filters": {
            "binary": True,
            "execute": False,
            "intel": True,
            "demangle": True,
            "labels": True,
            "libraryCode": True,
            "directives": True,
            "commentOnly": True,
            "trim": False
        },
        "tools": [],
        "libraries": []
    },
    "lang": "c",
    "files": [],
    "bypassCache": False,
    "allowStoreCodeDebug": True
}


def get_json(arch: str, code_string: str = None) -> dict:
    """Sends Request to godbolt according to the architecture passed.

        Parameters
        ----------
        arch : str, mandatory, x86/arm
            The architecture for compilation

        code_string : str, mandatory
            The code file that we want to compile

        Raises
        ------
        TypeError
            If the arch parameter is not passed
        """

    url = ""

    # We need a deep copy of the dictonory which is done using dict.copy() method
    header_with_source = COMPILER_HEADER.copy()
    header_with_source["source"] = code_string

    if arch == "x86":
        header_with_source["compiler"] = X86_COMPILER
        url = X86_URL

    elif arch == "arm":
        header_with_source["compiler"] = ARM_COMPILER
        url = ARM_URL

    else:
        raise TypeError("Incorrect Architecture Input")

    resp = requests.post(url=url, data=json.dumps(
        header_with_source), headers=REQUEST_HEADERS)

    return resp.json()


def extract_opcode_line(compiled_output_json: dict) -> dict:
    curr_line = 0
    running_string = ""
    opcode_line_dict = dict()

    for asm in compiled_output_json["asm"]:

        if asm["source"] == None:
            continue

        if asm["source"]["mainsource"] == 'true':

            if asm["source"]["line"] != curr_line:
                curr_line = asm["source"]["line"]

            if curr_line not in opcode_line_dict:
                opcode_line_dict[curr_line] = ''.join(asm['opcodes'])

            else:
                opcode_line_dict[asm["source"]["line"]] = opcode_line_dict[asm["source"]
                                                                           ["line"]] + ' ' + ''.join(asm['opcodes'])

    return opcode_line_dict


def match_arch_output_lines(output_json_1: dict, output_json_2: dict, code_str_lines: list = None) -> dict:

    matched_dict = dict()

    output_list_1 = output_json_1.keys()
    output_list_2 = output_json_2.keys()

    # if output_list_1 != output_list_2:
    #     print(output_list_1)
    #     print(output_list_2)
    #     raise IndexError("Lists do not match")

    try:
        for i in output_list_1:
            matched_dict[i] = [output_json_1[i], output_json_2[i]]

        if code_str_lines != None:
            for i in matched_dict.keys():
                matched_dict[i].append(code_str_lines[i-1])

    except KeyError:
        pass
    return matched_dict


# parse_pairs(get_json("x86"))
code_dir = os.listdir("code_dir")

for code_file in code_dir:
    if code_file[-1] != "c":
        code_dir.remove(code_file)


with open('x86-arm.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    csv_header = ['x86', 'arm', 'code']
    writer.writerow(csv_header)

    for code in range(len(code_dir)):
        print(code_dir[code])
        with open("code_dir/" + code_dir[code], "r") as code_str:
            code_str_op = code_str.read()
            code_str.seek(0)
            code_str_lines = code_str.readlines()
            matched_output = match_arch_output_lines(extract_opcode_line(get_json(
                arch="x86", code_string=code_str_op)), extract_opcode_line(get_json(arch="arm", code_string=code_str_op)), code_str_lines)

            for i in matched_output.keys():
                writer.writerow(matched_output[i])
