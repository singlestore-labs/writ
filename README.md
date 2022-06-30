# WRIT (WASI Reactor Interface Tester)

This is a CLI tool that, given a WIT specification, will correctly interpret and cast arguments for an arbitrarily specified function in a Wasm module, and run it.  In particular, this tool is be useful when writing and testing “reactor” style WASI modules, where there is no `main` routine to invoke.

When no WIT file is provided, the arguments will be interpreted as basic types the same way `wasmtime --invoke` works

To facilitate expression of complex types, this tool accepts JSON notation as input, and produces JSON notation as output.  For more information, please see the [examples](#examples) section below. 

# Usage
You may use this tool locally, or via a [Docker](#building-and-running-the-docker-image) container.

## Docker

### Prerequisites
Please make sure you have Docker installed.

### Installation
To use this program in a docker container, you'll need the [writ-docker](https://github.com/singlestore-labs/writ/blob/main/bin/writ-docker) script.  You can either clone this repository and run it from there, or just download this script by itself and run it in a location of your choosing.

### Running
The general form is as follows:
```sh
Usage: writ-docker [OPTIONS] WASMFILE FUNCNAME [ARGS...]
```

*Arguments:*
`WASMFILE`
Specifies the path to your Wasm module (the `.wasm` file).

`FUNCNAME`
Specifies the name of the function you wish to test.

`ARGS`
Specifies 0 or more arguments to pass into the Wasm function.  Complex arguments may be expressed in JSON format.  May not be used with the `-b` option.

*Options:*
`-b, --batch BATCHFILE`
* Specifies a path to a file containing one or more JSON-formatted inputs to use in place of in-line arguments (see [Batch File Format](batch-file-format), below).
    
`-d, --debug`
* Starts the Wasm program in GDB.  See [Debugging](debugging), below.

`-q, --quiet`
* Supresses output.  This can be useful if you have many rows of input and just want to see if the function crashes.

`-s, --source`
* Only valid with the `-d` option, this specifies a source code directory into which the debugger can map files.  May specified more than once.

`-v, --verbose`
* Enables some additional diagnostic output about `writ` itself.

`-w, --wit`
* Optionally specifies the path to the WIT (`.wit`) file.  If this is not provided, then only simple numeric types may be passed into the Wasm function.

### Debugging
The Docker image includes GDB, and provides options to run your Wasm program in a debugger.

To do this, specify the "--debug" flag on the command line:
```sh
writ-docker --debug ...
```

If you wish, you can also map in local source directories so that the debugger can correctly display source code.  More than one directory may be specified.  For example:
```sh
writ-docker --debug --source ~/myprog/src --source /usr/local/src/rust ...
```

*Note*: At this time, debugger support for Wasm is a bit thin. You will be able to step through your code and get nice back traces on failure, however you won't be able to inspect local variables yet. Hopefully that will be resolved in the future as debugger support increases for Wasm modules.

## Local

### Prerequisites
To use this program locally, you'll first need to ensure that the following prerequisite software is installed:

* [Wasmtime](https://wasmtime.dev/)

* [wasmtime-py](https://github.com/bytecodealliance/wasmtime-py)

* [wit-bindgen](https://github.com/bytecodealliance/wit-bindgen). You might need to install [cargo](https://doc.rust-lang.org/cargo/getting-started/installation.html) first.

* [WASI SDK](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-14)

### Installation
For now, just clone this repo.  In the future, we plan to add this program to *PyPI*.

### Running
The general form is as follows:
```sh
Usage: writ [OPTIONS] WASMFILE FUNCNAME [ARGS...]
```

*Arguments:*
`WASMFILE`
Specifies the path to your Wasm module (the `.wasm` file).

`FUNCNAME`
Specifies the name of the function you wish to test.

`ARGS`
Specifies 0 or more arguments to pass into the Wasm function.  Complex arguments may be expressed in JSON format.  May not be used with the `-b` option.

*Options:*
`-b, --batch BATCHFILE`
* Specifies a path to a file containing one or more JSON-formatted inputs to use in place of in-line arguments (see [Batch File Format](batch-file-format), below).

`-c, --cache CACHEDIR`
* Specifies a directory to use for the binding cache.  To help save time on repeated runs, `writ` can cache its generated bindings in a directory and re-use them again later.  You can specify the location of this directory with this option.
    
`-q, --quiet`
* Supresses output.  This can be useful if you have many rows of input and just want to see if the function crashes.

`-v, --verbose`
* Enables some additional diagnostic output about `writ` itself.

`-w, --wit`
* Optionally specifies the path to the WIT (`.wit`) file.  If this is not provided, then only simple numeric types may be passed into the Wasm function.

### Debugging
You can debug your Wasm module running locally in `writ`.  To do this, pass the path to your python interpreter as the first argument to your debugger.  For example:

*GDB*
```sh
gdb --args /usr/bin/python3 src/writ --wit examples/int/power.wit examples/int/power.wasm power-of 2 3
```

*LLDB*
```sh
lldb -- /usr/bin/python3 src/writ --wit examples/int/power.wit examples/int/power.wasm power-of 2 3
```

*Note*: At this time, debugger support for Wasm is a bit thin. You will be able to step through your code and get nice back traces on failure, however you won't be able to inspect local variables yet. Hopefully that will be resolved in the future as debugger support increases for Wasm modules.

# Batch File Format
A JSON-formatted file may be passed in lieu of in-line arguments.  This file must consist of either a list of lists or a list of single values.  For example, either of the following forms will work:

```json
[
  "John Lennon",
  "Paul McCartney",
  ...
]
```
*or*
```json
[
  [ "John Lennon", "Guitar", 1940 ],
  [ "Paul McCartney", "Bass", 1942 ],
  ...
]
```

Each entry in the outer-most list represents the arguments for a single call into the Wasm function currently under test.

When a batch file is in use, output will be formatted in a similar way, with each outer list entry corresponding to one record of input.

# Examples 
All of the examples below apply equally to both `writ` and `writ-docker`.

## Simple numeric arguments
This example passes simple numerics as arguments.  Due to the simplicity of the 
parameter types (all numeric), a WIT file is optional.
```sh
writ --wit examples/int/power.wit examples/int/power.wasm power-of 2 3
```
*or*
```sh
writ examples/int/power.wasm power-of 2 3
```
Output:
```console
8
```

## Simple numeric arguments with type coercion
Numerics will be coerced to the declared WIT type, where possible.
```sh
writ --wit examples/float/power.wit examples/float/power.wasm power-of 2.0 3.0
```
Output:
```console
8.0
```

## String arguments
As a convenience, string arguments may be passed literally and need not include the escaped quote character that JSON requires.
```sh
writ --wit examples/string/split.wit examples/string/split.wasm split-str "wasm_rocks_the_house" "_"
```
*or*
```sh
writ --wit examples/string/split.wit examples/string/split.wasm split-str '"wasm_rocks_the_house"' '"_"'
```
Output:
```console
[
  {
    "str": "wasm",
    "idx": 0
  },
  {
    "str": "rocks",
    "idx": 5
  },
  {
    "str": "the",
    "idx": 11
  },
  {
    "str": "house",
    "idx": 15
  }
]
```

## Complex arguments and binary data
Here, we represent the required WIT `record` type as a JSON object with name and value pairs.  In this example, `vec` is a blob (`list<u8>`), so we must represent it as a JSON list of single byte values.
```sh
writ --wit examples/hilbert/hilbert.wit examples/hilbert/hilbert.wasm hilbert-encode '{"vec": [19,2,20,56,6,2,25,19], "min-value": 1.0, "max-value": 3.0, "scale": 6.0}'
```
Output:
```console
[{"idx": "0"}]
```

## Testing multiple records
Here, we'll test splitting some strings.  We use the `--batch` option for this.
e
```sh
cat<<EOF > /tmp/writ-test.json
[ 
  ["first_string_to_test", "_"],
  ["second-string-to-test", "_"],
  ["third-string_to__test", "_"],
  ["fourth-string-to-test", ""]
]
EOF

writ --batch /tmp/writ-test.json --wit examples/string/split.wit examples/string/split.wasm split-str
```
Output:
```console
[
  [
    {
      "str": "first",
      "idx": 0
    },
    {
      "str": "string",
      "idx": 6
    },
    {
      "str": "to",
      "idx": 13
    },
    {
      "str": "test",
      "idx": 16
    }
  ],
  [
    {
      "str": "second-string-to-test",
      "idx": 0
    }
  ],
  [
    {
      "str": "third-string",
      "idx": 0
    },
    {
      "str": "to",
      "idx": 13
    },
    {
      "str": "",
      "idx": 16
    },
    {
      "str": "test",
      "idx": 17
    }
  ],
  [
    {
      "str": "fourth-string-to-test",
      "idx": 0
    }
  ]
]
```

# Building the Docker Image
For this, you will need [Docker](https://docs.docker.com/engine/install/) installed.

```bash
docker build -f docker/Dockerfile -t ghcr.io/singlestore-labs/writ .
```

